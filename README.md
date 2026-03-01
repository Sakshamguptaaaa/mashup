# Music Mashup Studio

A dual-interface application (Web & CLI) for creating custom music mashups. The project features a bold Neo-Brutalist design and integrates with YouTube for audio source extraction.

## 🚀 Features

- **Neo-Brutalist Interface**: High-contrast black & white design with bold borders and typography.
- **Dual Interface**:
  - **Web Studio**: Select from a curated library of tracks, set durations, and receive your mashup via email or direct download.
  - **CLI Power Tool**: Generate mashups on-the-fly by searching YouTube for any singer.
- **Audio Previews**: Listen to source tracks directly in the web browser before selection.
- **Smart Processing**: Automatic audio cutting and concatenation using FFmpeg.
- **Delivery System**: Background processing with email delivery (ZIP) and temporary download links.
- **Visitor Statistics**: Built-in persistence for tracking visitors and generated mashups.

## 🛠️ Project Structure

```text
mashup-main/
├── app.py              # Flask Web Application & API
├── index.html          # Neo-Brutalist Frontend
├── 102317256.py        # CLI Mashup Generator (YouTube Search)
└── README.md           # Project Documentation
```

## 💻 Usage Instructions

### 1. Web Application
The web interface allows you to create mashups from a pre-downloaded collection of Bollywood hits.

1.  **Launch**: Run `python app.py` and open `http://localhost:5000`.
2.  **Select Songs**: Choose your favorite tracks using the checkboxes in the "Select Songs" section.
3.  **Configure**:
    - Set the **Duration per Song** (10-35 seconds).
    - Enter your **Email** if you wish to receive the mashup as a ZIP file.
4.  **Create**: Click **CREATE MASHUP**.
5.  **Download**: Once processed, a download button will appear, or check your email.

### 2. CLI Tool
The command-line tool provides ultimate flexibility by searching YouTube directly.

```bash
python 102317256.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>
```
**Example:**
```bash
python 102317256.py "Arijit Singh" 15 25 arijit_mix.mp3
```
*Note: NumberOfVideos must be > 10 and AudioDuration must be > 20.*

## ⚙️ Installation & Setup

1.  **Prerequisites**:
    - Python 3.x
    - [FFmpeg](https://ffmpeg.org/download.html) (Mandatory for audio processing)
2.  **Install Dependencies**:
    ```bash
    pip install flask yt-dlp requests python-dotenv
    ```
3.  **Environment Variables** (Optional for Email):
    Create a `.env` file with:
    ```env
    MAILJET_API_KEY=your_key
    MAILJET_API_SECRET=your_secret
    MAIL_USERNAME=your_email
    MAIL_PASSWORD=your_app_password
    ```

## ⚖️ License & Credits

**Author**: Saksham Gupta
**Roll No**: 102317256 
**University**: Thapar Institute of Engineering & Technology  
