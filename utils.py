import os
import subprocess

def obter_pasta_downloads():
    """Retorna o caminho da pasta Download."""
    memoria_interna = "/storage/emulated/0/Download"
    if os.path.exists(memoria_interna):
        return memoria_interna
    return "/sdcard/Download"

def instalar_apk(caminho_apk: str) -> bool:
    """Dispara o instalador padrão do Android via Activity Manager."""
    try:
        cmd = [
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", f"file://{caminho_apk}",
            "-t", "application/vnd.android.package-archive",
            "-f", "0x10000000"
        ]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"[ERROR] Falha ao invocar instalador: {e}")
        return False