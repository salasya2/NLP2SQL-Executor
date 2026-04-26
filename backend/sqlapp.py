import re
import traceback
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from typing import List, Optional
import shutil
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.index import Indexer
from src.CG import CGAgent
from langchain_core.outputs import Generation
from langchain_redis.cache import RedisSemanticCache
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os
from fastapi import WebSocket, WebSocketDisconnect
import redis
import asyncio
from src.speech import transcribe

load_dotenv()


embed_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./model"
)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=17436,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)

redis_cache = RedisSemanticCache(
    redis_client=redis_client,
    embeddings=embed_model,
    distance_threshold=0.10,
)

app = FastAPI(title="CHESS SQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BuildIndexRequest(BaseModel):
    db_path: str
    description_path: str
    output_dir: str

class QueryRequest(BaseModel):
    question: str


def parse_sql(raw: str) -> tuple[str, str]:
    match = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        answer = raw[:match.start()].strip() or raw[match.end():].strip()
    else:
        sql = ""
        answer = raw.strip()
    return answer, sql


def execute_sql(sql: str, db_path: str = "data/active/database.sqlite") -> dict:
    if not sql:
        return {"columns": [], "rows": []}
    try:
        db_uri = f"{Path(db_path).absolute().as_uri()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        return {"columns": columns, "rows": [list(r) for r in rows]}
    except Exception as e:
        return {"columns": [], "rows": [], "error": str(e)}


@app.websocket("/api/ws-voice")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    audio_data = bytearray()
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            if "bytes" in message:
                audio_chunk = message["bytes"]
                audio_data.extend(audio_chunk)

                await websocket.send_text("Listening to your voice...")
            elif "text" in message and message["text"] == "DONE":
                
                
                try:
                    text = await transcribe(audio_data)
                    await websocket.send_text(f"You said: {text}")
                    query_result = await asyncio.to_thread(query_sql, QueryRequest(question=text))
                    await websocket.send_json(query_result)
                    break
                except Exception as e:
                    await websocket.send_text(f"Error: {str(e)}")
                    break
                
    except WebSocketDisconnect:
        print("Client disconnected")

    
    

@app.post("/api/build-index")
async def build_index(
    db_file: UploadFile = File(...),
    csv_files: Optional[List[UploadFile]] = File(None)
):
    try:
        active_dir = Path("data/active")
        desc_dir = active_dir / "descriptions"
        
        if active_dir.exists():
            shutil.rmtree(active_dir)
            
        desc_dir.mkdir(parents=True, exist_ok=True)
        
        # Save db
        db_path = active_dir / "database.sqlite"
        with open(db_path, "wb") as buffer:
            shutil.copyfileobj(db_file.file, buffer)
            
        # Save csvs
        if csv_files:
            for csv_file in csv_files:
                if csv_file.filename:
                    csv_path = desc_dir / csv_file.filename
                    with open(csv_path, "wb") as buffer:
                        shutil.copyfileobj(csv_file.file, buffer)
                        
        # Run indexer
        indexer = Indexer(db_path=str(db_path), description_path=str(desc_dir), directory="index")
        indexer.create_index()
        
        return {"status": "ok", "message": "Index created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schema")
def get_schema():
    import json
    from pathlib import Path
    path = Path("index/index.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="index.json not found. Run /api/build-index first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/query")
def query_sql(body: QueryRequest):
    try:
        llm_string = "final_sql_pipeline"
        cached_result = redis_cache.lookup(body.question, llm_string)
        
        if cached_result:
            print("CACHE HIT! Returning cached SQL...")
            raw = cached_result[0].text
        else:
            print("CACHE MISS! Running pipeline...")
            agent = CGAgent(body.question)
            raw = agent.generate_sql()
            # Save the final text output to cache
            redis_cache.update(body.question, llm_string, [Generation(text=raw)])

        answer, sql = parse_sql(raw)
        result = execute_sql(sql)
        
        return {
            "question": body.question,
            "answer": answer,
            "sql": sql,
            "columns": result["columns"],
            "rows": result["rows"],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
