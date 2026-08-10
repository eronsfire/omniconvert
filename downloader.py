import os
import sys
import stat
import yt_dlp
from utils import obter_pasta_downloads

class VideoDownloader:
    def __init__(self, callback_status, callback_progress):
        self.mostrar_status = callback_status
        self.progress_hook = callback_progress

    def _obter_caminho_ffmpeg(self):
        """Localiza o FFmpeg e garante permissão de execução no Android."""
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        ffmpeg_bin = os.path.join(base_path, "assets", "ffmpeg", "ffmpeg")

        if os.path.exists(ffmpeg_bin):
            try:
                # Garante permissão total de leitura, escrita e execução (rwxr-xr-x)
                os.chmod(ffmpeg_bin, 0o755)
                return ffmpeg_bin
            except Exception as e:
                print(f"Erro ao aplicar chmod no FFmpeg: {e}")
                return ffmpeg_bin

        return None

    def baixar_midia(self, url: str, formato_escolhido: str, eh_social: bool = False):
        """Baixa mídias e realiza a conversão para MP3 ou junção de vídeo HD em MP4."""
        pasta_dest = obter_pasta_downloads()
        caminho_ffmpeg = self._obter_caminho_ffmpeg()

        ydl_opts = {
            'outtmpl': os.path.join(pasta_dest, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'nocheckcertificate': True,
            'quiet': True,
            'noprogress': True,
            'prefer_ffmpeg': True,  # Força o uso estrito do FFmpeg local
        }

        # Aponta explicitamente o executável e a pasta onde ele se encontra
        if caminho_ffmpeg:
            ydl_opts['ffmpeg_location'] = caminho_ffmpeg

        # --- SELEÇÃO DE FORMATOS ---
        if "bestaudio" in formato_escolhido or "ba" in formato_escolhido or formato_escolhido == "mp3":
            # Baixa o melhor áudio e converte para MP3 192kbps
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Baixa a melhor qualidade de vídeo + áudio e junta em MP4 (1080p, 2K, 4K)
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'

        # --- CABEÇALHOS E EXTRATORES ---
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