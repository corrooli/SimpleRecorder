import tkinter as tk
from tkinter import ttk, filedialog
import os
import logging
from typing import List, Tuple

from simple_recorder.core.audio_devices import get_avfoundation_audio_devices, infer_channel_count
from simple_recorder.core.recorder import FFmpegRecorder, RecordingRequest, RecordingMode
from simple_recorder.utils.config import load_config


class SimpleRecorderApp(tk.Tk):
    """
    Main application class for the Simple Recorder UI.
    """
    def __init__(self) -> None:
        super().__init__()
        self.title("Recorder")
        self._recorder = FFmpegRecorder()

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TEntry", font=("Helvetica", 12), padding=5)
        style.configure("TButton", font=("Helvetica", 12, "bold"), padding=6)
        style.configure("TLabelframe", font=("Helvetica", 12, "bold"), padding=10)
        style.configure("TLabelframe.Label", font=("Helvetica", 13, "bold"))

        self.config(padx=20, pady=20)
        self.update_idletasks()
        try:
            self.state('zoomed')
        except Exception:
            pass

        self.audio_devices: List[Tuple[str, str]] = get_avfoundation_audio_devices() or [("0", "Default Device (not found by FFmpeg)")]

        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Audio Device:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        device_names = [f"{idx}: {name}" for (idx, name) in self.audio_devices]
        self.device_combo = ttk.Combobox(main_frame, values=device_names, state="readonly", width=40)
        self.device_combo.current(0)
        self.device_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.device_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_channel_lists())

        ttk.Label(main_frame, text="Total Channels:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.total_channels_var = tk.StringVar()
        self.total_channels_entry = ttk.Entry(main_frame, textvariable=self.total_channels_var, width=10)
        self.total_channels_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(main_frame, text="Audio Stream Index:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.stream_index_var = tk.IntVar(value=0)
        stream_frame = ttk.Frame(main_frame)
        stream_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(stream_frame, text="0", variable=self.stream_index_var, value=0).pack(side="left")
        ttk.Radiobutton(stream_frame, text="1", variable=self.stream_index_var, value=1).pack(side="left")

        ttk.Label(main_frame, text="File Name:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.file_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_name_var, width=30).grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(main_frame, text="Destination Folder:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.dest_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.dest_path_var, width=30).grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(main_frame, text="Browse...", command=self._choose_folder).grid(row=4, column=2, padx=5, pady=5)

        self.record_mode_var = tk.StringVar(value="stereo")
        mode_frame = ttk.LabelFrame(main_frame, text="Input Mode")
        mode_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Radiobutton(mode_frame, text="Mono", variable=self.record_mode_var, value="mono", command=self._on_mode_change).grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Stereo", variable=self.record_mode_var, value="stereo", command=self._on_mode_change).grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Multichannel", variable=self.record_mode_var, value="multichannel", command=self._on_mode_change).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(mode_frame, text="Mono Channel:").grid(row=1, column=0, sticky="e")
        self.mono_channel_var = tk.IntVar(value=1)
        self.mono_channel_dropdown = ttk.Combobox(mode_frame, values=[], textvariable=self.mono_channel_var, state="readonly", width=5)
        self.mono_channel_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(mode_frame, text="Stereo Pair:").grid(row=2, column=0, sticky="e")
        self.stereo_pair_var = tk.StringVar(value="1-2")
        self.stereo_pair_dropdown = ttk.Combobox(mode_frame, values=[], textvariable=self.stereo_pair_var, state="readonly", width=5)
        self.stereo_pair_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        self.record_button = ttk.Button(button_frame, text="Record ⏺", command=self._start_recording)
        self.record_button.grid(row=0, column=0, padx=15, pady=5)
        self.stop_button = ttk.Button(button_frame, text="Stop ⏹", command=self._stop_recording)
        self.stop_button.grid(row=0, column=1, padx=15, pady=5)

        self.status_label = ttk.Label(main_frame, text="Not recording.", font=("Helvetica", 13, "italic"))
        self.status_label.grid(row=7, column=0, columnspan=3, padx=5, pady=10)

        self._update_channel_lists()
        self._on_mode_change()
        self._load_default_settings()
        self._update_channel_lists()
        self._on_mode_change()

    def _log_message(self, message: str) -> None:
        self.status_label.config(text=message)
        logging.info(message)

    def _load_default_settings(self) -> None:
        cfg = load_config()
        if cfg.device_index is not None:
            for i, (dev_idx, _name) in enumerate(self.audio_devices):
                if dev_idx == cfg.device_index:
                    self.device_combo.current(i)
                    break
        self.stream_index_var.set(cfg.stream_index)
        self.file_name_var.set(cfg.file_name)
        self.dest_path_var.set(cfg.destination_folder)
        if cfg.record_mode in ("mono", "stereo", "multichannel"):
            self.record_mode_var.set(cfg.record_mode)
        self.mono_channel_var.set(cfg.mono_channel)
        self.stereo_pair_var.set(cfg.stereo_pair)

    def _choose_folder(self) -> None:
        """
        Open a dialog to choose a destination folder for recordings.
        """
        folder = filedialog.askdirectory()
        if folder:
            self.dest_path_var.set(folder)

    def _update_channel_lists(self) -> None:
        """
        Update the available mono and stereo channel options based on the selected device
        and the total channels specified.
        """
        chosen_device_text = self.device_combo.get()
        if ":" in chosen_device_text:
            name_part = chosen_device_text.split(":", 1)[-1].strip()
        else:
            name_part = chosen_device_text.strip()

        inferred = infer_channel_count(name_part)
        if not self.total_channels_var.get().strip():
            self.total_channels_var.set(str(inferred))

        try:
            total = int(self.total_channels_var.get())
        except ValueError:
            total = inferred

        mono_values = list(range(1, total + 1))
        self.mono_channel_dropdown["values"] = mono_values
        if self.mono_channel_var.get() not in mono_values:
            self.mono_channel_var.set(mono_values[0] if mono_values else 1)

        stereo_vals = []
        for i in range(1, total, 2):
            if i + 1 <= total:
                stereo_vals.append(f"{i}-{i+1}")
        if not stereo_vals:
            stereo_vals = ["1-2"]
        self.stereo_pair_dropdown["values"] = stereo_vals
        if self.stereo_pair_var.get() not in stereo_vals:
            self.stereo_pair_var.set(stereo_vals[0])

    def _on_mode_change(self) -> None:
        """
        Enable/disable channel selection widgets based on the selected recording mode.
        """
        mode = self.record_mode_var.get()
        if mode == "mono":
            self.mono_channel_dropdown.config(state="readonly")
            self.stereo_pair_dropdown.config(state="disabled")
        elif mode == "stereo":
            self.mono_channel_dropdown.config(state="disabled")
            self.stereo_pair_dropdown.config(state="readonly")
        else:
            self.mono_channel_dropdown.config(state="disabled")
            self.stereo_pair_dropdown.config(state="disabled")

    def _build_request(self) -> RecordingRequest:
        """
        Build a RecordingRequest object from the current UI state.
        """
        chosen_device_text = self.device_combo.get()
        try:
            device_index = chosen_device_text.split(":", 1)[0].strip()
        except Exception:
            device_index = "0"

        try:
            total_channels = int(self.total_channels_var.get())
        except ValueError:
            total_channels = 2

        # Map current UI value to enum, default to STEREO if invalid
        mode_str = self.record_mode_var.get()
        try:
            mode_enum = RecordingMode(mode_str)
        except ValueError:
            mode_enum = RecordingMode.STEREO

        req = RecordingRequest(
            device_index=device_index,
            stream_index=self.stream_index_var.get(),
            total_channels=total_channels,
            mode=mode_enum,
            mono_channel=self.mono_channel_var.get(),
            stereo_pair=self.stereo_pair_var.get(),
            dest_folder=self.dest_path_var.get().strip() or os.getcwd(),
            file_name_suffix=self.file_name_var.get().strip(),
        )
        return req

    def _start_recording(self) -> None:
        """
        Start the recording process.
        """
        if self._recorder.is_recording:
            self._log_message("Already recording.")
            return
        try:
            out = self._recorder.start(self._build_request())
            self._log_message(f"Recording -> {out}")
        except Exception as e:
            self._log_message(f"Failed to start: {e}")

    def _stop_recording(self) -> None:
        """
        Stop the recording process.
        """
        if not self._recorder.is_recording:
            self._log_message("Not currently recording.")
            return
        self._recorder.stop()
        self._log_message("Recording stopped.")
