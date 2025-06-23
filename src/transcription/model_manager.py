# src/transcription/model_manager.py

import os
import hashlib
import requests
from typing import Dict, Optional, List, Callable
from pathlib import Path

# This dictionary is from the whisper library source code.
# It contains the official model names, their download URLs, and SHA256 checksums.
# The checksum is part of the URL.
OFFICIAL_WHISPER_MODELS = {
    "tiny.en": "https://openaipublic.azureedge.net/main/whisper/models/d3dd57d32accea0b295c96e26691aa14d8822fac7d9d27d5dc00b4ca2826dd03/tiny.en.pt",
    "tiny": "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
    "base.en": "https://openaipublic.azureedge.net/main/whisper/models/25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead/base.en.pt",
    "base": "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
    "small.en": "https://openaipublic.azureedge.net/main/whisper/models/f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872/small.en.pt",
    "small": "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
    "medium.en": "https://openaipublic.azureedge.net/main/whisper/models/d7440d1dc186f76616474e0ff0b3b6b879abc9d1a4926b7adfa41db2d497ab4f/medium.en.pt",
    "medium": "https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt",
    "large-v1": "https://openaipublic.azureedge.net/main/whisper/models/e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a/large-v1.pt",
    "large-v2": "https://openaipublic.azureedge.net/main/whisper/models/81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/large-v2.pt",
    "large-v3": "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt",
    "large": "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt",
}

class ModelManager:
    """
    Manages Whisper models, including downloading, verifying, and listing.
    """
    def __init__(self, models_path: Optional[str] = None):
        if models_path:
            self.models_path = Path(models_path)
        else:
            self.models_path = Path.home() / ".cache/whisper"
        self.models_path.mkdir(parents=True, exist_ok=True)

    def get_model_info(self, name: str) -> Dict:
        """Gets information for a single model."""
        if name not in OFFICIAL_WHISPER_MODELS:
            raise ValueError(f"Model '{name}' not found in official list.")

        url = OFFICIAL_WHISPER_MODELS[name]
        checksum = url.split("/")[-2]
        filename = f"{name}.pt"
        filepath = self.models_path / filename

        return {
            "name": name,
            "url": url,
            "checksum": checksum,
            "filename": filename,
            "filepath": filepath,
        }

    def list_models(self) -> List[Dict]:
        """
        Lists all official Whisper models with their status.
        """
        models = []
        for name in OFFICIAL_WHISPER_MODELS.keys():
            info = self.get_model_info(name)
            info["size_bytes"] = self.get_remote_model_size(info['url'])
            info["is_downloaded"] = info['filepath'].exists()
            info["is_verified"] = self.verify_model(name) if info["is_downloaded"] else False
            models.append(info)
        return models

    def get_remote_model_size(self, url: str) -> Optional[int]:
        """
        Gets the size of a remote file in bytes using a HEAD request.
        """
        try:
            response = requests.head(url, timeout=5)
            response.raise_for_status()
            return int(response.headers.get('Content-Length', 0))
        except requests.RequestException:
            return None

    def verify_model(self, name: str) -> bool:
        """
        Verifies the checksum of a downloaded model.
        """
        info = self.get_model_info(name)
        if not info['filepath'].exists():
            return False

        with open(info['filepath'], "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return file_hash == info['checksum']

    def download_model(self, name: str, progress_callback: Optional[Callable] = None):
        """
        Downloads a model, verifying its checksum.
        A progress_callback can be provided to report download progress.
        It will be called with (bytes_downloaded, total_bytes).
        """
        info = self.get_model_info(name)
        url = info['url']
        filepath = info['filepath']
        
        # In case of partial download, remove it.
        if filepath.exists() and not self.verify_model(name):
            filepath.unlink()

        if filepath.exists() and self.verify_model(name):
            if progress_callback:
                size = filepath.stat().st_size
                progress_callback(size, size)
            return

        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                bytes_downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(bytes_downloaded, total_size)
            
            if not self.verify_model(name):
                raise Exception("Model checksum verification failed after download.")

        except requests.RequestException as e:
            # If download fails, remove partial file
            if filepath.exists():
                filepath.unlink()
            raise e 