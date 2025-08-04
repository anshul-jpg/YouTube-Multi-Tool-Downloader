
# YouTube-Multi-Tool-Downloader

YouTube Multi-Tool Downloader is a Python-based desktop application that provides a seamless experience for downloading YouTube content. Built with customtkinter for a modern UI and powered by yt-dlp for reliable downloads, this tool eliminates the need for browser extensions or questionable online services.



## Badges


![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)


# ✨ Features

 Built-in Search: Find videos directly within the app without opening a browser


 Download History: Complete download log with quick access to files and folders

 Multiple Formats:

Video: MP4, MKV, WEBM

Audio: MP3, M4A, WAV

 Quality Selection: Choose from available video resolutions

 Batch Downloads: Queue multiple URLs for sequential downloading

 Subtitle Support: Download available captions for videos

 Modern Interface: Clean, intuitive design using customtkinter
## Installation

Clone the repository:
git clone YouTube-Multi-Tool-Downloader

cd youtube-multi-tool-downloader

Create virtual environment:
python -m venv .venv

Activate virtual environment:
# Windows
.venv\Scripts\activate
# macOS/Linux  
source .venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Install FFmpeg (Required):
Download from https://ffmpeg.org/download.html
Add to system PATH
Verify: ffmpeg -version

    
## Usage

Launch the application:
python main.py

Basic Workflow:
1. Search or paste YouTube URLs
2. Select format and quality
3. Configure options (subtitles if needed)
4. Start download
5. Access files via History tab

For batch downloads, paste multiple URLs separated by new lines.



## Environment Variables
No environment variables required for basic usage.

Optional:
- DOWNLOAD_PATH: Custom default download location
- FFMPEG_PATH: Custom FFmpeg binary path

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Areas for contribution:
- Bug fixes
- Feature enhancements  
- UI improvements
- Documentation updates


## Authors

- [@Anshul](https://github.com/anshul-jpg)


## Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader engine
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [FFmpeg](https://ffmpeg.org/) - Video/audio processing

