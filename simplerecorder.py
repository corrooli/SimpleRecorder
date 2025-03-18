import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import subprocess
import signal
import datetime
import os
import re

def get_avfoundation_audio_devices():
    """
    Runs `ffmpeg -f avfoundation -list_devices true -i ""` and parses stderr
    to find lines matching the 'AVFoundation audio devices:' section.
    Returns a list of tuples (index_str, device_name).
    Example: [("0", "BlackHole 16ch"), ("1", "Audient EVO16")]
    """
    cmd = ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        lines = proc.stderr.splitlines()
    except Exception:
        return []  # ffmpeg not available

    audio_dev_section = False
    devices = []
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
    Tries to guess the number of channels by looking for patterns like '16ch', '8ch', etc.
    If none is found, defaults to 2.
    """
    match = re.search(r'(\d+)ch', device_name.lower())
    if match:
        return int(match.group(1))
    return 2  # fallback

class SimpleRecorder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Stereo Recorder")
        style = ttk.Style(self)
        style.theme_use("clam")
        self.config(padx=10, pady=10)

        # ========== Gather audio devices ==========
        self.audio_devices = get_avfoundation_audio_devices()
        if not self.audio_devices:
            self.audio_devices = [("0", "Default Device (not found by FFmpeg)")]

        # State
        self.record_process = None

        # ========== Main Frame ==========
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Audio Device selection
        ttk.Label(main_frame, text="Audio Device:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.device_var = tk.StringVar(value=self.audio_devices[0][0])
        device_names = [f"{idx}: {name}" for (idx, name) in self.audio_devices]
        self.device_combo = ttk.Combobox(main_frame, values=device_names, state="readonly", width=40)
        self.device_combo.current(0)
        self.device_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_changed)

        # Total Channels override (editable)
        ttk.Label(main_frame, text="Total Channels:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.total_channels_var = tk.StringVar()
        self.total_channels_entry = ttk.Entry(main_frame, textvariable=self.total_channels_var, width=10)
        self.total_channels_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Audio Stream Index (0 or 1)
        ttk.Label(main_frame, text="Audio Stream Index:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.stream_index_var = tk.IntVar(value=0)
        stream_frame = ttk.Frame(main_frame)
        stream_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(stream_frame, text="0", variable=self.stream_index_var, value=0).pack(side="left")
        ttk.Radiobutton(stream_frame, text="1", variable=self.stream_index_var, value=1).pack(side="left")

        # Band Name
        ttk.Label(main_frame, text="Band Name:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.band_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.band_name_var, width=30).grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Destination Folder
        ttk.Label(main_frame, text="Destination Folder:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.dest_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.dest_path_var, width=30).grid(row=4, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(main_frame, text="Browse...", command=self.choose_folder).grid(row=4, column=2, padx=5, pady=5)

        # Input Mode: Mono / Stereo / Multichannel
        self.record_mode_var = tk.StringVar(value="stereo")
        mode_frame = ttk.LabelFrame(main_frame, text="Input Mode")
        mode_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Radiobutton(mode_frame, text="Mono", variable=self.record_mode_var,
                        value="mono", command=self.on_mode_change).grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Stereo", variable=self.record_mode_var,
                        value="stereo", command=self.on_mode_change).grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="Multichannel", variable=self.record_mode_var,
                        value="multichannel", command=self.on_mode_change).grid(row=0, column=2, padx=5, pady=5)

        # For mono and stereo, let user choose channels:
        ttk.Label(mode_frame, text="Mono Channel:").grid(row=1, column=0, sticky="e")
        self.mono_channel_var = tk.IntVar(value=1)
        self.mono_channel_dropdown = ttk.Combobox(mode_frame, values=[], textvariable=self.mono_channel_var,
                                                  state="readonly", width=5)
        self.mono_channel_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(mode_frame, text="Stereo Pair:").grid(row=2, column=0, sticky="e")
        self.stereo_pair_var = tk.StringVar(value="1-2")
        self.stereo_pair_dropdown = ttk.Combobox(mode_frame, values=[], textvariable=self.stereo_pair_var,
                                                 state="readonly", width=5)
        self.stereo_pair_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        self.record_button = ttk.Button(button_frame, text="Record ⏺", command=self.start_recording)
        self.record_button.grid(row=0, column=0, padx=5, pady=5)
        self.stop_button = ttk.Button(button_frame, text="Stop ⏹", command=self.stop_recording)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        # Status Label
        self.status_label = ttk.Label(main_frame, text="Not recording.")
        self.status_label.grid(row=7, column=0, columnspan=3, padx=5, pady=5)

        self.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Initialize channel lists and total channels field
        self.update_channel_lists()
        self.on_mode_change()

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_path_var.set(folder)

    def on_device_changed(self, event=None):
        """Called when user picks a different device."""
        self.update_channel_lists()

    def update_channel_lists(self):
        """
        Uses the selected device name to infer the channel count and updates the
        mono and stereo channel selection dropdowns.
        Also sets the Total Channels field.
        """
        chosen_device_text = self.device_combo.get()  # e.g., "1: Audient EVO16"
        name_part = chosen_device_text.split(":", 1)[-1].strip()
        inferred = infer_channel_count(name_part)
        self.total_channels_var.set(str(inferred))
        total = inferred

        # Mono: channels 1 to total
        mono_values = list(range(1, total + 1))
        self.mono_channel_dropdown["values"] = mono_values
        self.mono_channel_var.set(mono_values[0])

        # Stereo pairs: (1-2, 3-4, etc.)
        stereo_vals = []
        for i in range(1, total, 2):
            if i + 1 <= total:
                stereo_vals.append(f"{i}-{i+1}")
        if not stereo_vals:
            stereo_vals = ["1-2"]
        self.stereo_pair_dropdown["values"] = stereo_vals
        self.stereo_pair_var.set(stereo_vals[0])

    def on_mode_change(self):
        """Enable/disable controls based on recording mode."""
        mode = self.record_mode_var.get()
        if mode == "mono":
            self.mono_channel_dropdown.config(state="readonly")
            self.stereo_pair_dropdown.config(state="disabled")
        elif mode == "stereo":
            self.mono_channel_dropdown.config(state="disabled")
            self.stereo_pair_dropdown.config(state="readonly")
        else:  # multichannel
            self.mono_channel_dropdown.config(state="disabled")
            self.stereo_pair_dropdown.config(state="disabled")

    def start_recording(self):
        if self.record_process and self.record_process.poll() is None:
            self.status_label.config(text="Already recording.")
            return

        # Construct output filename
        band_name = self.band_name_var.get().strip()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{now_str}"
        if band_name:
            filename += f"_{band_name}"
        filename += ".wav"
        destination_folder = self.dest_path_var.get().strip() or os.getcwd()
        output_path = os.path.join(destination_folder, filename)

        # Get device index (e.g., "1: Audient EVO16")
        chosen_device_text = self.device_combo.get()
        try:
            device_index = chosen_device_text.split(":", 1)[0].strip()
        except:
            device_index = "0"

        audio_stream_idx = self.stream_index_var.get()
        mode = self.record_mode_var.get()
        try:
            total_channels = int(self.total_channels_var.get())
        except:
            total_channels = 2

        # Build base command:
        # Force capturing with -ac set to total_channels
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "avfoundation",
            "-i", f":{device_index}",
            "-ac", str(total_channels),
            "-ar", "48000"
        ]
        # Map the chosen audio stream with a trailing '?' to avoid mapping errors.
        cmd.extend(["-map", f"0:{audio_stream_idx}?"])

        if mode == "mono":
            ch = self.mono_channel_var.get() - 1  # 0-based channel index for selection
            pan_str = f"pan=mono|c0=c{ch}"
            cmd.extend(["-af", pan_str, "-ac", "1", output_path])
            status_msg = (f"Recording MONO (channel {ch+1}) on device :{device_index} stream {audio_stream_idx} -> {output_path}")
        elif mode == "stereo":
            pair = self.stereo_pair_var.get()  # e.g., "1-2"
            left_str, right_str = pair.split("-")
            left = int(left_str) - 1
            right = int(right_str) - 1
            pan_str = f"pan=stereo|c0=c{left}|c1=c{right}"
            cmd.extend(["-af", pan_str, "-ac", "2", output_path])
            status_msg = (f"Recording STEREO (channels {left+1}-{right+1}) on device :{device_index} stream {audio_stream_idx} -> {output_path}")
        else:  # multichannel mode: record all channels without any pan filter
            cmd.append(output_path)
            status_msg = (f"Recording MULTICHANNEL (all {total_channels} channels) on device :{device_index} stream {audio_stream_idx} -> {output_path}")

        self.status_label.config(text=status_msg)
        # Launch ffmpeg; its logs will print to your Terminal.
        self.record_process = subprocess.Popen(cmd)

    def stop_recording(self):
        if self.record_process and self.record_process.poll() is None:
            self.record_process.send_signal(signal.SIGINT)
            self.record_process.wait()
            self.record_process = None
            self.status_label.config(text="Recording stopped.")
        else:
            self.status_label.config(text="Not currently recording.")

if __name__ == "__main__":
    app = SimpleRecorder()
    app.mainloop()
