# Market Data Service

A standalone FastAPI service providing mock market data.

## Features

- `GET /snapshot/{symbol}`: Returns the last price and reference data for a given symbol.
- `WS /ws/stream`: WebSocket endpoint streaming mock market data ticks with sequence numbers.
- `GET /health`: Health check endpoint.
- `GET /metrics`: Prometheus metrics endpoint.

## Running Locally

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Access the API documentation at `http://localhost:8000/docs`.

## Running with Docker

1. Build the image:
   ```bash
   docker build -t market-data-service .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 market-data-service
   ```
