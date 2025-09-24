"""
Module Description:
Audio device discovery helpers for macOS via ffmpeg/avfoundation.

Functions here parse ffmpeg's device listing output and provide a simple API
for enumerating audio devices and inferring channel counts from device names.
"""

import subprocess
import re
import logging
from typing import List, Tuple


def get_avfoundation_audio_devices() -> List[Tuple[str, str]]:
    """
    Enumerate AVFoundation audio devices using ffmpeg.

    Runs `ffmpeg -f avfoundation -list_devices true -i ""` and parses stderr
    to find lines matching the 'AVFoundation audio devices:' section.

    Returns:
        List[Tuple[str, str]]: A list of (index_str, device_name) pairs.
    """
    cmd = ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
    try:
        # Explicitly set check=False so we can parse stderr even when ffmpeg returns non-zero
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        lines = proc.stderr.splitlines()
    except FileNotFoundError as e:
        logging.error("ffmpeg not found! %s", e)
        return []
    except Exception as e:  # Fallback for unexpected runtime issues
        logging.error("Failed to list AVFoundation devices: %s", e)
        return []

    audio_dev_section = False
    devices: List[Tuple[str, str]] = []
    audio_dev_regex = re.compile(r'^\[AVFoundation [^]]+ @.*\]\s+\[(\d+)\]\s+(.+)$')
    for line in lines:
        line = line.strip()
        if "AVFoundation audio devices:" in line:
            audio_dev_section = True
            continue
        if "AVFoundation video devices:" in line:
            audio_dev_section = False
            continue
        if audio_dev_section:
            match = audio_dev_regex.match(line)
            if match:
                idx_str, name = match.groups()
                devices.append((idx_str, name))
    return devices


def infer_channel_count(device_name: str) -> int:
    """
    Infer channel count from a device name string.

    Tries to guess the number of channels by looking for patterns like '16ch', '8ch', etc.
    If none is found, defaults to 2.

    Args:
        device_name (str): Device name string to analyze.

    Returns:
        int: Inferred number of channels (defaults to 2).
    """
    match = re.search(r'(\d+)ch', device_name.lower())
    if match:
        return int(match.group(1))
    return 2  # fallback
