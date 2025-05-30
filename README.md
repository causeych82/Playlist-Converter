# Playlist Converter

A Python tool to convert playlists between Spotify and YouTube.

---

## Features

- Convert Spotify playlists to YouTube playlists  
- Convert YouTube playlists to Spotify playlists  
- Caches YouTube search results for efficiency  
- Supports private and public playlists  

---

## Prerequisites

- Python 3.8 or higher (for source usage)  
- Spotify Developer account with an app created  
- Google Cloud project with YouTube Data API enabled  

---

## Running the Tool

### Run the EXE (Recommended for most users)

1. Download the latest EXE from the [Releases page](https://github.com/causeych82/Playlist-Converter/releases)  
2. Place your credential files (client_secrets.json and spotify_credentials.json) in the same folder as the EXE  
3. Run the EXE directly — no Python installation needed  

---

### Run from source (for developers or advanced users)

1. Clone the repository
```bash
git clone https://github.com/causeych82/Playlist-Converter.git  
cd Playlist-Converter
```

2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Create configuration files

You need two config JSON files:

- client_secrets.json — YouTube OAuth credentials  
- spotify_credentials.json — Spotify API credentials  

You can generate example files by running:
```bash
python setup.py
```
This will create:

- client_secrets.json.example  
- spotify_credentials.json.example  

4. Edit config files

Rename these example files (remove .example) and replace placeholder values with your actual API credentials.

---

## Building the EXE (for developers)

To create a standalone EXE on Windows, run:
```bash
pyinstaller --onefile PlaylistConverter.py
```
The executable will be located in the dist/ folder.

---

## Important Notes

- Do NOT commit your real client_secrets.json or spotify_credentials.json files to GitHub.  
- Use .gitignore to exclude sensitive files and build folders.  
- The .yt_cache.json file caches YouTube search results and is created automatically.  
- If you get YouTube quota errors, request a quota increase from Google or reduce usage.  
- For Spotify API issues, check your app setup at the Spotify Developer Dashboard.  

---

## Troubleshooting

- Ensure API credentials have the correct scopes and redirect URIs  
- Follow instructions carefully for placing config files alongside the EXE  
- Check network/firewall if authentication windows do not open  

---

## License

For personal use only. Not licensed for commercial distribution.

---

## Contact

Created by Chris Causey  
GitHub: [causeych82](https://github.com/causeych82)
