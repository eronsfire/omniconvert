import os
import sys
import subprocess
from pathlib import Path

def obter_pasta_downloads() -> str:
    """
    Retorna o caminho correto para salvar mídias:
    - No Android: /storage/emulated/0/Download
    - No PC (Windows/Mac/Linux): Pasta Downloads oficial do usuário
    """
    # Verifica se está rodando no ambiente Android
    is_android = 'ANDROID_STORAGE' in os.environ or 'ANDROID_ARGUMENT' in os.environ

    if is_android:
        memoria_interna = "/storage/emulated/0/Download"
        if os.path.exists(memoria_interna):
            return memoria_interna
        return "/sdcard/Download"
    else:
        # No PC (Windows/Linux/Mac), salva direto na pasta Downloads do seu usuário
        pasta_pc = str(Path.home() / "Downloads")
        if not os.path.exists(pasta_pc):
            os.makedirs(pasta_pc, exist_ok=True)
        return pasta_pc

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