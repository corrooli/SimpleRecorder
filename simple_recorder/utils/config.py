"""
Module Description:
Configuration loading utilities for Simple Recorder.

Provides the AppConfig dataclass and a helper to load defaults from
`defaultsettings.json`.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional


DEFAULT_CONFIG_FILE = "defaultsettings.json"


@dataclass
class AppConfig:
    """
    Application configuration values loaded from `defaultsettings.json`.

    Args:
        device_index: AVFoundation device index as a string (e.g., "0").
        stream_index: Input stream index to map from ffmpeg (usually 0 or 1).
        file_name: Optional suffix appended to the timestamp in the output filename.
        destination_folder: Directory where recordings will be saved.
        record_mode: One of "mono", "stereo", or "multichannel".
        mono_channel: 1-based channel number to record in mono mode.
        stereo_pair: Stereo pair in the form "L-R" (1-based) for stereo mode.
    """
    device_index: Optional[str] = None
    stream_index: int = 0
    file_name: str = ""
    destination_folder: str = ""
    record_mode: str = "stereo"
    mono_channel: int = 1
    stereo_pair: str = "1-2"


def load_config(path: str = DEFAULT_CONFIG_FILE) -> AppConfig:
    """
    Load application configuration from a JSON file.

    Args:
        path (str): Path to the configuration JSON file.

    Returns:
        AppConfig: Parsed configuration with sane defaults on error or when
            the file is missing.
    """
    if not os.path.isfile(path):
        return AppConfig()
    try:
        with open(path, "r", encoding="UTF8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return AppConfig()

    return AppConfig(
        device_index=data.get("device_index"),
        stream_index=int(data.get("stream_index", 0)),
        file_name=data.get("file_name", ""),
        destination_folder=data.get("destination_folder", ""),
        record_mode=data.get("record_mode", "stereo"),
        mono_channel=int(data.get("mono_channel", 1)),
        stereo_pair=data.get("stereo_pair", "1-2"),
    )
