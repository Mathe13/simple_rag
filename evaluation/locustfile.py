import uuid
import random
import requests
from locust import HttpUser, task, between

import json
import os

# A pool of realistic questions based on the HP manuals to ensure
# the vector database and LLM process different contexts.
# Load queries from qa_dataset.json
dataset_path = os.path.join(os.path.dirname(__file__), 'qa_dataset.json')
with open(dataset_path, 'r', encoding='utf-8') as f:
    qa_data = json.load(f)
    SAMPLE_QUERIES = [item['question'] for item in qa_data]

class ChatbotLoadTestUser(HttpUser):
    # Simulate the time a user takes to read a response and type the next question
    # (Waits between 2 and 5 seconds between tasks)
    wait_time = between(2, 5)

    def on_start(self):
        """
        Executed when a simulated user starts.
        Initializes unique user credentials and an empty conversation state.
        """
        self.user_id = str(uuid.uuid4())
        self.conversation_id = None
        self.email = f"user_{self.user_id[:8]}@example.com"
        
        # Authenticate with the mock SSO to get a valid token
        response = requests.post("http://localhost:8001/sso/token", json={
            "username": self.email,
            "password": "password"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None
            print(f"Failed to authenticate: {response.status_code} {response.text}")


    @task
    def ask_technical_question(self):
        """
        The main task that hits the FastAPI backend.
        It manages the conversation state dynamically.
        """
        query = random.choice(SAMPLE_QUERIES)
        
        payload = {
            "user_id": self.user_id,
            "query": query
        }
        
        # If the user already has an active conversation, append the ID to the payload
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id

        headers = {"x-mock-request": "true"}
        #headers = {}
        if hasattr(self, 'token') and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        # Use the 'name' parameter to group the endpoint metrics in the Locust UI
        with self.client.post("/api/chat", json=payload, headers=headers, name="/api/chat", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Store the conversation ID for the next requests from this simulated user
                    if not self.conversation_id and "conversation_id" in data:
                        self.conversation_id = data["conversation_id"]
                    response.success()
                except Exception as e:
                    response.failure(f"Failed to parse JSON response: {str(e)}")
            else:
                response.failure(f"Status code {response.status_code} returned.")