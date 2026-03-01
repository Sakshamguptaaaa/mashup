from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import shutil
import subprocess
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import zipfile
import yt_dlp
import time
import uuid
import threading
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')

# Store generated mashups temporarily
MASHUP_STORAGE = {}
# Track email send status per mashup_id: 'pending'|'sent'|'failed'|'not_configured'|'none'
EMAIL_STATUS = {}

# ffmpeg path
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', '/opt/homebrew/bin/ffmpeg')
# On Render, ffmpeg will be at /usr/bin/ffmpeg
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = 'ffmpeg'  # Use system ffmpeg

def create_mashup(song_filenames, duration):
    """Create mashup from existing downloaded songs"""
    print(f"=== CREATE MASHUP CALLED with {len(song_filenames)} songs, duration={duration} ===", flush=True)
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(temp_dir, "output.mp3")
    downloads_folder = os.path.join(os.path.dirname(__file__), "downloads")
    
    try:
        # Use existing downloaded files
        source_files = []
        for filename in song_filenames:
            source_path = os.path.join(downloads_folder, filename)
            if os.path.exists(source_path):
                source_files.append(source_path)
                print(f"Found: {filename}", flush=True)
        
        if not source_files:
            raise Exception("No valid songs selected")
        
        print(f"Processing {len(source_files)} files...", flush=True)
        
        # Cut audio clips to specified duration
        temp_clips = []
        for idx, audio_file in enumerate(source_files):
            print(f"Cutting clip {idx+1}/{len(source_files)}...", flush=True)
            temp_clip = os.path.join(temp_dir, f"clip_{idx}.mp3")
            cmd = [FFMPEG_PATH, '-i', audio_file, '-t', str(duration), '-acodec', 'libmp3lame', '-y', temp_clip]
            result = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if result.returncode != 0:
                print(f"ffmpeg error: {result.stderr.decode()}", flush=True)
                raise Exception(f"ffmpeg failed for {audio_file}")
            temp_clips.append(temp_clip)
            print(f"Clip {idx+1} done", flush=True)
        
        # Concatenate all clips
        print("Concatenating clips...", flush=True)
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for clip in temp_clips:
                f.write(f"file '{clip}'\n")
        
        cmd = [FFMPEG_PATH, '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', '-y', output_file]
        result = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode != 0:
            print(f"concat error: {result.stderr.decode()}", flush=True)
            raise Exception("ffmpeg concat failed")
        
        print(f"Mashup created: {output_file}", flush=True)
        return output_file, temp_dir
    
    except Exception as e:
        print(f"ERROR in create_mashup: {str(e)}", flush=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


def send_email(to_email, attachment_path, songs_list):
    """Send mashup as ZIP via email"""
    from_email = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    
    if not from_email or not password:
        raise Exception("Email credentials not configured")
    
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = '🎵 Your Custom Mashup is Ready!'
    
    # Convert filenames to song numbers
    song_names = []
    all_songs = [
        'E_SbwSe15y0.mp3', '75o1iC1OSrE.mp3', '7SLGxEDyqWo.mp3', 'GFljvZMZI0U.mp3',
        'HoCwa6gnmM0.mp3', 'II2EO3Nw4m0.mp3', 'Op_UWVBWj3c.mp3', 'YyepU5ztLf4.mp3',
        'ZtgchQLx3ao.mp3', 'b4b1cMVZOUU.mp3', 'eM8Mjuq4MwQ.mp3', 'e_vl5aFXB4Q.mp3',
        'gdZyzxJPzP8.mp3', 'qpIdoaaPa6U.mp3', 'yDv0WSgXJVg.mp3', 'zC3UbTf4qrM.mp3',
        'Mmu-tj-psuk.mp3', 'ZHzTI5YCksY.mp3'
    ]
    
    for song_file in songs_list:
        if song_file in all_songs:
            song_num = all_songs.index(song_file) + 1
            song_names.append(f"Bollywood Hit #{song_num}")
        else:
            song_names.append(song_file)
    
    songs_html = "".join([f"<li style='margin: 8px 0; font-size: 16px;'>{name}</li>" for name in song_names])
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border: 3px solid #000000;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px; text-align: center; border-bottom: 3px solid #000000; background-color: #000000;">
                                <h1 style="margin: 0; font-size: 36px; font-weight: 900; color: #ffffff; letter-spacing: -1px;">MASHUP STUDIO</h1>
                                <p style="margin: 10px 0 0 0; font-size: 14px; color: #cccccc; font-weight: 600;">Create Professional Music Mashups</p>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; font-size: 24px; font-weight: 900; color: #000000;">Your Mashup is Ready! 🎵</h2>
                                
                                <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; color: #333333;">
                                    Hello Music Lover,
                                </p>
                                
                                <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.6; color: #333333;">
                                    Your custom Bollywood mashup has been created successfully! Your personalized mix is attached as a ZIP file.
                                </p>
                                
                                <div style="background-color: #f9f9f9; border: 2px solid #000000; padding: 25px; margin-bottom: 30px;">
                                    <h3 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 900; color: #000000; text-transform: uppercase;">Songs Included:</h3>
                                    <ul style="margin: 0; padding-left: 25px; list-style-type: square;">
                                        {songs_html}
                                    </ul>
                                </div>
                                
                                <p style="margin: 0 0 10px 0; font-size: 16px; line-height: 1.6; color: #333333;">
                                    <strong>📎 Attachment:</strong> mashup.zip
                                </p>
                                
                                <p style="margin: 30px 0 0 0; font-size: 16px; line-height: 1.6; color: #333333;">
                                    Enjoy your music!
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px; background-color: #000000; text-align: center; border-top: 3px solid #000000;">
                                <p style="margin: 0 0 15px 0; font-size: 14px; font-weight: 700; color: #ffffff;">
                                    
                                </p>
                                
                                <p style="margin: 0 0 20px 0; font-size: 12px; color: #cccccc;">
                                    Roll No: 102317257
                                </p>
                                
                                <div style="margin: 20px 0;">
                                    <a href="https://www.linkedin.com/in/deepanshtandon012/" style="display: inline-block; margin: 0 10px; padding: 12px 24px; background-color: #ffffff; color: #000000; text-decoration: none; font-weight: 900; font-size: 12px; border: 2px solid #ffffff; text-transform: uppercase; letter-spacing: 1px;">
                                        💼 LINKEDIN
                                    </a>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Plain text fallback
    text_body = f"""
    MASHUP STUDIO
    Your Custom Mashup is Ready!
    
    Hello Music Lover,
    
    Your custom Bollywood mashup has been created successfully!
    
    Songs Included:
    {chr(10).join(['• ' + name for name in song_names])}
    
    Please find the attached mashup.zip file.
    
    Enjoy your music!
    
    ---
    Made by Deepansh Tandon (Roll No: 102317257)
    """
    
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    # Create ZIP file
    zip_path = attachment_path.replace('.mp3', '.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(attachment_path, 'custom_mashup.mp3')
    
    # Attach ZIP
    with open(zip_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename=mashup.zip')
        msg.attach(part)
    
    # Use Mailjet HTTP API as primary email provider (recommended for cloud hosts)
    mailjet_key = os.environ.get('MAILJET_API_KEY')
    mailjet_secret = os.environ.get('MAILJET_API_SECRET')
    if mailjet_key and mailjet_secret:
        try:
            print("Attempting Mailjet API send (primary)...", flush=True)
            with open(zip_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode()

            mj_payload = {
                "Messages": [
                    {
                        "From": {"Email": os.environ.get('MAIL_FROM', from_email)},
                        "To": [{"Email": to_email}],
                        "Subject": msg['Subject'],
                        "TextPart": text_body,
                        "HTMLPart": html_body,
                        "Attachments": [
                            {"ContentType": "application/zip", "Filename": "mashup.zip", "Base64Content": encoded}
                        ]
                    }
                ]
            }
            resp = requests.post(
                'https://api.mailjet.com/v3.1/send',
                json=mj_payload,
                auth=(mailjet_key, mailjet_secret),
                timeout=10
            )
            if resp.status_code in (200, 201):
                print(f"Mailjet: email queued to {to_email}", flush=True)
                return
            else:
                raise Exception(f"Mailjet API error: {resp.status_code} {resp.text}")
        except Exception as mj_exc:
            print(f"Mailjet primary failed: {mj_exc}", flush=True)
            raise
    else:
        raise Exception("Mailjet not configured")


@app.route('/')
def index():
    return send_file('index.html')


@app.route('/bollywood_mashup.mp3')
def serve_bollywood_mashup():
    """Serve the pre-made bollywood mashup"""
    filepath = os.path.join(os.path.dirname(__file__), 'bollywood_mashup.mp3')
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg')
    return jsonify({'error': 'File not found'}), 404


@app.route('/downloads/<filename>')
def serve_download(filename):
    """Serve individual downloaded songs"""
    filepath = os.path.join(os.path.dirname(__file__), 'downloads', filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg')
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/create-mashup', methods=['POST'])
def create_mashup_api():
    print("=== API CALLED ===", flush=True)
    try:
        # Ensure directories exist
        os.makedirs('mashups', exist_ok=True)
        os.makedirs('downloads', exist_ok=True)
        
        data = request.get_json()
        print(f"Received data: {data}", flush=True)
        
        songs = data.get('songs', [])
        duration = int(data.get('duration', 20))
        email = data.get('email')
        
        print(f"Songs: {songs}, Duration: {duration}", flush=True)
        
        if not songs:
            return jsonify({'error': 'Please select at least one song'}), 400
        
        if duration < 10 or duration > 35:
            return jsonify({'error': 'Duration must be between 10-35 seconds'}), 400
        
        # Create mashup
        output_file, temp_dir = create_mashup(songs, duration)
        
        # Generate unique ID for download
        mashup_id = str(uuid.uuid4())
        
        # Create ZIP file
        zip_path = output_file.replace('.mp3', '.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(output_file, 'custom_mashup.mp3')
        
        # Store mashup temporarily (will be cleaned up after 1 hour)
        MASHUP_STORAGE[mashup_id] = {
            'zip_path': zip_path,
            'mp3_path': output_file,
            'temp_dir': temp_dir
        }
        
        # Send email if provided and credentials are configured (SMTP or Mailjet)
        message = 'Mashup created successfully! Download below.'
        mail_status = 'none'
        if email:
            from_email = os.environ.get('MAIL_USERNAME')
            password = os.environ.get('MAIL_PASSWORD')
            mailjet_key = os.environ.get('MAILJET_API_KEY')
            mailjet_secret = os.environ.get('MAILJET_API_SECRET')

            # Allow sending if Mailjet is configured OR SMTP creds are present
            if (mailjet_key and mailjet_secret) or (from_email and password):
                try:
                    # Send email in background thread to avoid blocking the request
                    def _send_and_log(to_addr, attach_path, songs_list, mid):
                        try:
                            send_email(to_addr, attach_path, songs_list)
                            EMAIL_STATUS[mid] = 'sent'
                            print(f"Email successfully sent to {to_addr}", flush=True)
                        except Exception as exc:
                            EMAIL_STATUS[mid] = f'failed: {exc}'
                            print(f"Email send error for {to_addr}: {exc}", flush=True)
                    # mark pending and start thread with mashup id
                    EMAIL_STATUS[mashup_id] = 'pending'
                    email_thread = threading.Thread(target=_send_and_log, args=(email, output_file, songs, mashup_id))
                    email_thread.daemon = True
                    email_thread.start()
                    mail_status = 'pending'
                    message = f'✅ Mashup created! Email will be sent to {email} shortly.'
                except Exception as e:
                    print(f"Failed to start email thread: {e}", flush=True)
                    EMAIL_STATUS[mashup_id] = f'failed: {e}'
                    mail_status = 'failed'
                    message = f'✅ Mashup created! (Email failed - using download link instead)'
            else:
                message = '✅ Mashup created! (Email not configured - use download link below)'
                mail_status = 'not_configured'
        
        return jsonify({
            'message': message,
            'download_url': f'/download-mashup/{mashup_id}',
            'mail_status': mail_status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download-mashup/<mashup_id>')
def download_custom_mashup(mashup_id):
    """Download generated mashup"""
    if mashup_id not in MASHUP_STORAGE:
        return jsonify({'error': 'Mashup not found or expired'}), 404
    
    mashup_data = MASHUP_STORAGE[mashup_id]
    zip_path = mashup_data['zip_path']
    
    if not os.path.exists(zip_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(zip_path, as_attachment=True, download_name='mashup.zip')


@app.route('/email-status/<mashup_id>')
def email_status_endpoint(mashup_id):
    """Return email send status for a given mashup id"""
    status = EMAIL_STATUS.get(mashup_id, 'none')
    return jsonify({'mail_status': status})


@app.route('/download/<singer>')
def download_mashup(singer):
    """Legacy endpoint - not used anymore"""
    return jsonify({'message': 'Use the form to create a custom mashup'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
