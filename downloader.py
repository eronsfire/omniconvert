import os
import yt_dlp
from utils import obter_pasta_downloads

class VideoDownloader:
    def __init__(self, callback_status, callback_progress):
        self.mostrar_status = callback_status
        self.progress_hook = callback_progress

    def baixar_midia(self, url: str, formato_escolhido: str, eh_social: bool = False):
        """Baixa mídias das redes suportadas."""
        pasta_dest = obter_pasta_downloads()

        ydl_opts = {
            'format': formato_escolhido,
            'outtmpl': os.path.join(pasta_dest, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'quiet': True,
            'noprogress': True,
        }

        # Converte automaticamente para MP3 se o formato escolhido for de áudio
        if "bestaudio" in formato_escolhido or "ba" in formato_escolhido:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        if eh_social:
            ydl_opts.update({
                'no_warnings': True,
                'extractor_args': {
                    'tiktok': {
                        'api_hostname': 'api16-normal-c-useast1a.tiktokv.com',
                        'app_name': 'musical_ly',
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            })
        else:
            ydl_opts.update({
                'check_formats': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web_creator', 'android'],
                        'player_skip': ['js', 'configs', 'webpage'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Android 14; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                }
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as err:
            self.mostrar_status(f"Erro ao baixar mídia: {str(err)}", True)