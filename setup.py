#!/usr/bin/env python3
"""
Setup script for WsprForLinux (W4L)
"""

from setuptools import setup, find_packages

setup(
    name="wsprforlinux",
    version="0.1.0",
    description="Offline voice input assistant for Linux using local Whisper model",
    author="W4L Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pyaudio>=0.2.11",
        "numpy>=1.21.0",
        "soundfile>=0.10.3",
        "openai-whisper>=20231117",
        "torch>=1.9.0",
        "torchaudio>=0.9.0",
        "json5>=0.9.0",
        "psutil>=5.8.0",
        "pydub>=0.25.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ]
    },
) 