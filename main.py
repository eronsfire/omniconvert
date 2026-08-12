import threading
import flet as ft
from downloader import VideoDownloader
from updater import AppUpdater
from youtube_auth import YouTubeAuthenticator
from config import APP_VERSION

def main(page: ft.Page):
    page.title = f"Downloader Eronsfire v{APP_VERSION}"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = {"left": 15, "top": 40, "right": 15, "bottom": 10}

    # --- UI STATUS & PROGRESSO ---
    progresso_bar = ft.ProgressBar(value=0, visible=False, color=ft.Colors.BLUE_400)
    progresso_texto = ft.Text("", size=12, color=ft.Colors.GREY_400)
    txt_status = ft.Text(value="", size=13, selectable=True)

    container_status = ft.Container(
        content=ft.Column([
            progresso_bar,
            progresso_texto,
            txt_status
        ], spacing=5),
        padding={"left": 5, "top": 5, "right": 5, "bottom": 5},
        height=95,
        alignment=ft.Alignment(-1, -1)
    )

    def mostrar_status(texto, e_erro=False):
        txt_status.value = texto
        txt_status.color = ft.Colors.RED_400 if e_erro else ft.Colors.WHITE
        page.update()

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0) or 0

            porcentagem = (downloaded / total) if total > 0 else 0
            mb_total = total / (1024 * 1024)
            mb_speed = speed / (1024 * 1024)

            progresso_bar.visible = True
            progresso_bar.value = porcentagem
            progresso_texto.value = f"{porcentagem*100:.1f}% de {mb_total:.1f} MB ({mb_speed:.2f} MB/s)"
            
            try:
                progresso_bar.update()
                progresso_texto.update()
            except Exception:
                page.update()

        elif d['status'] == 'finished':
            progresso_bar.value = 1.0
            progresso_texto.value = "Download concluído! Processando arquivo..."
            txt_status.value = "Download finalizado! Salvo na pasta Downloads."
            txt_status.color = ft.Colors.GREEN_400
            try:
                progresso_bar.update()
                progresso_texto.update()
                txt_status.update()
            except Exception:
                page.update()

    # Instanciando os serviços
    downloader_service = VideoDownloader(mostrar_status, progress_hook)
    updater_service = AppUpdater(mostrar_status)
    auth_service = YouTubeAuthenticator(mostrar_status)

    # --- BOTÃO DE ATUALIZAÇÃO ---
    btn_atualizar = ft.IconButton(
        icon=ft.Icons.SYSTEM_UPDATE,
        tooltip="Buscar Atualização"
    )

    # --- STATUS DE AUTENTICAÇÃO ---
    status_auth = ft.Icon(
        ft.Icons.LOCK_OPEN,
        size=20,
        color=ft.Colors.ORANGE_400,
        tooltip="Não autenticado no YouTube"
    )
    
    def atualizar_status_auth():
        """Atualiza o ícone de status de autenticação."""
        if auth_service.verificar_cookies_validos():
            status_auth.name = ft.Icons.LOCK_CLOCK
            status_auth.color = ft.Colors.GREEN_400
            status_auth.tooltip = "Autenticado no YouTube ✓"
        else:
            status_auth.name = ft.Icons.LOCK_OPEN
            status_auth.color = ft.Colors.ORANGE_400
            status_auth.tooltip = "Não autenticado no YouTube"
        try:
            status_auth.update()
        except:
            pass

    # --- BOTÃO DE LOGIN ---
    btn_login = ft.IconButton(
        icon=ft.Icons.LOGIN,
        tooltip="Login YouTube"
    )
    
    def fazer_login_youtube(e=None):
        """Inicia o processo de login."""
        btn_login.disabled = True
        mostrar_status("Abrindo navegador para login...")
        page.update()
        
        def tarefa():
            try:
                # Tentar Chrome primeiro (mais estável)
                resultado = auth_service.fazer_login_youtube(usar_firefox=False)
                if resultado:
                    mostrar_status("Login realizado com sucesso! Seus cookies estão salvos.")
                    atualizar_status_auth()
                else:
                    mostrar_status("Falha no login. Verifique se você fez login no navegador.", e_erro=True)
            except Exception as err:
                mostrar_status(f"Erro ao fazer login: {err}", e_erro=True)
            finally:
                btn_login.disabled = False
                page.update()
        
        threading.Thread(target=tarefa, daemon=True).start()

    btn_login.on_click = fazer_login_youtube

    # --- EVENTOS ---
    def verificar_atualizacao(e=None):
        mostrar_status("Buscando atualizações...")
        btn_atualizar.disabled = True
        page.update()
        
        def progresso_apk(baixado, total_size):
            porcentagem = (baixado / total_size) if total_size > 0 else 0
            mb_total = total_size / (1024 * 1024)
            progresso_bar.visible = True
            progresso_bar.value = porcentagem
            progresso_texto.value = f"{porcentagem*100:.1f}% de {mb_total:.1f} MB"
            page.update()

        def tarefa():
            try:
                updater_service.checar_e_atualizar(progresso_apk)
            except Exception as err:
                mostrar_status(f"Erro na busca: {err}", e_erro=True)
            finally:
                progresso_bar.visible = False
                btn_atualizar.disabled = False
                page.update()

        threading.Thread(target=tarefa, daemon=True).start()

    btn_atualizar.on_click = verificar_atualizacao

    def mapear_formato(qualidade: str, eh_social: bool = False) -> str:
        if qualidade == "Apenas Áudio (MP3)":
            return "audio"

        # Formatos mais precisos para cada qualidade
        formatos = {
            "Melhor Qualidade (Máxima)": "best[ext=mp4]/best",
            "8K (7680p)": "best[height<=7680][ext=mp4]/best[height<=7680]/best",
            "4K (2160p)": "best[height<=2160][ext=mp4]/best[height<=2160]/best",
            "2K (1440p)": "best[height<=1440][ext=mp4]/best[height<=1440]/best",
            "Full HD (1080p)": "best[height<=1080][ext=mp4]/best[height<=1080]/best",
            "HD (720p)": "best[height<=720][ext=mp4]/best[height<=720]/best",
            "Standard (480p)": "best[height<=480][ext=mp4]/best[height<=480]/best",
            "Low (360p)": "best[height<=360][ext=mp4]/best[height<=360]/best",
            "Mínima (240p)": "best[height<=240][ext=mp4]/best[height<=240]/best",
            "Apenas Áudio (Melhor Qualidade)": "bestaudio/ba",
        }
        return formatos.get(qualidade, "best[ext=mp4]/best")

    def disparar_download(url: str, qualidade: str, eh_social: bool = False):
        if not url:
            mostrar_status("Informe uma URL válida.", e_erro=True)
            return

        fmt = mapear_formato(qualidade, eh_social)
        progresso_bar.visible = True
        progresso_bar.value = 0
        progresso_texto.value = "Iniciando download..."
        mostrar_status(f"Iniciando download ({qualidade})...")

        def tarefa():
            try:
                downloader_service.baixar_midia(url, fmt, eh_social)
            except Exception as err:
                mostrar_status(f"Erro no download: {err}", e_erro=True)
            finally:
                progresso_bar.visible = False
                page.update()

        threading.Thread(target=tarefa, daemon=True).start()

    # --- ABA YOUTUBE ---
    input_url_yt = ft.TextField(label="Cole a URL do vídeo do YouTube aqui", expand=True)
    dropdown_yt = ft.Dropdown(
        label="Qualidade / Formato",
        options=[
            ft.dropdown.Option("Melhor Qualidade (Máxima)"),
            ft.dropdown.Option("8K (7680p)"),
            ft.dropdown.Option("4K (2160p)"),
            ft.dropdown.Option("2K (1440p)"),
            ft.dropdown.Option("Full HD (1080p)"),
            ft.dropdown.Option("HD (720p)"),
            ft.dropdown.Option("Standard (480p)"),
            ft.dropdown.Option("Low (360p)"),
            ft.dropdown.Option("Mínima (240p)"),
            ft.dropdown.Option("Apenas Áudio (MP3)"),
            ft.dropdown.Option("Apenas Áudio (Melhor Qualidade)"),
        ],
        value="Melhor Qualidade (Máxima)"
    )

    conteudo_yt = ft.Column([
        ft.Text("Download do YouTube", size=18, weight=ft.FontWeight.BOLD),
        input_url_yt,
        dropdown_yt,
        ft.Button("Baixar YouTube", icon=ft.Icons.DOWNLOAD, 
                  on_click=lambda e: disparar_download(input_url_yt.value.strip(), dropdown_yt.value))
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    # --- ABA INSTAGRAM / TIKTOK ---
    input_url_social = ft.TextField(label="Link do Instagram ou TikTok", expand=True)
    dropdown_social = ft.Dropdown(
        label="Qualidade / Formato",
        options=[
            ft.dropdown.Option("Melhor Qualidade (Máxima)"),
            ft.dropdown.Option("8K (7680p)"),
            ft.dropdown.Option("4K (2160p)"),
            ft.dropdown.Option("2K (1440p)"),
            ft.dropdown.Option("Full HD (1080p)"),
            ft.dropdown.Option("HD (720p)"),
            ft.dropdown.Option("Standard (480p)"),
            ft.dropdown.Option("Low (360p)"),
            ft.dropdown.Option("Mínima (240p)"),
            ft.dropdown.Option("Apenas Áudio (MP3)"),
            ft.dropdown.Option("Apenas Áudio (Melhor Qualidade)"),
        ],
        value="Melhor Qualidade (Máxima)"
    )

    conteudo_social = ft.Column([
        ft.Text("Download Instagram & TikTok", size=18, weight=ft.FontWeight.BOLD),
        input_url_social,
        dropdown_social,
        ft.Button("Baixar Mídia", icon=ft.Icons.DOWNLOAD, 
                  on_click=lambda e: disparar_download(input_url_social.value.strip(), dropdown_social.value, True))
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    # --- TABS E ESTRUTURA ---
    tabs_control = ft.Tabs(
        length=2,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Row([
                    ft.TabBar(tabs=[
                        ft.Tab(label="YouTube", icon=ft.Icons.VIDEO_LIBRARY),
                        ft.Tab(label="Insta / TikTok", icon=ft.Icons.CAMERA_ALT),
                    ]),
                    ft.Row([
                        status_auth,
                        btn_login,
                        btn_atualizar,
                    ], spacing=5)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.TabBarView(
                    expand=True,
                    controls=[conteudo_yt, conteudo_social]
                )
            ]
        )
    )

    # --- RODAPÉ COM SELO DE AUTENTICIDADE ---
    rodape = ft.Row(
        controls=[
            ft.Icon(ft.Icons.VERIFIED_USER_OUTLINED, size=12, color=ft.Colors.BLUE_400),
            ft.Text(
                "2026© Willian Lima", 
                size=11, 
                color=ft.Colors.GREY_500, 
                weight=ft.FontWeight.W_500,
                italic=True
            )
        ],
        alignment=ft.MainAxisAlignment.END,
        spacing=4
    )

    page.add(
        ft.Column(
            controls=[
                ft.Container(content=tabs_control, expand=True),
                ft.Divider(height=1),
                container_status,
                rodape
            ],
            expand=True,
            spacing=3
        )
    )
    
    # Atualizar status de autenticação ao iniciar
    atualizar_status_auth()

if __name__ == "__main__":
    ft.run(main)