import json
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from .model_constants import OFFICIAL_WHISPER_MODELS
import requests
import hashlib

DEFAULT_UPDATE_INTERVAL_DAYS = 7
DEFAULT_METADATA_PATH = Path.home() / ".config/w4l/model_metadata.json"

class ModelMetadataManager:
    def __init__(self, metadata_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.metadata_path = Path(metadata_path) if metadata_path else DEFAULT_METADATA_PATH
        self.lock = threading.Lock()
        file_existed = self.metadata_path.exists()
        self.data = self._load_metadata()
        self._on_update_callback = None
        self.logger.debug(f"ModelMetadataManager initialized with path: {self.metadata_path}")
        # If the metadata file did not exist, create it now
        if not file_existed:
            self.logger.info(f"Metadata file not found at {self.metadata_path}, creating with online model data.")
            self.refresh_metadata(fetch_online=True)

    def _default_metadata(self) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat() + 'Z'
        next_update = (datetime.utcnow() + timedelta(days=DEFAULT_UPDATE_INTERVAL_DAYS)).isoformat() + 'Z'
        return {
            "update_interval_days": DEFAULT_UPDATE_INTERVAL_DAYS,
            "last_refreshed": now,
            "next_update": next_update,
            "models": {}
        }

    def _load_metadata(self) -> Dict[str, Any]:
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    data = json.load(f)
                    self.logger.debug(f"Loaded metadata from {self.metadata_path}: {len(data.get('models', {}))} models")
                    return data
            except Exception as e:
                self.logger.warning(f"Failed to load metadata from {self.metadata_path}: {e}")
                pass  # Corrupted file, fall back to default
        else:
            self.logger.debug(f"Metadata file does not exist: {self.metadata_path}")
        
        default_data = self._default_metadata()
        self.logger.debug("Using default metadata structure")
        return default_data

    def save_metadata(self):
        with self.lock:
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            self.logger.debug(f"Saved metadata to {self.metadata_path}")

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        info = self.data["models"].get(model_name)
        self.logger.debug(f"Getting model info for '{model_name}': {info}")
        return info

    def update_model_info(self, model_name: str, checksum: str, size: int, status: str):
        now = datetime.utcnow().isoformat() + 'Z'
        model = self.data["models"].setdefault(model_name, {
            "name": model_name,
            "current_checksum": checksum,
            "current_size": size,
            "status": status,
            "history": []
        })
        # Only add to history if checksum/size changed
        if model["current_checksum"] != checksum or model["current_size"] != size:
            model["history"].append({
                "checksum": checksum,
                "size": size,
                "download_date": now
            })
        model["current_checksum"] = checksum
        model["current_size"] = size
        model["status"] = status
        self.logger.debug(f"Updated model info for '{model_name}': checksum={checksum[:8]}..., size={size}, status={status}")
        self.save_metadata()

    def set_update_interval(self, days: int):
        self.data["update_interval_days"] = days
        self.save_metadata()

    def schedule_next_update(self):
        interval = self.data.get("update_interval_days", DEFAULT_UPDATE_INTERVAL_DAYS)
        next_update = (datetime.utcnow() + timedelta(days=interval)).isoformat() + 'Z'
        self.data["next_update"] = next_update
        self.save_metadata()

    def needs_update(self) -> bool:
        next_update = self.data.get("next_update")
        if not next_update:
            return True
        try:
            return datetime.utcnow() >= datetime.fromisoformat(next_update.replace('Z', ''))
        except Exception:
            return True

    def set_on_update_callback(self, callback):
        self._on_update_callback = callback

    def background_check_for_updates(self):
        def check():
            self.logger.debug("Starting background check for model updates")
            with self.lock:
                for model_name, url in OFFICIAL_WHISPER_MODELS.items():
                    checksum = url.split("/")[-2]
                    # Get remote size (HEAD request)
                    try:
                        resp = requests.head(url, timeout=5)
                        resp.raise_for_status()
                        size = int(resp.headers.get('Content-Length', 0))
                    except Exception as e:
                        self.logger.warning(f"Failed to get remote size for {model_name}: {e}")
                        size = None
                    meta = self.data["models"].get(model_name)
                    if meta is None:
                        # New model
                        self.logger.debug(f"Adding new model to metadata: {model_name}")
                        self.data["models"][model_name] = {
                            "name": model_name,
                            "current_checksum": checksum,
                            "current_size": size,
                            "status": "not_downloaded",
                            "history": []
                        }
                    else:
                        # Check for update
                        if meta["current_checksum"] != checksum or meta["current_size"] != size:
                            self.logger.debug(f"Model {model_name} has updates available")
                            meta["status"] = "outdated"
                            meta["history"].append({
                                "checksum": checksum,
                                "size": size,
                                "download_date": datetime.utcnow().isoformat() + 'Z'
                            })
                            meta["current_checksum"] = checksum
                            meta["current_size"] = size
                # Remove models that are no longer in the official list
                for model_name in list(self.data["models"].keys()):
                    if model_name not in OFFICIAL_WHISPER_MODELS:
                        self.logger.debug(f"Removing deprecated model from metadata: {model_name}")
                        del self.data["models"][model_name]
                self.schedule_next_update()
                self.save_metadata()
            # Notify callback if set
            if self._on_update_callback:
                self._on_update_callback()
            self.logger.debug("Background check for model updates completed")
        t = threading.Thread(target=check, daemon=True)
        t.start()

    def ensure_metadata_file(self):
        if not self.metadata_path.exists():
            self.logger.info(f"Metadata file missing, creating default at {self.metadata_path}")
            self.save_metadata()

    def update_last_refreshed(self):
        now = datetime.utcnow().isoformat() + 'Z'
        self.data["last_refreshed"] = now
        self.save_metadata()

    def refresh_metadata(self, fetch_online: bool = False):
        """
        Refresh the metadata for all official models.
        If fetch_online is True, fetch the latest checksums and sizes from the official URLs.
        Otherwise, use the existing metadata for checksums/sizes.
        Always update status based on the actual files on disk.
        This should be called on app load and after any model operation.
        """
        now = datetime.utcnow().isoformat() + 'Z'
        update_interval = self.data.get("update_interval_days", DEFAULT_UPDATE_INTERVAL_DAYS)
        self.data["last_refreshed"] = now
        self.data["next_update"] = (datetime.utcnow() + timedelta(days=update_interval)).isoformat() + 'Z'

        for model_name, url in OFFICIAL_WHISPER_MODELS.items():
            checksum = url.split("/")[-2]
            size = None
            if fetch_online:
                # Try to get the size from a HEAD request
                try:
                    resp = requests.head(url, timeout=5)
                    resp.raise_for_status()
                    size = int(resp.headers.get('Content-Length', 0))
                except Exception as e:
                    self.logger.warning(f"Failed to get remote size for {model_name}: {e}")
            # If not fetching online, use existing size if present
            if not size:
                meta = self.data["models"].get(model_name)
                if meta:
                    size = meta.get("current_size")

            # Check the file on disk
            models_path = Path.home() / ".cache/whisper"
            filepath = models_path / f"{model_name}.pt"
            file_exists = filepath.exists()
            file_size = filepath.stat().st_size if file_exists else None
            file_hash = None
            if file_exists:
                try:
                    with open(filepath, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                except Exception as e:
                    self.logger.warning(f"Failed to hash model file {filepath}: {e}")

            # Determine status
            if file_exists and file_hash == checksum:
                status = "downloaded"
            elif file_exists and file_hash != checksum:
                status = "corrupted"
            else:
                status = "not_downloaded"

            # Update or create metadata entry
            meta = self.data["models"].setdefault(model_name, {
                "name": model_name,
                "current_checksum": checksum,
                "current_size": size,
                "status": status,
                "history": []
            })
            # Only add to history if checksum/size changed
            if meta["current_checksum"] != checksum or meta["current_size"] != size:
                meta["history"].append({
                    "checksum": checksum,
                    "size": size,
                    "download_date": now
                })
            meta["current_checksum"] = checksum
            meta["current_size"] = size
            meta["status"] = status
        # Remove models that are no longer in the official list
        for model_name in list(self.data["models"].keys()):
            if model_name not in OFFICIAL_WHISPER_MODELS:
                self.logger.debug(f"Removing deprecated model from metadata: {model_name}")
                del self.data["models"][model_name]
        self.save_metadata()
        self.logger.info(f"Model metadata refreshed (fetch_online={fetch_online}) at {now}") 