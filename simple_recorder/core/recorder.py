"""
Module Description:
Core recording facilities for Simple Recorder.

This module provides:
- RecordingMode: an enumeration of supported recording modes.
- RecordingRequest: a dataclass carrying parameters for a recording session.
- FFmpegRecorder: a controller that builds ffmpeg commands and manages the
  recording subprocess on macOS using the avfoundation input.
"""

import datetime
import os
import signal
import subprocess
import logging
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class RecordingMode(Enum):
    """
    Enumeration of supported recording modes.

    Values correspond to ffmpeg pan/filter behavior and output channel count.
    """
    MONO = "mono"
    STEREO = "stereo"
    MULTICHANNEL = "multichannel"


@dataclass
class RecordingRequest:
    """
    Immutable parameters describing a single recording request.

    Args:
        device_index: AVFoundation audio device index as a string (e.g. "0").
        stream_index: Input stream index to map from ffmpeg (usually 0 or 1).
        total_channels: Total number of channels to request from the device.
        mode: Desired recording mode (mono, stereo, or multichannel).
        mono_channel: 1-based channel number to record when in mono mode.
        stereo_pair: Stereo pair in the form "L-R" (1-based) when in stereo mode.
        dest_folder: Destination directory for the output file.
        file_name_suffix: Optional suffix appended to the timestamped filename.
    """
    device_index: str
    stream_index: int
    total_channels: int
    mode: RecordingMode
    mono_channel: Optional[int] = None  # 1-based
    stereo_pair: Optional[str] = None   # e.g. "1-2"
    dest_folder: str = "."
    file_name_suffix: str = ""


class FFmpegRecorder:
    """
    Controller for launching and stopping ffmpeg-based audio recordings.

    Manages command construction and the lifecycle of the ffmpeg subprocess.
    """
    def __init__(self) -> None:
        """
        Initialize the recorder with no active subprocess.
        """
        self._proc: Optional[subprocess.Popen] = None

    @property
    def is_recording(self) -> bool:
        """
        Indicate whether a recording subprocess is currently running.

        Returns:
            bool: True if ffmpeg is running; False otherwise.
        """
        return self._proc is not None and self._proc.poll() is None

    def _build_base_cmd(self, device_index: str, total_channels: int, stream_index: int) -> List[str]:
        """
        Build the base ffmpeg command for a given device/stream.

        Args:
            device_index (str): AVFoundation audio device index.
            total_channels (int): Requested number of input channels.
            stream_index (int): Input stream index to map from ffmpeg.

        Returns:
            List[str]: The base command parts prior to output/mode filters.
        """
        cmd = [
            "ffmpeg",
            "-thread_queue_size", "512",
            "-y",
            "-f", "avfoundation",
            "-i", f":{device_index}",
            "-ac", str(total_channels),
            "-map", f"0:{stream_index}?",
        ]
        return cmd

    def build_command(self, req: RecordingRequest, output_path: str) -> List[str]:
        """
        Create a full ffmpeg command based on the recording request.

        Args:
            req (RecordingRequest): Parameters describing the recording.
            output_path (str): Destination .wav file path.

        Returns:
            List[str]: The complete ffmpeg command to execute.
        """
        cmd = self._build_base_cmd(req.device_index, req.total_channels, req.stream_index)
        if req.mode == RecordingMode.MONO:
            assert req.mono_channel is not None
            ch = req.mono_channel - 1
            pan_str = f"pan=mono|c0=c{ch}"
            cmd.extend(["-af", pan_str, "-ac", "1", output_path])
        elif req.mode == RecordingMode.STEREO:
            assert req.stereo_pair is not None
            left_str, right_str = req.stereo_pair.split("-")
            left = int(left_str) - 1
            right = int(right_str) - 1
            pan_str = f"pan=stereo|c0=c{left}|c1=c{right}"
            cmd.extend(["-af", pan_str, "-ac", "2", output_path])
        else:  # RecordingMode.MULTICHANNEL
            cmd.append(output_path)
        return cmd

    def start(self, req: RecordingRequest) -> str:
        """
        Start a recording using ffmpeg.

        Args:
            req (RecordingRequest): Parameters describing the recording.

        Returns:
            str: Absolute path to the output .wav file.
        """
        if self.is_recording:
            raise RuntimeError("Already recording")

        now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = now_str
        if req.file_name_suffix:
            file_name += f"_{req.file_name_suffix}"
        file_name += ".wav"

        dest = req.dest_folder or os.getcwd()
        os.makedirs(dest, exist_ok=True)
        output_path = os.path.join(dest, file_name)

        cmd = self.build_command(req, output_path)
        logging.info("Starting ffmpeg: %s", " ".join(cmd))
        self._proc = subprocess.Popen(cmd)
        return output_path

    def stop(self) -> None:
        """
        Stop the current recording if one is active.
        """
        if self._proc and self._proc.poll() is None:
            self._proc.send_signal(signal.SIGINT)
            self._proc.wait()
        self._proc = None
