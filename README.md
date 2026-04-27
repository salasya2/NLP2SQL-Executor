# CHESS SQL Framework

CHESS (Contextual Harnessing for Efficient SQL Synthesis) is an end-to-end Natural Language to SQL pipeline. It allows users to interact with their SQLite databases using plain English text or voice commands, translating them into accurate SQL queries and returning the results instantly.

## Features

- **Agentic Architecture**: Utilizes a three-stage pipeline (Information Retrieval $\rightarrow$ Schema Selection $\rightarrow$ Candidate Generation) powered by `Llama-3.3-70b` (via Groq) to intelligently prune irrelevant schema context and generate highly accurate SQL.
- **Voice-to-SQL**: Real-time voice query capabilities using WebSockets and Groq's `Whisper-large-v3` for fast, accurate speech recognition.
- **Semantic Caching**: Implements Redis-backed semantic caching with `sentence-transformers/all-MiniLM-L6-v2` embeddings, resolving repeated or similar queries in under 50ms without invoking the LLM pipeline.
- **Full-Stack Application**: 
  - **Backend**: High-performance FastAPI server.
  - **Frontend**: Modern React + Vite application served via Nginx.
- **Production-Ready Deployment**: Fully containerized using Docker with Kubernetes manifests for scalable orchestration and secure namespace-scoped secrets management.

## Project Structure

- `/backend` - FastAPI server handling the core API endpoints (`/api/query`, `/api/ws-voice`, etc.).
- `/frontend` - React based User Interface.
- `/src` - Core LLM agent logic (`IR.py`, `SS.py`, `CG.py`), indexing utilities, and speech processing.
- `/templates` - Prompt templates for the LLM agents.
- `/data` - Active databases and schema descriptions.
- `/index` - Generated database indices (`index.json`) for schema pruning.

## How to Run

You can run the CHESS SQL framework entirely locally using Python/Node, or containerize it using Docker and Kubernetes.

### Prerequisites
- Groq API Key
- Redis server (local or hosted)

### Environment Setup
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
REDIS_HOST=localhost
REDIS_PASSWORD=your_redis_password
```

### Option 1: Running Locally (Development)

This is the fastest way to test changes.

**1. Start Redis**
Ensure you have a Redis instance running on port `17436` (or update `backend/sqlapp.py` to match your Redis config).
```bash
redis-server --port 17436 --requirepass "your_redis_password"
```

**2. Start the Backend (FastAPI)**
```bash
pip install -r requirements.txt
uvicorn backend.sqlapp:app --host 0.0.0.0 --port 5000
```
*The API will be available at http://localhost:5000*

**3. Start the Frontend (React)**
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
*The UI will be available at http://localhost:5173*

### Option 2: Running via Docker

You can build and run the individual Docker containers.

**1. Build the Images**
```bash
# Build backend
docker build -t chess-backend:latest .

# Build frontend
cd frontend
docker build -t chess-frontend:latest .
```

**2. Run the Containers**
```bash
# Run backend (Make sure your REDIS_HOST in .env points to a reachable Redis IP)
docker run -d -p 5000:5000 --env-file .env chess-backend:latest

# Run frontend
docker run -d -p 80:80 chess-frontend:latest
```

### Option 3: Deployment (Kubernetes)

For production-like orchestration using Minikube or Docker Desktop.

**1. Load images into your cluster** (e.g., for Minikube)
```bash
minikube image load chess-backend:latest
minikube image load chess-frontend:latest
```

**2. Deploy Secrets and Services**
```bash
kubectl create secret generic chess-secrets --from-env-file=.env
kubectl apply -f k8s-backend.yaml
kubectl apply -f k8s-frontend.yaml
```

**3. Access the Application**
```bash
kubectl port-forward svc/frontend-service 8080:80
# Access via http://localhost:8080
```

---

## How it Works (Briefly)

1. **Upload Database**: Upload a `.sqlite` database and descriptive `.csv` files via the UI to build an `index.json`.
2. **Ask a Question**: Type a natural language query or use the voice recorder.
3. **Pipeline Execution**: The system checks the Redis semantic cache. On a miss, it routes through the IR (Keywords), SS (Schema Pruning), and CG (SQL Generation) agents via Llama-3.3-70b.
4. **View Results**: The generated SQL executes against the SQLite database, returning the query and data table.
