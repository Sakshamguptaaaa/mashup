import sys
import os
import shutil
import yt_dlp
import subprocess
import time


def validate_arguments(args):
    if len(args) != 5:
        print("Usage: python 102317257.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        sys.exit(1)
    
    try:
        num_videos = int(args[2])
        audio_duration = int(args[3])
    except ValueError:
        print("Error: NumberOfVideos and AudioDuration must be integers")
        sys.exit(1)
    
    if num_videos <= 10:
        print("Error: NumberOfVideos must be greater than 10")
        sys.exit(1)
    
    if audio_duration <= 20:
        print("Error: AudioDuration must be greater than 20")
        sys.exit(1)
    
    return args[1], num_videos, audio_duration, args[4]


def search_youtube_videos(singer_name, num_videos):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        search_query = f"ytsearch{num_videos}:{singer_name}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)
            
        video_urls = []
        if 'entries' in result:
            for video in result['entries']:
                if video:
                    video_urls.append(f"https://www.youtube.com/watch?v={video['id']}")
        
        return video_urls
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []


def download_audio(video_urls, download_folder):
    if os.path.exists(download_folder):
        shutil.rmtree(download_folder)
    os.makedirs(download_folder)
    
    downloaded_files = []
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_folder, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'extractor_retries': 3,
        'retries': 3,
    }
    
    for idx, url in enumerate(video_urls):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    video_id = info['id']
                    mp3_file = os.path.join(download_folder, f"{video_id}.mp3")
                    if os.path.exists(mp3_file):
                        downloaded_files.append(mp3_file)
                        print(f"Downloaded {idx + 1}/{len(video_urls)}")
            time.sleep(1)
        except Exception as e:
            print(f"Failed to download video {idx + 1}")
            continue
    
    return downloaded_files


def cut_and_merge_audio(audio_files, duration, output_file):
    if not audio_files:
        print("Error: No audio files to process")
        sys.exit(1)
    
    temp_clips = []
    
    for idx, audio_file in enumerate(audio_files):
        try:
            temp_clip = os.path.join(os.path.dirname(audio_file), f"clip_{idx}.mp3")
            cmd = [
                'ffmpeg', '-i', audio_file, '-t', str(duration),
                '-acodec', 'libmp3lame', '-y', temp_clip
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            temp_clips.append(temp_clip)
        except Exception as e:
            print(f"Error processing {audio_file}: {e}")
            continue
    
    if not temp_clips:
        print("Error: No valid audio clips to merge")
        sys.exit(1)
    
    try:
        concat_file = os.path.join(os.path.dirname(temp_clips[0]), "concat_list.txt")
        with open(concat_file, 'w') as f:
            for clip in temp_clips:
                f.write(f"file '{clip}'\n")
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy', '-y', output_file
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        os.remove(concat_file)
        for clip in temp_clips:
            os.remove(clip)
        
        print(f"Mashup created successfully: {output_file}")
    except Exception as e:
        print(f"Error exporting mashup: {e}")
        sys.exit(1)


def cleanup(download_folder):
    try:
        if os.path.exists(download_folder):
            shutil.rmtree(download_folder)
    except Exception as e:
        print(f"Warning: Could not cleanup temporary files: {e}")


def main():
    singer_name, num_videos, audio_duration, output_file = validate_arguments(sys.argv)
    
    download_folder = "downloads"
    
    print(f"Searching for {num_videos} videos of {singer_name}...")
    video_urls = search_youtube_videos(singer_name, num_videos)
    
    if not video_urls:
        print("No videos found")
        sys.exit(1)
    
    print(f"Found {len(video_urls)} videos")
    print("Downloading audio...")
    
    audio_files = download_audio(video_urls, download_folder)
    
    if not audio_files:
        print("Failed to download any audio files")
        cleanup(download_folder)
        sys.exit(1)
    
    print(f"Creating mashup with {audio_duration} seconds from each track...")
    cut_and_merge_audio(audio_files, audio_duration, output_file)
    
    cleanup(download_folder)


if __name__ == "__main__":
    main()
