import os
import time
import random
import yt_dlp
from utils import obter_pasta_downloads

class VideoDownloader:
    def __init__(self, callback_status, callback_progress):
        self.mostrar_status = callback_status
        self.progress_hook = callback_progress
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]

    def verificar_ffmpeg(self) -> bool:
        """Verifica se FFmpeg está disponível no sistema."""
        import shutil
        return shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None

    def esta_no_android(self) -> bool:
        """Detecta se está rodando no Android."""
        return 'ANDROID_STORAGE' in os.environ or 'ANDROID_ARGUMENT' in os.environ

    def baixar_midia(self, url: str, formato_escolhido: str, eh_social: bool = False):
        pasta_dest = obter_pasta_downloads()
        
        # Local onde os cookies capturados são salvos
        pasta_app = os.path.dirname(os.path.abspath(__file__))
        caminho_cookie = os.path.join(pasta_app, "youtube_cookies.txt")

        ydl_opts = {
            'outtmpl': os.path.join(pasta_dest, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'quiet': False,
            'noprogress': True,
            'concurrent_fragment_downloads': 4,
            'nocheckcertificate': True,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
            'http_headers': {
                'User-Agent': random.choice(self.user_agents),
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            },
        }

        # Se o arquivo de cookies existir, ativa a autenticação
        if os.path.exists(caminho_cookie):
            print(f"[DEBUG] Usando cookies salvos: {caminho_cookie}")
            ydl_opts['cookiefile'] = caminho_cookie
            ydl_opts['extract_flat'] = False
        else:
            print("[DEBUG] Nenhum cookie encontrado. Tentando acesso público.")
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'skip_unavailable_streams': True
                }
            }

        # --- SELEÇÃO DE FORMATOS ---
        eh_android = self.esta_no_android()
        tem_ffmpeg = self.verificar_ffmpeg()

        if formato_escolhido == "audio":
            # "Apenas Áudio (MP3)" - Converte com FFmpeg se disponível
            if eh_android or not tem_ffmpeg:
                print("[INFO] Ambiente Android ou FFmpeg não disponível. Baixando áudio direto sem conversão.")
                self.mostrar_status("📱 Baixando melhor áudio disponível (sem conversão)...")
                ydl_opts['format'] = 'bestaudio/ba'
                # Não adiciona postprocessor se não tem FFmpeg
            else:
                # PC com FFmpeg - converte para MP3
                print("[INFO] FFmpeg disponível. Convertendo para MP3...")
                self.mostrar_status("🎵 Convertendo para MP3...")
                ydl_opts['format'] = 'bestaudio/ba'
                # Garante que vai usar FFmpeg para converter
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                # Prevent fallback to other formats
                ydl_opts['keepvideo'] = False
        elif formato_escolhido == "bestaudio/ba":
            # "Apenas Áudio (Melhor Qualidade)" - Áudio sem conversão
            print("[INFO] Baixando melhor áudio disponível (formato nativo)...")
            self.mostrar_status("🎵 Baixando melhor áudio (formato nativo)...")
            ydl_opts['format'] = 'bestaudio/ba'
        else:
            # Vídeos em diferentes qualidades
            ydl_opts['format'] = formato_escolhido

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
                # Mensagem de sucesso
                if formato_escolhido == "audio":
                    if eh_android or not tem_ffmpeg:
                        self.mostrar_status(
                            "✓ Download do áudio concluído! (Formato nativo do YouTube)",
                            eh_erro=False
                        )
                    else:
                        self.mostrar_status(
                            "✓ Download e conversão para MP3 concluído!",
                            eh_erro=False
                        )
                elif formato_escolhido == "bestaudio/ba":
                    self.mostrar_status(
                        "✓ Download do áudio concluído! (Formato nativo)",
                        eh_erro=False
                    )
                
        except yt_dlp.utils.DownloadError as err:
            if "Sign in to confirm you're not a bot" in str(err) or "bot" in str(err).lower():
                self.mostrar_status(
                    "❌ YouTube bloqueou como suspeita de bot. Faça login pela opção 'Login YouTube' no app.",
                    True
                )
            else:
                self.mostrar_status(f"Erro ao baixar mídia: {str(err)}", True)
        except Exception as err:
            erro_msg = str(err)
            # Detectar erros específicos de FFmpeg
            if "ffmpeg" in erro_msg.lower() or "postprocessor" in erro_msg.lower():
                self.mostrar_status(
                    "⚠️ Erro de processamento (FFmpeg não disponível). Tente novamente sem conversão.",
                    True
                )
            else:
                self.mostrar_status(f"Erro ao baixar mídia: {erro_msg}", True)