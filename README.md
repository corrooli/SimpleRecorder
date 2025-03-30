# SimpleRecorder
Super simple and fast to use audio recorder, developed for my practice space for my band [Naked Soldier](http://www.nakedsoldier.ch/)
Runs on Mac (Linux in the future too, happy for every contribution!) using FFmpeg.
The goal of this app is to have a super-fast way to start and stop recordings in my practice space, since setting up a full DAW, entering file names, and target path is annoying and I want to focus on practicing and writing songs.
Maybe this app will help you out, too.

## Installation

### Prerequisites
Before using SimpleRecorder, ensure you have the following installed on your Mac:

1. **Python**  
    Install Python via [Homebrew](https://brew.sh/):
    ```bash
    brew install python
    ```

2. **Tkinter**  
    Tkinter is required for the graphical interface. Install it with Homebrew:
    ```bash
    brew install python-tk
    ```

3. **FFmpeg**  
    FFmpeg is used for audio processing. Install it with Homebrew:
    ```bash
    brew install ffmpeg
    ```

### Clone the Repository
Clone the SimpleRecorder repository to your local machine:
```bash
git clone https://github.com/yourusername/SimpleRecorder.git
cd SimpleRecorder
```

## Usage

1. Run the application:
    ```bash
    python simple_recorder.py
    ```

2. Follow the on-screen instructions to start recording audio.

### Storing Default Settings Using `defaultsettings.json` File (Optional)

You can store default settings for SimpleRecorder in a file named `defaultsettings.json`. This file allows you to predefine certain parameters, so you don't have to input them every time you use the application. Below is an example of how the file might look:

```json
{
    "device_index": "1",
    "file_name": "My awesome snake jazz band",
    "destination_folder": "/Users/oliver/Desktop",
    "record_mode": "stereo",
    "mono_channel": 1,
    "stereo_pair": "3-4"
}
```

### Explanation of Keys
- **`device_index`**: Specifies the audio input device to use.  
- **`file_name`**: The default name for the recorded file.  
- **`destination_folder`**: The folder where recordings will be saved.  
- **`record_mode`**: Defines the recording mode (`mono` or `stereo`).  
- **`mono_channel`**: If `record_mode` is `mono`, this specifies the channel to record.  
- **`stereo_pair`**: If `record_mode` is `stereo`, this specifies the stereo pair to use.

### Optional Keys
Not all keys need to be populated. For example, if you only want to set the `destination_folder` and leave other settings to be configured manually, your `defaultsettings.json` file could look like this:

```json
{
    "destination_folder": "/Users/oliver/Desktop"
}
```

When the application runs, it will use the values from `defaultsettings.json` if they are present. Any missing values will need to be provided manually or will use the application's default settings.

## Contributing
Contributions are welcome! Feel free to submit pull requests for Linux support or any other features.

## License
This project is licensed under the GNU Affero GPL Licens (or how I lovingly call it: Spaghetti alfredo license.). See the `LICENSE` file for details.
