# Enterprise Mocks

`enterprise-mocks` is a lightweight mock service designed to simulate external enterprise APIs for local development and testing. It provides mocked endpoints for two main services:

- **SSO Authentication Mock (`/sso/token`)**: Simulates a Single Sign-On service. It accepts dummy credentials and returns a valid, signed JWT access token for testing authentication flows.
- **Vault Secrets Mock (`/vault/secrets/{secret_path}`)**: Simulates a secrets management vault (like HashiCorp Vault). It reads mock secrets from a local `secrets.json` file, allowing you to securely test credential fetching without exposing real keys.

## Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker (optional, for containerized execution)

### Running Locally

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Start the FastAPI service:
   ```bash
   uv run uvicorn app:app --host 0.0.0.0 --port 8001
   ```

### Running via Docker

1. Build the image:
   ```bash
   docker build -t mocks:latest .
   ```
2. Run the container:
   ```bash
   docker run -p 8001:8001 mocks:latest
   ```

### Running Tests

To run the unit tests and check coverage:
```bash
uv run pytest --cov=app --cov-report=term-missing test_app.py
```
