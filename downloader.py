import os
import random
import yt_dlp
from utils import obter_pasta_downloads, obter_pasta_dados, esta_no_android

class VideoDownloader:
    def __init__(self, callback_status, callback_progress):
        self.mostrar_status = callback_status
        self.progress_hook = callback_progress
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]

    def _avaliar_cookies(self, caminho: str) -> dict:
        """Verifica se o arquivo de cookies existe e contém marcadores de login reais."""
        resultado = {"existe": False, "valido": False, "marcadores": []}
        if not os.path.exists(caminho):
            return resultado
        resultado["existe"] = True
        try:
            from youtube_auth import YouTubeAuthenticator
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                info = YouTubeAuthenticator.analisar_cookies_netscape(f.read())
            resultado["marcadores"] = info["marcadores"]
            resultado["valido"] = len(info["marcadores"]) > 0
        except Exception:
            resultado["valido"] = False
        return resultado

    def verificar_ffmpeg(self) -> bool:
        """Verifica se FFmpeg está disponível no sistema."""
        import shutil
        return shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None

    def baixar_midia(self, url: str, formato_escolhido: str, eh_social: bool = False):
        pasta_dest = obter_pasta_downloads()

        # Local onde os cookies capturados são salvos (diretório gravável do app)
        caminho_cookie = os.path.join(obter_pasta_dados(), "youtube_cookies.txt")

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
        cookie_info = self._avaliar_cookies(caminho_cookie)
        if cookie_info["existe"]:
            if cookie_info["valido"]:
                print(f"[DEBUG] Login válido detectado ({', '.join(cookie_info['marcadores'])}). Usando cookies salvos: {caminho_cookie}")
                self.mostrar_status(f"Usando seu login do YouTube ({', '.join(cookie_info['marcadores'])}).")
            else:
                print(f"[WARN] Arquivo de cookies SEM marcadores de login: {caminho_cookie}")
                self.mostrar_status(
                    "Atenção: suas cookies parecem expirados/inválidos (sem marcador de login). "
                    "Se o download for bloqueado, reimporte o cookies.txt no botão de upload.",
                    e_erro=True,
                )
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
        eh_android = esta_no_android()
        tem_ffmpeg = self.verificar_ffmpeg()

        if formato_escolhido == "audio":
            # "Apenas Áudio (MP3)" - Converte com FFmpeg se disponível
            if eh_android or not tem_ffmpeg:
                print("[INFO] Ambiente Android ou FFmpeg não disponível. Baixando áudio direto sem conversão.")
                self.mostrar_status("Baixando melhor áudio disponível (sem conversão)...")
                ydl_opts['format'] = 'bestaudio/ba'
                # Não adiciona postprocessor se não tem FFmpeg
            else:
                # PC com FFmpeg - converte para MP3
                print("[INFO] FFmpeg disponível. Convertendo para MP3...")
                self.mostrar_status("Convertendo para MP3...")
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
            self.mostrar_status("Baixando melhor áudio (formato nativo)...")
            ydl_opts['format'] = 'bestaudio/ba'
        else:
            # Vídeos em diferentes qualidades
            ydl_opts['format'] = formato_escolhido

        # --- TENTATIVAS COM CLIENTES DE EXTRAÇÃO ---
        # O YouTube muda o anti-bot com frequência. Se o cliente padrão for
        # recusado (bot/403/429/PO token), tenta os outros na ordem.
        if eh_android:
            clientes = ["android_vr", None, "web_safari"]
        else:
            clientes = [None, "web_safari", "android_vr"]

        ultimo_erro = None
        baixou = False
        for cliente in clientes:
            opts = dict(ydl_opts)
            if cliente:
                extrator = dict(opts.get('extractor_args') or {})
                youtube = dict(extrator.get('youtube') or {})
                youtube['player_client'] = [cliente]
                extrator['youtube'] = youtube
                opts['extractor_args'] = extrator
                nome_cliente = cliente
            else:
                nome_cliente = "padrão do yt-dlp"

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                baixou = True

                # Mensagem de sucesso
                if formato_escolhido == "audio":
                    if eh_android or not tem_ffmpeg:
                        self.mostrar_status(
                            "Download do áudio concluído! (Formato nativo do YouTube)",
                            eh_erro=False
                        )
                    else:
                        self.mostrar_status(
                            "Download e conversão para MP3 concluído!",
                            eh_erro=False
                        )
                elif formato_escolhido == "bestaudio/ba":
                    self.mostrar_status(
                        "Download do áudio concluído! (Formato nativo)",
                        eh_erro=False
                    )
                break
            except yt_dlp.utils.DownloadError as err:
                ultimo_erro = err
                msg = str(err).lower()
                if any(x in msg for x in ("bot", "sign in", "403", "forbidden", "429", "too many", "po token")):
                    print(f"[WARN] Cliente '{nome_cliente}' recusado pelo YouTube: {err}")
                    self.mostrar_status(f"YouTube recusou (cliente {nome_cliente}); tentando outro cliente...")
                    continue
                raise

        if not baixou:
            err = ultimo_erro
            try:
                raise err if err else RuntimeError("Falha sem detalhes")
            except yt_dlp.utils.DownloadError as e:
                if "bot" in str(e).lower() or "403" in str(e) or "sign in" in str(e).lower():
                    self.mostrar_status(
                        "YouTube bloqueou como suspeita de bot em todos os clientes. "
                        "Toque no ícone de login/upload e importe um cookies.txt exportado do seu login.",
                        True,
                    )
                else:
                    self.mostrar_status(f"Erro ao baixar mídia: {str(e)}", True)
            except Exception as e:
                self.mostrar_status(f"Erro ao baixar mídia: {str(e)}", True)
