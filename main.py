import threading
import flet as ft
from downloader import VideoDownloader
from updater import AppUpdater, VERSION_ATUAL

def main(page: ft.Page):
    page.title = f"Downloader Eronsfire v{VERSION_ATUAL}"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = {"left": 15, "top": 40, "right": 15, "bottom": 20}

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
        padding={"left": 5, "top": 5, "right": 5, "bottom": 10},
        height=105,
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

    # Instanciando os serviços separados
    downloader_service = VideoDownloader(mostrar_status, progress_hook)
    updater_service = AppUpdater(mostrar_status)

    # --- EVENTOS ---
    def verificar_atualizacao(e=None):
        mostrar_status("Buscando atualizações...")
        
        def progresso_apk(baixado, total_size):
            porcentagem = (baixado / total_size) if total_size > 0 else 0
            mb_total = total_size / (1024 * 1024)
            progresso_bar.visible = True
            progresso_bar.value = porcentagem
            progresso_texto.value = f"{porcentagem*100:.1f}% de {mb_total:.1f} MB"
            page.update()

        def tarefa():
            updater_service.checar_atualizacao(progresso_apk)
            progresso_bar.visible = False
            page.update()

        threading.Thread(target=tarefa, daemon=True).start()

    def mapear_formato(qualidade: str, eh_social: bool = False) -> str:
        formatos = {
            "Melhor Qualidade (Máxima)": "best",
            "2160p (4K)": "best[height<=2160]",
            "1440p (2K)": "best[height<=1440]",
            "1080p (Full HD)": "best[height<=1080]",
            "720p (HD)": "best[height<=720]",
            "480p (SD)": "best[height<=480]",
            "360p (Baixa)": "best[height<=360]",
            "Apenas Áudio (MP3)": "ba[ext=m4a]/ba[ext=mp3]/ba/best" if eh_social else "bestaudio/best",
        }
        return formatos.get(qualidade, "best")

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
            downloader_service.baixar_midia(url, fmt, eh_social)
            progresso_bar.visible = False
            page.update()

        threading.Thread(target=tarefa, daemon=True).start()

    # --- ABA YOUTUBE ---
    input_url_yt = ft.TextField(label="Cole a URL do vídeo do YouTube aqui", expand=True)
    dropdown_yt = ft.Dropdown(
        label="Qualidade / Formato",
        options=[
            ft.dropdown.Option("Melhor Qualidade (Máxima)"),
            ft.dropdown.Option("2160p (4K)"),
            ft.dropdown.Option("1440p (2K)"),
            ft.dropdown.Option("1080p (Full HD)"),
            ft.dropdown.Option("720p (HD)"),
            ft.dropdown.Option("480p (SD)"),
            ft.dropdown.Option("360p (Baixa)"),
            ft.dropdown.Option("Apenas Áudio (MP3)"),
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
            ft.dropdown.Option("2160p (4K)"),
            ft.dropdown.Option("1440p (2K)"),
            ft.dropdown.Option("1080p (Full HD)"),
            ft.dropdown.Option("720p (HD)"),
            ft.dropdown.Option("480p (SD)"),
            ft.dropdown.Option("360p (Baixa)"),
            ft.dropdown.Option("Apenas Áudio (MP3)"),
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
    btn_atualizar = ft.IconButton(
        icon=ft.Icons.SYSTEM_UPDATE,
        tooltip="Buscar Atualização",
        on_click=verificar_atualizacao
    )

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
                    btn_atualizar,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.TabBarView(
                    expand=True,
                    controls=[conteudo_yt, conteudo_social]
                )
            ]
        )
    )

    page.add(
        ft.Column(
            controls=[
                ft.Container(content=tabs_control, expand=True),
                ft.Divider(height=1),
                container_status
            ],
            expand=True,
            spacing=5
        )
    )

if __name__ == "__main__":
    ft.run(main)