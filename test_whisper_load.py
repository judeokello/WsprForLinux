import logging
import traceback
import whisper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whisper_test")

model_name = "tiny"

try:
    logger.info(f"Attempting to load Whisper model: {model_name}")
    model = whisper.load_model(model_name)
    logger.info(f"Successfully loaded Whisper model: {model_name}")
except Exception as e:
    tb = traceback.format_exc()
    logger.error(f"Failed to load Whisper model: {model_name}\nError: {e}\nTraceback:\n{tb}") 