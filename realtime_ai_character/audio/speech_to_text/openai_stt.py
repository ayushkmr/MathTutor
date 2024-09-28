import io
import os
import types

import requests
import pydub  # Import the pydub module
from openai import OpenAI
from pydub import AudioSegment, effects
from pydub.silence import split_on_silence

from realtime_ai_character.audio.speech_to_text.base import SpeechToText
from realtime_ai_character.logger import get_logger
from realtime_ai_character.utils import Singleton, timed

logger = get_logger(__name__)

config = types.SimpleNamespace(
    **{
        "language": "en",  # Set default language to English
        "api_key": os.getenv("OPENAI_API_KEY"),
        "min_volume_threshold": -40.0,  # Minimum volume threshold in dBFS
    }
)

class OpenAI_STT(Singleton, SpeechToText):
    def __init__(self):
        super().__init__()
        logger.info("Initializing [OpenAI Speech To Text] client...")
        self.client = OpenAI(api_key=config.api_key)
        self.language = config.language
        self.min_volume_threshold = config.min_volume_threshold

    @timed
    def transcribe(
        self, audio_bytes, platform="web", prompt="", language="en-US", suppress_tokens=[-1]
    ) -> str:
        logger.info("Transcribing audio using OpenAI Whisper API...")

        # Only proceed if the language is English
        if language != "en-US":
            logger.warning("Non-English language detected. Ignoring transcription.")
            return ""

        if platform == "web":
            audio = self._convert_webm_to_wav(audio_bytes)
        elif platform == "twilio":
            audio = self._ulaw_to_wav(audio_bytes)
        else:
            audio = self._convert_bytes_to_wav(audio_bytes)

        # Preprocess the audio to remove low-volume segments and reduce noise
        processed_audio = self._preprocess_audio(audio)

        if processed_audio:
            transcription = self._transcribe_api(processed_audio, prompt)
            if transcription:
                filtered_transcription = self._moderate_content(transcription)
                return filtered_transcription
            else:
                return ""
        else:
            logger.warning("No audio left after preprocessing. Ignoring transcription.")
            return ""

    def _preprocess_audio(self, audio_data):
        # Load the audio data into an AudioSegment
        audio_data.seek(0)
        audio = AudioSegment.from_file(audio_data)

        # Normalize the audio to a standard level
        audio = effects.normalize(audio)

        # Reduce background noise (simple method)
        audio = self._reduce_noise(audio)

        # Split the audio into chunks where the volume is above the threshold
        loud_chunks = self._split_on_silence(audio, self.min_volume_threshold)

        if not loud_chunks:
            return None

        # Concatenate the loud chunks back together
        processed_audio = AudioSegment.empty()
        for chunk in loud_chunks:
            processed_audio += chunk

        # Export the processed audio to a BytesIO object
        output_data = io.BytesIO()
        processed_audio.export(output_data, format="wav")
        output_data.name = "audio.wav"
        output_data.seek(0)
        return output_data

    def _reduce_noise(self, audio):
        # Simple noise reduction by applying a low-pass filter
        # Adjust the cutoff frequency as needed (e.g., 3000 Hz)
        reduced_noise_audio = audio.low_pass_filter(3000)
        return reduced_noise_audio

    def _split_on_silence(self, audio_segment, min_volume_threshold):
        # Define parameters for splitting
        min_silence_len = 500  # Minimum length of silence in ms to be considered a split
        silence_thresh = min_volume_threshold  # Silence threshold in dBFS

        # Use split_on_silence directly
        chunks = split_on_silence(
            audio_segment,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            keep_silence=200,  # Keep a bit of silence at the edges
        )

        return chunks

    def _transcribe_api(self, audio, prompt=""):
        # Set the name attribute with the correct file extension
        audio.name = "audio.wav"

        try:
            # Use OpenAI's Whisper API for transcription with optimized settings
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language=self.language,  # Force English language
                prompt=prompt,
                temperature=0,  # Set temperature to 0 for deterministic output
                # Consider adding 'response_format' if needed
            )
            text = response.text.strip()

            # Ignore if the transcription is empty
            if not text:
                logger.warning("Empty transcription received.")
                return ""

            return text

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during transcription: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            return ""

    def _moderate_content(self, text):
        # Use OpenAI's Moderation API to detect offensive content
        response = self.client.moderations.create(
            model="text-moderation-latest",
            input=text,
        )
        moderation_result = response.results[0]

        # Check if any category is flagged
        flagged = moderation_result.flagged

        if flagged:
            logger.warning("Offensive content detected in transcription. Ignoring.")
            return ""
        else:
            return text

    def _convert_webm_to_wav(self, webm_data):
        webm_audio = AudioSegment.from_file(io.BytesIO(webm_data))
        # Reduce sample rate to 16000 Hz to minimize file size
        webm_audio = webm_audio.set_frame_rate(16000)
        wav_data = io.BytesIO()
        webm_audio.export(wav_data, format="wav")
        wav_data.name = "audio.wav"
        wav_data.seek(0)
        return wav_data

    def _convert_bytes_to_wav(self, audio_bytes):
        wav_data = io.BytesIO(audio_bytes)
        wav_data.name = "audio.wav"
        wav_data.seek(0)
        return wav_data

    def _ulaw_to_wav(self, audio_bytes):
        sound = AudioSegment(
            data=audio_bytes,
            sample_width=1,
            frame_rate=8000,
            channels=1,
        )
        # Upsample to 16000 Hz to match API expectations
        sound = sound.set_frame_rate(16000)
        wav_data = io.BytesIO()
        sound.export(wav_data, format="wav")
        wav_data.name = "audio.wav"
        wav_data.seek(0)
        return wav_data
