from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import tempfile
from typing import Optional
import soundfile as sf

# Import your TTS dependencies
from kokoro import KPipeline

# Initialize the TTS pipeline
pipeline = KPipeline(lang_code='a')  # Make sure lang_code matches voice

# Initialize FastAPI app
app = FastAPI(title="Kokoro TTS API Service")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create temp directory to store audio files
TEMP_DIR = tempfile.gettempdir()
os.makedirs(TEMP_DIR, exist_ok=True)

def tts(text, file_name, voice='af_bella', speed=0.9):
    """
    Generate speech from text using Kokoro TTS
    
    Args:
        text (str): Text to convert to speech
        file_name (str): Path to save the output .wav file
        voice (str): Voice to use for TTS
        speed (float): Speed of speech
        
    Returns:
        str: Path to the generated audio file
    """
    try:
        generator = pipeline(
            text, voice=voice,
            speed=speed, split_pattern=None
        )

        for i, (gs, ps, audio) in enumerate(generator):
            sf.write(file_name, audio, 24000)  # save audio file
        
        return file_name
    except Exception as e:
        raise Exception(f"TTS generation failed: {str(e)}")

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_bella"
    speed: float = 0.9

@app.post("/tts/")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech and return a .wav file
    """
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(TEMP_DIR, filename)
        
        # Generate speech using your TTS function
        tts(request.text, output_path, request.voice, request.speed)
        
        # Return the audio file
        return FileResponse(
            path=output_path, 
            filename=filename,
            media_type="audio/wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.get("/tts-get/")
async def text_to_speech_get(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query("af_bella", description="Voice to use for TTS"),
    speed: float = Query(0.9, description="Speed of speech (0.5-1.5)")
):
    """
    GET endpoint for text-to-speech conversion
    """
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(TEMP_DIR, filename)
        
        # Generate speech using your TTS function
        tts(text, output_path, voice, speed)
        
        # Return the audio file
        return FileResponse(
            path=output_path, 
            filename=filename,
            media_type="audio/wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.get("/voices/")
async def available_voices():
    """
    Return a list of available voices
    """
    # This is a placeholder - you should replace with actual available voices
    # from your kokoro library
    return {
        "voices": ["af_bella"],  # Add other available voices here
        "default": "af_bella"
    }

@app.get("/")
async def root():
    """
    Serve the frontend HTML
    """
    return FileResponse('static/index.html')