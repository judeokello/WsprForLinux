# src/transcription/model_manager.py

import os
import hashlib
import requests
import logging
from typing import Dict, Optional, List, Callable
from pathlib import Path
from .model_metadata_manager import ModelMetadataManager
from .model_constants import OFFICIAL_WHISPER_MODELS

class ModelManager:
    """
    Manages Whisper models, including downloading, verifying, and listing.
    Integrates with ModelMetadataManager for persistent metadata and background updates.
    """
    def __init__(self, models_path: Optional[str] = None, metadata_manager: Optional[ModelMetadataManager] = None):
        self.logger = logging.getLogger(__name__)
        if models_path:
            self.models_path = Path(models_path)
        else:
            self.models_path = Path.home() / ".cache/whisper"
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.metadata_manager = metadata_manager or ModelMetadataManager()
        self.logger.debug(f"ModelManager initialized with models_path: {self.models_path}")
        self.logger.debug(f"Metadata manager path: {self.metadata_manager.metadata_path}")

    def get_model_info(self, name: str) -> Dict:
        """Gets information for a single model, using metadata manager if available."""
        if name not in OFFICIAL_WHISPER_MODELS:
            raise ValueError(f"Model '{name}' not found in official list.")

        url = OFFICIAL_WHISPER_MODELS[name]
        checksum = url.split("/")[-2]
        filename = f"{name}.pt"
        filepath = self.models_path / filename
        meta = self.metadata_manager.get_model_info(name) or {}
        status = meta.get("status", "not_downloaded")
        size = meta.get("current_size")
        
        self.logger.debug(f"Model info for '{name}': status={status}, size={size}, filepath={filepath}, exists={filepath.exists()}")
        
        return {
            "name": name,
            "url": url,
            "checksum": checksum,
            "filename": filename,
            "filepath": filepath,
            "status": status,
            "size_bytes": size,
            "history": meta.get("history", [])
        }

    def list_models(self) -> List[Dict]:
        """
        Lists all official Whisper models with their status from metadata manager.
        """
        models = []
        self.logger.debug(f"Listing models from directory: {self.models_path}")
        
        for name in OFFICIAL_WHISPER_MODELS.keys():
            info = self.get_model_info(name)
            info["is_downloaded"] = info['filepath'].exists()
            # Use checksum verification for 'is_verified'
            info["is_verified"] = self.verify_model(name) if info["is_downloaded"] else False
            self.logger.debug(f"Model '{name}': downloaded={info['is_downloaded']}, verified={info['is_verified']}")
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
            self.logger.debug(f"Model file does not exist: {info['filepath']}")
            return False

        self.logger.debug(f"Verifying model '{name}' with checksum: {info['checksum']}")
        try:
            with open(info['filepath'], "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            is_valid = file_hash == info['checksum']
            self.logger.debug(f"Model '{name}' verification result: {is_valid} (file_hash: {file_hash[:8]}..., expected: {info['checksum'][:8]}...)")
            return is_valid
        except Exception as e:
            self.logger.error(f"Error verifying model '{name}': {e}")
            return False

    def download_model(self, name: str, progress_callback: Optional[Callable] = None):
        """
        Downloads a model, verifying its checksum.
        A progress_callback can be provided to report download progress.
        It will be called with (bytes_downloaded, total_bytes).
        """
        info = self.get_model_info(name)
        url = info['url']
        filepath = info['filepath']
        checksum = info['checksum']

        self.logger.info(f"Starting download of model '{name}' from {url}")

        # In case of partial download, remove it.
        if filepath.exists() and not self.verify_model(name):
            self.logger.warning(f"Removing corrupted model file: {filepath}")
            filepath.unlink()

        if filepath.exists() and self.verify_model(name):
            self.logger.info(f"Model '{name}' already exists and is valid")
            if progress_callback:
                size = filepath.stat().st_size
                progress_callback(size, size)
            return

        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            self.logger.debug(f"Downloading {total_size} bytes for model '{name}'")

            if progress_callback:
                progress_callback(0, total_size)

            with open(filepath, 'wb') as f:
                bytes_downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(bytes_downloaded, total_size)

            self.logger.debug(f"Download completed for model '{name}', verifying checksum...")

            if not self.verify_model(name):
                self.logger.error(f"Checksum verification failed for model '{name}' after download.")
                filepath.unlink(missing_ok=True)
                raise Exception("Model checksum verification failed after download.")

            # Update metadata
            self.metadata_manager.update_model_info(
                name, checksum, total_size, status="downloaded"
            )

            self.logger.info(f"Model '{name}' downloaded and verified successfully")

        except Exception as e:
            # If download fails, remove partial file
            if filepath.exists():
                filepath.unlink(missing_ok=True)
            self.logger.error(f"Download failed for model '{name}': {e}")
            raise

    def trigger_background_metadata_update(self):
        """Trigger a background check for model updates."""
        self.logger.debug("Triggering background metadata update")
        self.metadata_manager.background_check_for_updates() 