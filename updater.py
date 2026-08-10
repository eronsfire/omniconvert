import os
import glob
import requests
from utils import obter_pasta_downloads, instalar_apk

VERSION_ATUAL = "0.9.4"
REPO_GITHUB = "eronsfire/omniconvert"

class AppUpdater:
    def __init__(self, callback_status):
        self.mostrar_status = callback_status

    def checar_atualizacao(self, callback_progresso_apk):
        """Verifica se há nova release no GitHub e instala o APK."""
        try:
            url_api = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
            res = requests.get(url_api, timeout=8)

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
                        self.mostrar_status(f"Nova versão v{tag_versao} encontrada! Baixando...")
                        pasta_dest = obter_pasta_downloads()

                        # Limpeza de APKs antigos
                        try:
                            padrao_apks = os.path.join(pasta_dest, "Conversor_Eronsfire_*.apk")
                            for apk_antigo in glob.glob(padrao_apks):
                                try:
                                    os.remove(apk_antigo)
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        nome_apk = f"Conversor_Eronsfire_v{tag_versao}.apk"
                        caminho_apk = os.path.join(pasta_dest, nome_apk)

                        with requests.get(apk_url, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            total_length = int(r.headers.get('content-length', 0))
                            baixado = 0
                            with open(caminho_apk, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        baixado += len(chunk)
                                        callback_progresso_apk(baixado, total_length)

                        self.mostrar_status(f"Download da v{tag_versao} concluído!\nAbrindo instalador...")
                        instalar_apk(caminho_apk)
                    else:
                        self.mostrar_status(f"Versão v{tag_versao} encontrada, mas sem APK anexo.", True)
                else:
                    self.mostrar_status(f"Você já está na versão mais recente (v{VERSION_ATUAL}).")
            else:
                self.mostrar_status("Nenhuma atualização encontrada no GitHub.")
        except Exception as err:
            self.mostrar_status(f"Erro ao verificar atualização: {str(err)}", True)