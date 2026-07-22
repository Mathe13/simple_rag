import os
import sys
import json
import argparse
import pandas as pd
from datasets import Dataset

# --- HOST ENVIRONMENT OVERRIDES ---
# These must be set before importing the backend to override docker defaults
os.environ["DATABASE_URL"] = "postgresql+asyncpg://admin:admin@localhost:5437/hp_rag_db"
os.environ["VECTOR_DB_URL"] = "postgresql+psycopg2://admin:admin@localhost:5437/hp_rag_db"
os.environ["OPENAI_BASE_URL"] = "http://localhost:9000/v1"
os.environ["OPENAI_API_KEY"] = "sk-local-dev-key"
os.environ["EMBEDDING_MODEL"] = "BAAI/bge-small-en-v1.5"
os.environ["CHAT_MODEL"] = "meta-llama/Llama-3.2-1B-Instruct"

from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall
)

# Add the project root to the system path to import the backend modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.app.services.rag_chain import get_rag_chain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Define the path to your custom dataset
DATASET_PATH = os.path.join(os.path.dirname(__file__), "qa_dataset.json")

def load_custom_dataset(filepath):
    """
    Loads the custom JSON dataset. 
    Expects a list of dictionaries with 'question', 'ground_truth', and 'suggested_context'.
    """
    if not os.path.exists(filepath):
        print(f"Error: Dataset not found at {filepath}")
        sys.exit(1)
        
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)
        
    return data

def run_benchmark(limit=None):
    """
    Executes the RAG benchmarking process using a custom JSON dataset.
    """
    print(f"Loading custom dataset from {DATASET_PATH}...")
    evaluation_data = load_custom_dataset(DATASET_PATH)
    
    if limit is not None:
        evaluation_data = evaluation_data[:limit]
        print(f"Limiting evaluation to {limit} questions.")
    
    print("Initializing RAG chain for benchmarking...")
    rag_chain = get_rag_chain()

    # Ragas requires specific keys. We will also track the suggested_context 
    # to output it in the final CSV for your own analysis.
    data_samples = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": [],
        "suggested_context": [] # Kept for the final CSV report
    }

    print(f"Running {len(evaluation_data)} queries from your dataset...")

    # Process each question through the RAG pipeline
    for item in evaluation_data:
        question = item.get("question")
        ground_truth = item.get("ground_truth")
        suggested_context = item.get("suggested_context", "")
        
        if not question or not ground_truth:
            print(f"Skipping malformed entry: {item}")
            continue
            
        # Invoke the chain with an empty chat history for baseline benchmarking
        try:
            response = rag_chain.invoke({
                "input": question,
                "chat_history": []
            })
            
            # Extract the generated answer and the text chunks retrieved from PGVector
            generated_answer = response["answer"]
            retrieved_contexts = [doc.page_content for doc in response["context"]]
            
        except Exception as e:
            print(f"Error processing question '{question}': {e}")
            continue
        
        data_samples["question"].append(question)
        data_samples["answer"].append(generated_answer)
        data_samples["contexts"].append(retrieved_contexts)
        
        # Ragas expects ground_truth as a string or list of strings depending on version.
        # String is the safest standard for text-based QA evaluation.
        data_samples["ground_truth"].append(ground_truth)
        
        # Keep track of your custom context for your own reporting
        data_samples["suggested_context"].append(suggested_context)

    # Convert the raw data into a HuggingFace Dataset, dropping 'suggested_context' 
    # for the Ragas evaluation step (Ragas throws errors on unrecognized columns)
    ragas_dict = {
        "question": data_samples["question"],
        "answer": data_samples["answer"],
        "contexts": data_samples["contexts"],
        "ground_truth": data_samples["ground_truth"]
    }
    dataset = Dataset.from_dict(ragas_dict)

    print("Evaluating metrics via Ragas... (This uses the local API and may take a few minutes)")

    eval_llm = ChatOpenAI(
        model=os.environ["CHAT_MODEL"],
        temperature=0,
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"]
    )
    
    eval_embeddings = OpenAIEmbeddings(
        model=os.environ["EMBEDDING_MODEL"],
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"]
    )

    # Execute the Ragas evaluation
    result = evaluate(
        dataset,
        metrics=[
            Faithfulness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall()
        ],
        llm=eval_llm,
        embeddings=eval_embeddings,
    )

    # Convert the results to a Pandas DataFrame
    df_results = result.to_pandas()
    
    # Re-attach your 'suggested_context' to the final dataframe so you can compare 
    # 'contexts' (what PGVector actually found) vs 'suggested_context' (what you expected)
    df_results['suggested_context'] = data_samples['suggested_context']
    
    # Reorder columns for readability
    cols = ['question', 'ground_truth', 'answer', 'contexts', 'suggested_context', 
            'faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
    df_results = df_results[cols]
    
    # Save the benchmark report
    output_file = os.path.join(os.path.dirname(__file__), "rag_benchmark_report.csv")
    df_results.to_csv(output_file, index=False)
    
    print("\n=== Benchmark Completed ===")
    print(df_results[['question', 'faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']].head())
    print(f"\nDetailed report saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG benchmark using Ragas.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of questions to evaluate")
    args = parser.parse_args()
    
    run_benchmark(limit=args.limit)