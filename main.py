import os
import urllib.request
import threading
import requests
import flet as ft
from PIL import Image
from pdf2image import convert_from_path
import yt_dlp

VERSION_ATUAL = "0.8"
REPO_GITHUB = "eronsfire/omniconvert"  # Seu usuário/repositório


def main(page: ft.Page):
    page.title = f"Conversor Eronsfire v{VERSION_ATUAL}"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    txt_status = ft.Text(value="", size=14, selectable=True)

    def mostrar_status(mensagem, cor):
        txt_status.value = mensagem
        txt_status.color = cor
        page.update()

    # ==========================================
    # LÓGICA DE VERIFICAÇÃO DE ATUALIZAÇÕES
    # ==========================================
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
                        mostrar_status(f"Nova versão v{tag_versao} encontrada! Baixando APK...", ft.Colors.BLUE_400)
                        
                        pasta_dest = "/sdcard/Download" if os.path.exists("/sdcard/Download") else "."
                        caminho_apk = os.path.join(pasta_dest, "Conversor Eronsfire.apk")
                        
                        urllib.request.urlretrieve(apk_url, caminho_apk)
                        mostrar_status(f"APK v{tag_versao} baixado com sucesso em:\n{caminho_apk}\nAbra o arquivo para instalar!", ft.Colors.GREEN_400)
                    else:
                        mostrar_status(f"Versão v{tag_versao} encontrada, mas o APK não foi anexado.", ft.Colors.ORANGE_400)
                else:
                    mostrar_status(f"Você já está na versão mais recente (v{VERSION_ATUAL}).", ft.Colors.GREEN_400)
            else:
                mostrar_status("Nenhuma atualização/release encontrada no GitHub.", ft.Colors.WHITE)
        except Exception as err:
            mostrar_status(f"Erro ao verificar atualização: {str(err)}", ft.Colors.RED_400)

    # ==========================================
    # LÓGICA DE CONVERSÃO DE ARQUIVOS
    # ==========================================
    def converter_arquivo(caminho_origem, formato_destino):
        if not caminho_origem or not os.path.exists(caminho_origem):
            raise FileNotFoundError("Selecione um arquivo válido.")

        extensao = os.path.splitext(caminho_origem)[1].lower().replace(".", "")
        fmt_dest = formato_destino.lower()

        if extensao == "pdf" and fmt_dest in ["jpg", "png", "webp"]:
            imagens = convert_from_path(caminho_origem)
            if not imagens:
                raise Exception("Não foi possível processar o PDF.")

            caminho_saida = os.path.splitext(caminho_origem)[0] + f".{fmt_dest}"
            imagens[0].save(caminho_saida, fmt_dest.upper())
            return caminho_saida

        elif extensao in ["png", "jpg", "jpeg", "webp"] and fmt_dest in ["png", "jpg", "jpeg", "webp"]:
            caminho_saida = os.path.splitext(caminho_origem)[0] + f".{fmt_dest}"
            with Image.open(caminho_origem) as img:
                img.convert("RGB").save(caminho_saida)
            return caminho_saida

        else:
            raise ValueError(f"Não é possível converter de .{extensao} para .{fmt_dest}")

    # ==========================================
    # INTERFACE DO USUÁRIO & COMPONENTES
    # ==========================================

    async def selecionar_arquivo(e):
        resultado = await page.pick_files_async(allow_multiple=False)
        if resultado and resultado.files:
            input_caminho.value = resultado.files[0].path
            page.update()

    # ABA 1: CONVERSOR DE ARQUIVOS
    input_caminho = ft.TextField(label="Arquivo selecionado", read_only=True, expand=True)
    
    btn_procurar = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=selecionar_arquivo
    )

    dropdown_fmt = ft.Dropdown(
        label="Formato Final",
        options=[
            ft.dropdown.Option("jpg"),
            ft.dropdown.Option("png"),
            ft.dropdown.Option("webp"),
        ],
        value="jpg"
    )

    def ao_clicar_converter(e):
        try:
            mostrar_status("Processando arquivo...", ft.Colors.AMBER_400)
            saida = converter_arquivo(input_caminho.value, dropdown_fmt.value)
            mostrar_status(f"Concluído!\nSalvo em: {saida}", ft.Colors.GREEN_400)
        except Exception as err:
            mostrar_status(f"Erro: {str(err)}", ft.Colors.RED_400)

    aba_conversor = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("Conversor de Arquivos", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([input_caminho, btn_procurar]),
            dropdown_fmt,
            ft.Button(
                "CONVERTER",
                icon=ft.Icons.TRANSFORM,
                on_click=ao_clicar_converter,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                width=400,
                height=45
            )
        ], spacing=15)
    )

    # ABA 2: DOWNLOADER DO YOUTUBE
    input_url = ft.TextField(label="Cole a URL do vídeo do YouTube aqui")
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

    progresso_bar = ft.ProgressBar(width=400, value=0, visible=False)
    progresso_texto = ft.Text("", size=12, color=ft.Colors.GREY_400)
    
    btn_baixar = ft.Button(
        "BAIXAR VÍDEO",
        icon=ft.Icons.DOWNLOAD,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        width=400,
        height=45
    )

    def ao_clicar_baixar(e):
        url = input_url.value.strip()
        qualidade = dropdown_qualidade.value

        if not url:
            mostrar_status("Cole uma URL do YouTube válida.", ft.Colors.RED_400)
            return

        # Bloqueia o botão e ativa barras
        btn_baixar.disabled = True
        progresso_bar.visible = True
        progresso_bar.value = 0
        progresso_texto.value = "Iniciando..."
        mostrar_status("Iniciando download da mídia...", ft.Colors.AMBER_400)
        page.update()

        def rodar_download():
            try:
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

                pasta_download = "/sdcard/Download" if os.path.exists("/sdcard/Download") else "."

                def progress_hook(d):
                    if d['status'] == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        downloaded = d.get('downloaded_bytes', 0)
                        speed = d.get('speed', 0) or 0

                        porcentagem = (downloaded / total) if total > 0 else 0
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        mb_speed = speed / (1024 * 1024)

                        progresso_bar.value = porcentagem
                        progresso_texto.value = f"{porcentagem * 100:.1f}% de {mb_total:.1f} MB ({mb_speed:.2f} MB/s)"
                        page.update()

                    elif d['status'] == 'finished':
                        progresso_bar.value = 1.0
                        progresso_texto.value = "Finalizando e salvando arquivo..."
                        page.update()

                ydl_opts = {
                    "format": formatos.get(qualidade, "best"),
                    "outtmpl": os.path.join(pasta_download, "%(title)s.%(ext)s"),
                    "progress_hooks": [progress_hook],
                    "quiet": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                mostrar_status("Download finalizado! Salvo na pasta Downloads.", ft.Colors.GREEN_400)

            except Exception as err:
                mostrar_status(f"Erro no download: {str(err)}", ft.Colors.RED_400)
            finally:
                btn_baixar.disabled = False
                progresso_bar.visible = False
                page.update()

        # Executa em thread paralela para a UI não travar
        threading.Thread(target=rodar_download, daemon=True).start()

    btn_baixar.on_click = ao_clicar_baixar

    aba_downloader = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Text("YouTube Downloader", size=18, weight=ft.FontWeight.BOLD),
            input_url,
            dropdown_qualidade,
            btn_baixar,
            progresso_bar,
            progresso_texto,
        ], spacing=15)
    )

    # NAVEGAÇÃO E ATUALIZAÇÕES
    conteudo_principal = ft.Container(content=aba_conversor, expand=True)

    def abrir_conversor(e):
        conteudo_principal.content = aba_conversor
        page.update()

    def abrir_downloader(e):
        conteudo_principal.content = aba_downloader
        page.update()

    menu_navegacao = ft.Row(
        controls=[
            ft.Button("Conversor", icon=ft.Icons.SWAP_HORIZ, on_click=abrir_conversor),
            ft.Button("YouTube Downloader", icon=ft.Icons.VIDEO_LIBRARY, on_click=abrir_downloader),
            ft.IconButton(
                icon=ft.Icons.SYSTEM_UPDATE,
                tooltip="Verificar Atualizações",
                on_click=verificar_atualizacao
            )
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    page.add(
        menu_navegacao,
        ft.Divider(),
        conteudo_principal,
        ft.Divider(),
        txt_status
    )


if __name__ == "__main__":
    ft.app(target=main)