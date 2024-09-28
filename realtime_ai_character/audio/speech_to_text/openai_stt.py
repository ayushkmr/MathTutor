import io
import os
import types

from openai import OpenAI
from pydub import AudioSegment

from realtime_ai_character.audio.speech_to_text.base import SpeechToText
from realtime_ai_character.logger import get_logger
from realtime_ai_character.utils import Singleton, timed

logger = get_logger(__name__)

config = types.SimpleNamespace(
    **{
        "language": "en",
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
)

class OpenAI_STT(Singleton, SpeechToText):
    def __init__(self):
        super().__init__()
        logger.info("Initializing [OpenAI Speech To Text] client...")
        self.client = OpenAI(api_key=config.api_key)
        self.language = config.language

    @timed
    def transcribe(
        self, audio_bytes, platform="web", prompt="", language="en-US", suppress_tokens=[-1]
    ) -> str:
        logger.info("Transcribing audio using OpenAI Whisper API...")
        if platform == "web":
            audio = self._convert_webm_to_wav(audio_bytes)
        elif platform == "twilio":
            audio = self._ulaw_to_wav(audio_bytes)
        else:
            audio = self._convert_bytes_to_wav(audio_bytes)

        transcription = self._transcribe_api(audio, prompt)
        filtered_transcription = self._moderate_content(transcription)
        return filtered_transcription

    def _transcribe_api(self, audio, prompt=""):
        audio_file = io.BytesIO(audio.getbuffer())
        # Use OpenAI's Whisper API for transcription
        response = self.client.audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language=self.language,
            prompt=prompt,
        )
        text = response.get("text", "")
        return text

    def _moderate_content(self, text):
        # Use OpenAI's Moderation API to detect offensive content
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        moderation_result = response["results"][0]

        # Check if any category is flagged
        flagged = moderation_result["flagged"]

        if flagged:
            logger.warning("Offensive content detected in transcription.")
            # Replace the offensive content with '***' or handle accordingly
            # For this example, we'll replace the entire text
            filtered_text = "***"
        else:
            filtered_text = text

        return filtered_text

    def _convert_webm_to_wav(self, webm_data):
        webm_audio = AudioSegment.from_file(io.BytesIO(webm_data))
        wav_data = io.BytesIO()
        webm_audio.export(wav_data, format="wav")
        wav_data.seek(0)
        return wav_data

    def _convert_bytes_to_wav(self, audio_bytes):
        wav_data = io.BytesIO(audio_bytes)
        return wav_data

    def _ulaw_to_wav(self, audio_bytes):
        sound = AudioSegment(
            data=audio_bytes,
            sample_width=1,
            frame_rate=8000,
            channels=1,
        )
        audio = io.BytesIO()
        sound.export(audio, format="wav")
        audio.seek(0)
        return audio
