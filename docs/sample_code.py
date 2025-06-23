import time
import torch
import whisper
import pyaudio
import wave
from tqdm import tqdm

def log(msg):
    print(f"[⏱ {time.time() - START:.2f}s] {msg}")

START = time.time()
log("Script starting...")

log("Importing Whisper...")
# (Already imported above but kept for clarity)

log("Loading Whisper model...")
model = whisper.load_model("small").to("cpu")
log("Model loaded.")

# Audio setup
log("Setting up PyAudio...")
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

audio = pyaudio.PyAudio()

log("Opening audio stream...")
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

while True:
    input("\nPress Enter to start recording or 'Ctrl+C' to quit...\n")
    log("Recording started.")
    frames = []

    for _ in tqdm(range(0, int(RATE / CHUNK * RECORD_SECONDS)), desc="🎤 Recording"):
        data = stream.read(CHUNK)
        frames.append(data)

    log("Recording finished.")

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    log("Transcribing...")
    start_cpu = time.time()
    result = model.transcribe(WAVE_OUTPUT_FILENAME)
    cpu_time = time.time() - start_cpu

    log(f"Transcript: {result['text']}")
    log(f"CPU transcription time: {cpu_time:.2f} seconds")
