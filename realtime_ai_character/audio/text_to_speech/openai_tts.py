import asyncio
import os
from typing import Optional

import httpx
from fastapi import WebSocket

from realtime_ai_character.audio.text_to_speech.base import TextToSpeech
from realtime_ai_character.logger import get_logger
from realtime_ai_character.utils import Singleton, timed

logger = get_logger(__name__)

class OpenAITTS(Singleton, TextToSpeech):
    def __init__(self):
        super().__init__()
        logger.info("Initializing [OpenAI Text To Speech] client...")
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI API key is not set!")
        self.client = httpx.AsyncClient(timeout=None)
        self.default_voice_id = "shimmer"
        self.default_language = "en"
        self.model = "tts-1"

    @timed
    async def stream(
        self,
        text: str,
        websocket: WebSocket,
        tts_event: asyncio.Event,
        voice_id: str = "",
        first_sentence: bool = False,
        language: str = "",
        platform: str = "",
        sid: str = "",
        *args,
        **kwargs
    ):
        voice_id = voice_id or self.default_voice_id
        language = language or self.default_language

        logger.info(f"Streaming TTS for text: '{text[:30]}...' with voice ID: '{voice_id}'")

        if tts_event.is_set():
            logger.info("TTS event triggered.")

        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "voice": voice_id,
                "input": text,  # Changed 'text' back to 'input'
            }

            # Send TTS request to OpenAI
            logger.info("Sending TTS request to OpenAI...")

            response = await self.client.post(
                "https://api.openai.com/v1/audio/speech",  # Correct endpoint
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload  # Send data as JSON
            )

            # Log response status and headers
            logger.debug(f"Received response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            response.raise_for_status()

            # Handle the response (assuming the API returns the audio data directly)
            audio_data = response.content

            if platform != "twilio":
                # Send binary audio data directly
                await websocket.send_bytes(audio_data)
            else:
                # Handle Twilio-specific requirements
                import base64
                audio_b64 = base64.b64encode(audio_data).decode()
                media_response = {
                    "event": "media",
                    "streamSid": sid,
                    "media": {
                        "payload": audio_b64,
                    },
                }
                await websocket.send_json(media_response)
                # Send done marker
                mark = {
                    "event": "mark",
                    "streamSid": sid,
                    "mark": {
                        "name": "done",
                    },
                }
                await websocket.send_json(mark)

            logger.info("Audio data sent successfully.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI TTS: {e}")
            raise

    async def generate_audio(
        self,
        text: str,
        voice_id: str = "",
        language: str = ""
    ) -> Optional[bytes]:
        voice_id = voice_id or self.default_voice_id
        language = language or self.default_language

        logger.info(f"Generating audio for text: '{text[:30]}...' with voice ID: '{voice_id}'")

        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "voice": voice_id,
                "input": text,  # Changed 'text' back to 'input'
            }

            # Send request to OpenAI for audio generation
            logger.info("Sending request to OpenAI for audio generation...")

            response = await self.client.post(
                "https://api.openai.com/v1/audio/speech",  # Correct endpoint
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload  # Send data as JSON
            )

            # Log response status and headers
            logger.debug(f"Received response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            response.raise_for_status()

            audio_data = response.content

            logger.info("Audio generated successfully.")
            return audio_data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI TTS generate_audio: {e}")
            return None
