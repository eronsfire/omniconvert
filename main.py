import threading
import flet as ft
from downloader import VideoDownloader
from updater import AppUpdater
from youtube_auth import YouTubeAuthenticator
from config import APP_VERSION
from utils import mapear_formato, versao_menor

# Lock para serializar atualizações de UI vindas das threads de trabalho
# (o Flet não é thread-safe para `page.update()` chamado direto de threads)
ui_lock = threading.Lock()

def main(page: ft.Page):
    page.title = f"Conversor Eronsfire v{APP_VERSION}"
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
        with ui_lock:
            try:
                page.update()
            except Exception:
                pass

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
            
            with ui_lock:
                try:
                    progresso_bar.update()
                    progresso_texto.update()
                except Exception:
                    try:
                        page.update()
                    except Exception:
                        pass

        elif d['status'] == 'finished':
            progresso_bar.value = 1.0
            progresso_texto.value = "Download concluído! Processando arquivo..."
            txt_status.value = "Download finalizado! Salvo na pasta Downloads."
            txt_status.color = ft.Colors.GREEN_400
            with ui_lock:
                try:
                    progresso_bar.update()
                    progresso_texto.update()
                    txt_status.update()
                except Exception:
                    try:
                        page.update()
                    except Exception:
                        pass

    # Instanciando os serviços
    downloader_service = VideoDownloader(mostrar_status, progress_hook)
    updater_service = AppUpdater(mostrar_status)
    auth_service = YouTubeAuthenticator(mostrar_status)

    # Seletor de arquivos (importar cookies.txt)
    file_picker = ft.FilePicker()

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
        """Atualiza o ícone de status de autenticação (com base nos cookies reais)."""
        if auth_service.verificar_cookies_validos():
            status_auth.name = ft.Icons.LOCK
            status_auth.color = ft.Colors.GREEN_400
            status_auth.tooltip = "Autenticado no YouTube ✓"
        else:
            status_auth.name = ft.Icons.LOCK_OPEN
            status_auth.color = ft.Colors.ORANGE_400
            status_auth.tooltip = "Não autenticado no YouTube"
        try:
            status_auth.update()
        except Exception:
            pass

    # --- BOTÃO DE LOGIN ---
    btn_login = ft.IconButton(
        icon=ft.Icons.LOGIN,
        tooltip="Login YouTube (abre o navegador e captura os cookies)"
    )

    def fazer_login_youtube(e=None):
        """Inicia o processo de login."""
        btn_login.disabled = True
        page.update()
        
        def tarefa():
            try:
                resultado = auth_service.fazer_login_youtube(usar_firefox=False)
                if resultado:
                    atualizar_status_auth()
            except Exception as err:
                mostrar_status(f"Erro ao fazer login: {err}", e_erro=True)
            finally:
                btn_login.disabled = False
                page.update()
        
        threading.Thread(target=tarefa, daemon=True).start()

    btn_login.on_click = fazer_login_youtube

    # --- BOTÃO DE IMPORTAR COOKIES (funciona em qualquer aparelho) ---
    btn_importar_cookies = ft.IconButton(
        icon=ft.Icons.UPLOAD_FILE,
        tooltip="Importar cookies.txt do YouTube (exportado do navegador)"
    )

    def importar_cookies(e=None):
        """Abre o seletor de arquivos e importa o cookies.txt validando o conteúdo."""
        async def _importar():
            try:
                mostrar_status("Selecione o cookies.txt exportado do YouTube...")
                files = await file_picker.pick_files(
                    dialog_title="Selecione o cookies.txt do YouTube",
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["txt"],
                    with_data=True,
                )
            except Exception as err:
                mostrar_status(f"Erro ao abrir o seletor de arquivos: {err}", True)
                return

            if not files:
                mostrar_status("Importação cancelada (nenhum arquivo selecionado).")
                return

            selecionado = files[0]
            dados = selecionado.bytes
            if dados is None and selecionado.path:
                try:
                    with open(selecionado.path, "rb") as f:
                        dados = f.read()
                except Exception as err:
                    mostrar_status(f"Não foi possível ler o arquivo: {err}", True)
                    return

            if not dados:
                mostrar_status("O arquivo está vazio.", True)
                return

            ok, mensagem = auth_service.importar_cookies(dados)
            mostrar_status(mensagem, not ok)
            atualizar_status_auth()

        page.run_task(_importar)

    btn_importar_cookies.on_click = importar_cookies

    # --- BOTÃO DE AJUDA (passo a passo do login) ---
    btn_ajuda_cookies = ft.IconButton(
        icon=ft.Icons.HELP_OUTLINE,
        tooltip="Como importar o cookies.txt?"
    )

    def mostrar_ajuda_cookies(e=None):
        dialog = ft.AlertDialog(
            title=ft.Text("Login do YouTube"),
            content=ft.Column([
                ft.Text("O YouTube bloqueia downloads com 'suspeita de robô'. Para desbloquear:", size=13),
                ft.Text("1. No Chrome ou Firefox, instale a extensão 'Get cookies.txt LOCALLY'.", size=12),
                ft.Text("2. Abra o YouTube já logado e exporte o arquivo cookies.txt (botão Export da extensão).", size=12),
                ft.Text("3. Toque no botão de upload (ao lado do login) e selecione o cookies.txt.", size=12),
                ft.Text("4. Pronto: o app passa a usar seus cookies de login.", size=12),
                ft.Divider(height=1),
                ft.Text("No PC, o botão de login também funciona sozinho: abre o navegador e captura os cookies automaticamente.", size=12),
                ft.Text("Seus cookies ficam só no aparelho e são usados apenas pelo yt-dlp. Se o login expirar, exporte e importe de novo.", size=11, color=ft.Colors.GREY_500),
            ], spacing=8, tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Entendi", on_click=lambda _: page.pop_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    btn_ajuda_cookies.on_click = mostrar_ajuda_cookies

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

    def disparar_download(url: str, qualidade: str, eh_social: bool = False):
        if not url:
            mostrar_status("Informe uma URL válida.", e_erro=True)
            return

        fmt = mapear_formato(qualidade, downloader_service.verificar_ffmpeg())
        progresso_bar.visible = True
        progresso_bar.value = 0
        progresso_texto.value = "Iniciando download..."
        mostrar_status(f"Iniciando download ({qualidade})...")

        def tarefa():
            try:
                downloader_service.baixar_midia(url, fmt, eh_social)
            except Exception as err:
                msg_err = str(err).lower()
                if "ffmpeg" in msg_err or "postprocessor" in msg_err:
                    mostrar_status("Erro de processamento (FFmpeg ausente/desatualizado). Tente novamente sem conversão.", e_erro=True)
                else:
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
            ft.dropdown.Option("Apenas Áudio (MP3 no PC)"),
            ft.dropdown.Option("Apenas Áudio (Melhor Qualidade)"),
        ],
        value="Melhor Qualidade (Máxima)"
    )

    conteudo_yt = ft.Column([
        ft.Text("Download do YouTube", size=18, weight=ft.FontWeight.BOLD),
        input_url_yt,
        dropdown_yt,
        ft.Text(
            "Bloqueio 'suspeita de bot'? Faça login (botão de login acima) ou importe o cookies.txt (botão de upload). Toque no (?) para ver como.",
            size=11,
            color=ft.Colors.GREY_500,
        ),
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
            ft.dropdown.Option("Apenas Áudio (MP3 no PC)"),
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
                        btn_importar_cookies,
                        btn_ajuda_cookies,
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

    # Verifica em segundo plano se o yt-dlp está desatualizado
    # (o YouTube muda o anti-bot com frequência; manter o yt-dlp atual evita o bloqueio de bot)
    def verificar_yt_dlp_atualizado():
        try:
            import yt_dlp
            import requests
            atual = yt_dlp.version.__version__
            r = requests.get("https://pypi.org/pypi/yt-dlp/json", timeout=6)
            if r.status_code != 200:
                return
            recente = r.json().get("info", {}).get("version", "")
            if recente and versao_menor(atual, recente):
                mostrar_status(
                    f"Aviso: yt-dlp desatualizado ({atual} -> {recente}). "
                    "Atualize para evitar o bloqueio de suspeita de bot.",
                    e_erro=True,
                )
        except Exception:
            pass

    threading.Thread(target=verificar_yt_dlp_atualizado, daemon=True).start()

if __name__ == "__main__":
    ft.run(main)
