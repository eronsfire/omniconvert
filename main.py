import os
import threading
import requests
import urllib.request
import yt_dlp
import flet as ft

VERSION_ATUAL = "0.9"
REPO_GITHUB = "eronsfire/omniconvert"

def instalar_apk(caminho_apk):
    try:
        import subprocess
        cmd = [
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", f"file://{caminho_apk}",
            "-t", "application/vnd.android.package-archive"
        ]
        subprocess.run(cmd, check=True)
    except Exception:
        try:
            import importlib
            jnius = importlib.import_module("jnius")
            autoclass = jnius.autoclass

            Intent = autoclass('android.content.Intent')
            File = autoclass('java.io.File')
            Uri = autoclass('android.net.Uri')

            file = File(caminho_apk)
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.fromFile(file), "application/vnd.android.package-archive")
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PythonActivity.mActivity.startActivity(intent)
        except Exception:
            pass

def main(page: ft.Page):
    page.title = f"Conversor Eronsfire v{VERSION_ATUAL}"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = {"left": 15, "top": 40, "right": 15, "bottom": 20}

    # --- COMPONENTES DE PROGRESSO IGUAIS AO SEU CÓDIGO ANTIGO ---
    progresso_bar = ft.ProgressBar(value=0, visible=False, color=ft.Colors.BLUE_400)
    progresso_texto = ft.Text("", size=12, color=ft.Colors.GREY_400)
    txt_status = ft.Text(value="", size=13, selectable=True)

    # Contêiner do rodapé adicionando os componentes corretos
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

    def mostrar_status(texto, cor=ft.Colors.WHITE):
        txt_status.value = texto
        txt_status.color = cor
        page.update()

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0) or 0

            porcentagem = (downloaded / total) if total > 0 else 0
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            mb_speed = speed / (1024 * 1024)

            # Atualiza os componentes diretamente
            progresso_bar.visible = True
            progresso_bar.value = porcentagem
            progresso_texto.value = f"{porcentagem*100:.1f}% de {mb_total:.1f} MB ({mb_speed:.2f} MB/s)"
            
            # Força a renderização imediata na tela
            try:
                progresso_bar.update()
                progresso_texto.update()
            except Exception:
                page.update()

        elif d['status'] == 'finished':
            progresso_bar.value = 1.0
            progresso_texto.value = "Download concluído! Processando arquivo..."
            txt_status.value = "Download finalizado! Salvo em Downloads."
            txt_status.color = ft.Colors.GREEN_400
            try:
                progresso_bar.update()
                progresso_texto.update()
                txt_status.update()
            except Exception:
                page.update()

    def verificar_atualizacao(e=None):
        mostrar_status("Buscando atualizações...", ft.Colors.AMBER_400)
        try:
            url_api = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
            res = requests.get(url_api, timeout=5)

            if res.status_code == 200:
                dados = res.json()
                tag_versao = dados.get("tag_name", "").replace("v", "").strip()

                if tag_versao and tag_versao != VERSION_ATUAL:
                    apk_url = None
                    for asset in dados.get("assets", []):
                        if asset.get("name", "").endswith(".apk"):
                            apk_url = asset.get("browser_download_url")
                            break

                    if apk_url:
                        mostrar_status(f"Nova versão v{tag_versao} encontrada! Baixando...", ft.Colors.BLUE_400)
                        pasta_dest = "/sdcard/Download" if os.path.exists("/sdcard/Download") else "."
                        caminho_apk = os.path.join(pasta_dest, "Conversor Eronsfire.apk")
                        
                        def progresso_apk(count, block_size, total_size):
                            baixado = count * block_size
                            porcentagem = (baixado / total_size) if total_size > 0 else 0
                            mb_baixado = baixado / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            
                            progresso_bar.visible = True
                            progresso_bar.value = porcentagem
                            progresso_texto.value = f"{porcentagem*100:.1f}% de {mb_total:.1f} MB"
                            mostrar_status(f"Baixando Atualização v{tag_versao}...", ft.Colors.BLUE_400)

                        urllib.request.urlretrieve(apk_url, caminho_apk, reporthook=progresso_apk)
                        progresso_bar.visible = False
                        mostrar_status(f"Download da v{tag_versao} concluído!\nAbrindo instalador...", ft.Colors.GREEN_400)
                        instalar_apk(caminho_apk)
                    else:
                        mostrar_status(f"Versão v{tag_versao} encontrada, mas o APK não foi anexado.", ft.Colors.ORANGE_400)
                else:
                    mostrar_status(f"Você já está na versão mais recente (v{VERSION_ATUAL}).", ft.Colors.GREEN_400)
            else:
                mostrar_status("Nenhuma atualização/release encontrada no GitHub.", ft.Colors.WHITE)
        except Exception as err:
            mostrar_status(f"Erro ao verificar atualização: {str(err)}", ft.Colors.RED_400)

    # --- ABA 1: CONVERTER ARQUIVOS LOCAIS ---
    caminho_arquivo_selecionado = ""
    lbl_arquivo_selecionado = ft.Text("Nenhum arquivo selecionado.", italic=True, size=13)
    
    dd_formato_destino = ft.Dropdown(
        label="Formato de Destino",
        width=250,
        options=[
            ft.dropdown.Option("mp4", "MP4 (Vídeo)"),
            ft.dropdown.Option("mp3", "MP3 (Áudio)"),
            ft.dropdown.Option("m4a", "M4A (Áudio)"),
            ft.dropdown.Option("mkv", "MKV (Vídeo)"),
            ft.dropdown.Option("avi", "AVI (Vídeo)"),
            ft.dropdown.Option("wav", "WAV (Áudio)"),
        ],
        value="mp3"
    )

    def resultado_selecao_arquivo(e):
        nonlocal caminho_arquivo_selecionado
        if e.files and len(e.files) > 0:
            caminho_arquivo_selecionado = e.files[0].path
            lbl_arquivo_selecionado.value = f"Arquivo: {e.files[0].name}"
            mostrar_status("Arquivo selecionado com sucesso!", ft.Colors.GREEN_400)
        else:
            lbl_arquivo_selecionado.value = "Seleção cancelada."
            page.update()

    btn_selecionar_file = ft.ElevatedButton(
        "Selecionar Arquivo",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: page.pick_files(on_result=resultado_selecao_arquivo, allow_multiple=False)
    )

    def converter_arquivo(e):
        if not caminho_arquivo_selecionado or not os.path.exists(caminho_arquivo_selecionado):
            mostrar_status("Por favor, selecione um arquivo válido primeiro.", ft.Colors.RED_400)
            return

        fmt = dd_formato_destino.value
        mostrar_status(f"Iniciando conversão para .{fmt}...", ft.Colors.AMBER_400)
        
        def rodar_ffmpeg():
            try:
                import subprocess
                pasta_dest = "/sdcard/Download" if os.path.exists("/sdcard/Download") else os.path.dirname(caminho_arquivo_selecionado)
                nome_base = os.path.splitext(os.path.basename(caminho_arquivo_selecionado))[0]
                arquivo_saida = os.path.join(pasta_dest, f"{nome_base}_convertido.{fmt}")

                cmd = ["ffmpeg", "-y", "-i", caminho_arquivo_selecionado, arquivo_saida]
                subprocess.run(cmd, check=True)
                
                mostrar_status(f"Conversão concluída!\nSalvo em: {arquivo_saida}", ft.Colors.GREEN_400)
            except Exception as err:
                mostrar_status(f"Erro na conversão: {str(err)}", ft.Colors.RED_400)

        threading.Thread(target=rodar_ffmpeg, daemon=True).start()

    btn_executar_conversao = ft.ElevatedButton("Converter Agora", icon=ft.Icons.TRANSFORM, on_click=converter_arquivo)

    conteudo_converter = ft.Column([
        ft.Text("Conversor de Mídia Local", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("Escolha um arquivo do dispositivo e o formato desejado:"),
        ft.Row([btn_selecionar_file, lbl_arquivo_selecionado], alignment=ft.MainAxisAlignment.START),
        dd_formato_destino,
        btn_executar_conversao
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    # --- ABA 2: YOUTUBE DOWNLOADER ---
    input_url = ft.TextField(label="Cole a URL do vídeo do YouTube aqui", expand=True)
    dropdown_qualidade = ft.Dropdown(
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

    def executar_download_yt(e):
        url = input_url.value.strip()
        if not url:
            mostrar_status("Informe uma URL do YouTube válida.", ft.Colors.RED_400)
            return

        qualidade = dropdown_qualidade.value
        formatos = {
            "Melhor Qualidade (Máxima)": "best",
            "2160p (4K)": "best[height<=2160]",
            "1440p (2K)": "best[height<=1440]",
            "1080p (Full HD)": "best[height<=1080]",
            "720p (HD)": "best[height<=720]",
            "480p (SD)": "best[height<=480]",
            "360p (Baixa)": "best[height<=360]",
            "Apenas Áudio (MP3)": "bestaudio/best",
        }

        formato_escolhido = formatos.get(qualidade, "best")
        pasta_dest = "/sdcard/Download" if os.path.exists("/sdcard/Download") else "."

        progresso_bar.visible = True
        progresso_bar.value = 0
        progresso_texto.value = "Iniciando download..."
        mostrar_status(f"Iniciando download ({qualidade})...", ft.Colors.AMBER_400)

        def tarefa_download():
            ydl_opts = {
                'format': formato_escolhido,
                'outtmpl': os.path.join(pasta_dest, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True,
                'quiet': True,
                'noprogress': True,
                # 1. Simula os apps mobile (evita bloqueio sem precisar de conta)
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'ios']
                    }
                }
            }

            # 2. Se estiver rodando no PC/VS Code, puxa os cookies do navegador se necessário
            try:
                ydl_opts['cookiesfrombrowser'] = ('chrome',) # ou 'firefox', 'edge'
            except Exception:
                pass

        threading.Thread(target=tarefa_download, daemon=True).start()

    btn_baixar_yt = ft.ElevatedButton("Baixar YouTube", icon=ft.Icons.DOWNLOAD, on_click=executar_download_yt)

    conteudo_yt = ft.Column([
        ft.Text("Download do YouTube", size=18, weight=ft.FontWeight.BOLD),
        input_url,
        dropdown_qualidade,
        btn_baixar_yt
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    # --- ABA 3: INSTAGRAM / TIKTOK DOWNLOADER ---
    txt_url_social = ft.TextField(label="Link do Instagram ou TikTok", expand=True)
    dropdown_qualidade_social = ft.Dropdown(
        label="Qualidade / Formato",
        options=[
            ft.dropdown.Option("Melhor Qualidade (Máxima)"),
            ft.dropdown.Option("1080p (Full HD)"),
            ft.dropdown.Option("720p (HD)"),
            ft.dropdown.Option("Apenas Áudio"),
        ],
        value="Melhor Qualidade (Máxima)"
    )

    def executar_download_social(e):
        url = txt_url_social.value.strip()
        if not url:
            mostrar_status("Informe um link do Instagram ou TikTok válido.", ft.Colors.RED_400)
            return

        qualidade = dropdown_qualidade_social.value
        formatos = {
            "Melhor Qualidade (Máxima)": "best",
            "1080p (Full HD)": "best[height<=1080]",
            "720p (HD)": "best[height<=720]",
            "Apenas Áudio": "bestaudio/best",
        }
        
        formato_escolhido = formatos.get(qualidade, "best")
        pasta_dest = "/sdcard/Download" if os.path.exists("/sdcard/Download") else "."

        progresso_bar.visible = True
        progresso_bar.value = 0
        progresso_texto.value = "Iniciando download..."
        mostrar_status("Iniciando download...", ft.Colors.AMBER_400)

        def tarefa_download_social():
            ydl_opts = {
                'format': formato_escolhido,
                'outtmpl': os.path.join(pasta_dest, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as err:
                mostrar_status(f"Erro ao baixar mídia: {str(err)}", ft.Colors.RED_400)
            finally:
                progresso_bar.visible = False
                page.update()

        threading.Thread(target=tarefa_download_social, daemon=True).start()

    btn_baixar_social = ft.ElevatedButton("Baixar Mídia", icon=ft.Icons.DOWNLOAD, on_click=executar_download_social)

    conteudo_social = ft.Column([
        ft.Text("Download Instagram & TikTok", size=18, weight=ft.FontWeight.BOLD),
        txt_url_social,
        dropdown_qualidade_social,
        btn_baixar_social
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    # --- NAVEGAÇÃO DE ABAS ---
    btn_atualizar = ft.IconButton(
        icon=ft.Icons.SYSTEM_UPDATE,
        tooltip="Buscar Atualização",
        on_click=verificar_atualizacao
    )

    tabs_control = ft.Tabs(
        length=3,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.Row(
                    [
                        ft.TabBar(
                            tabs=[
                                ft.Tab(label="Converter", icon=ft.Icons.TRANSFORM),
                                ft.Tab(label="YouTube", icon=ft.Icons.VIDEO_LIBRARY),
                                ft.Tab(label="Insta / TikTok", icon=ft.Icons.CAMERA_ALT),
                            ]
                        ),
                        btn_atualizar,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        conteudo_converter,
                        conteudo_yt,
                        conteudo_social,
                    ]
                )
            ]
        )
    )

    # Layout Principal
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