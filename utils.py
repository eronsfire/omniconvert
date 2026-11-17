import os
import subprocess
import tempfile
from pathlib import Path

def esta_no_android() -> bool:
    """
    Detecção unificada de ambiente Android (build do Flet/APK).
    Usada por downloader, updater, auth e utils para evitar divergência de ramo.
    """
    try:
        if os.getenv("ANDROID_STORAGE") or os.getenv("ANDROID_ARGUMENT") or os.getenv("ANDROID_ROOT"):
            return True
        if os.path.exists("/system/build.prop"):
            return True
        # O Flet aponta FLET_APP_STORAGE_DATA para o diretório de arquivos do app no Android
        storage = os.getenv("FLET_APP_STORAGE_DATA", "")
        if storage and ("/data/user/" in storage or "/data/data/" in storage):
            return True
    except Exception:
        pass
    return False

def obter_pasta_dados() -> str:
    """
    Retorna um diretório GRAVAVEL para dados internos do app
    (cookies do YouTube, status, etc.).

    NUNCA usa a pasta do código-fonte (somente leitura dentro do APK).
    Ordem de preferência:
      1. FLET_APP_STORAGE_DATA (definido pelo Flutter/Flet em apps rodando, inclui Android)
      2. ~/.omniconvert no PC
      3. Pasta temporária do sistema (último recurso)
    """
    candidatos = []

    env_storage = os.getenv("FLET_APP_STORAGE_DATA")
    if env_storage:
        candidatos.append(env_storage)

    if not esta_no_android():
        candidatos.append(str(Path.home() / ".omniconvert"))

    candidatos.append(os.path.join(tempfile.gettempdir(), "omniconvert"))

    for caminho in candidatos:
        try:
            os.makedirs(caminho, exist_ok=True)
            # Teste real de escrita (evita retornar pasta somente leitura)
            probe = os.path.join(caminho, ".escrita_ok")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return caminho
        except Exception:
            continue

    # Fallback extremo: diretório atual
    return os.getcwd()

def caminho_cookies_youtube() -> str:
    """Caminho unificado do arquivo de cookies do YouTube."""
    return os.path.join(obter_pasta_dados(), "youtube_cookies.txt")

def obter_pasta_downloads() -> str:
    """
    Retorna o caminho correto para salvar mídias:
    - No Android: /storage/emulated/0/Download
    - No PC (Windows/Mac/Linux): Pasta Downloads oficial do usuário
    """
    if esta_no_android():
        memoria_interna = "/storage/emulated/0/Download"
        if os.path.exists(memoria_interna):
            return memoria_interna
        return "/sdcard/Download"

    # No PC (Windows/Linux/Mac), salva direto na pasta Downloads do seu usuário
    pasta_pc = str(Path.home() / "Downloads")
    if not os.path.exists(pasta_pc):
        os.makedirs(pasta_pc, exist_ok=True)
    return pasta_pc

def versao_menor(atual: str, recente: str) -> bool:
    """True se `atual` for anterior a `recente` (comparação numérica por partes)."""
    try:
        from packaging.version import Version
        return Version(atual) < Version(recente)
    except Exception:
        try:
            def _partes(v):
                if not any(ch.isdigit() for ch in v):
                    raise ValueError("versão inválida")
                partes = []
                for pedaco in v.replace("-", ".").split("."):
                    digitos = "".join(ch for ch in pedaco if ch.isdigit())
                    partes.append(int(digitos) if digitos else 0)
                return partes
            return _partes(atual) < _partes(recente)
        except Exception:
            return False

def mapear_formato(qualidade: str, tem_ffmpeg: bool = False) -> str:
    """
    Converte o rótulo da UI em um seletor de formato do yt-dlp.

    Com FFmpeg disponível, prefere segmentos vídeo+áudio mesclados (qualidade
    máxima real). Sem FFmpeg (ex.: Android), usa arquivo único pré-mesclado.
    """
    if qualidade.startswith("Apenas Áudio (MP3"):
        return "audio"
    if qualidade == "Apenas Áudio (Melhor Qualidade)":
        return "bestaudio/ba"

    alturas = {
        "8K (7680p)": 7680,
        "4K (2160p)": 2160,
        "2K (1440p)": 1440,
        "Full HD (1080p)": 1080,
        "HD (720p)": 720,
        "Standard (480p)": 480,
        "Low (360p)": 360,
        "Mínima (240p)": 240,
    }

    if tem_ffmpeg:
        if qualidade == "Melhor Qualidade (Máxima)":
            return "bv*+ba/best"
        altura = alturas.get(qualidade)
        if altura:
            return f"bv*[height<={altura}]+ba/b[height<={altura}]/best[height<={altura}][ext=mp4]/best"
    else:
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
        }
        if qualidade in formatos:
            return formatos[qualidade]

    return "best[ext=mp4]/best"

def instalar_apk(caminho_apk: str) -> bool:
    """Dispara o instalador padrão do Android com suporte a permissões do sistema."""
    if not os.path.exists(caminho_apk):
        print("[ERROR] Arquivo APK não encontrado.")
        return False

    try:
        # Tenta o comando com as permissões de URI
        cmd = [
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", f"file://{caminho_apk}",
            "-t", "application/vnd.android.package-archive",
            "-f", "0x10000001"  # FLAG_ACTIVITY_NEW_TASK + FLAG_GRANT_READ_URI_PERMISSION
        ]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"[ERROR] Falha ao invocar instalador: {e}")
        return False
