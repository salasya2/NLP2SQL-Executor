import os
from groq import AsyncGroq
from dotenv import load_dotenv
import uuid

load_dotenv()


client = AsyncGroq()

async def transcribe(audio_data: bytes) -> str:
    temp_file_name = f"{uuid.uuid4()}.webm"
    with open(temp_file_name, "wb") as f:
        f.write(audio_data)
    with open(temp_file_name, "rb") as file:
        transcription = await client.audio.transcriptions.create(
            file=(temp_file_name, file.read()),
            model="whisper-large-v3",
        )
    
    os.remove(temp_file_name)
    return transcription.text
