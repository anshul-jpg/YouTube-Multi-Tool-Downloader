import yt_dlp
import logging
import re
import os

def search_youtube(query, max_results=10):
    """Searches YouTube and returns a list of videos."""
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            return result.get('entries', [])
    except Exception as e:
        logging.error(f"Youtube failed: {e}")
        return []

class Downloader:
    def get_video_info(self, url):
        """Fetches video information without downloading."""
        ydl_opts = {'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info

    def _get_sanitized_filename(self, info, ext):
        """Generates a sanitized filename from video info."""
        title = info.get('title', 'video')
        # Remove characters that are invalid in filenames on most OSes
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        return f"{sanitized_title}.{ext}"

    def download(self, url, download_path, quality, file_format, download_subtitles, progress_hook):
        """Downloads the video, renames it, and returns the final path."""
        # Use a simple, temporary name during download
        temp_template = os.path.join(download_path, '%(id)s.%(ext)s')
        
        ydl_opts = {
            'outtmpl': temp_template,
            'progress_hooks': [progress_hook],
            'writesubtitles': download_subtitles,
            'allsubtitles': download_subtitles,
        }

        if file_format in ['mp3', 'wav', 'm4a']:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': file_format,
            }]
        else: # Video download
            height = quality.split('p')[0]
            ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best'
            ydl_opts['merge_output_format'] = file_format

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Determine the temporary path yt-dlp created
            temp_path = ydl.prepare_filename(info).replace('.webm', f'.{file_format}').replace('.m4a', f'.{file_format}')

            # Construct the new, sanitized path and rename the file
            final_filename = self._get_sanitized_filename(info, file_format)
            final_path = os.path.join(download_path, final_filename)
            
            # Ensure we don't try to rename a file that doesn't exist
            if os.path.exists(temp_path):
                os.rename(temp_path, final_path)
                return final_path
            else:
                # Handle cases where the extension is different after post-processing
                base_temp_path = os.path.join(download_path, info['id'])
                possible_temp_path = f"{base_temp_path}.{file_format}"
                if os.path.exists(possible_temp_path):
                    os.rename(possible_temp_path, final_path)
                    return final_path
        
        # Fallback if renaming logic fails
        return None