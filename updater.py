import os
import glob
import requests
import subprocess
from config import get_download_path, APP_VERSION, GITHUB_REPO

class AppUpdater:
    def __init__(self, callback_status):
        self.mostrar_status = callback_status

    def checar_e_atualizar(self, callback_progresso_apk):
        """Automação completa: Limpa velhos, baixa novo e abre o instalador na tela."""
        try:
            url_api = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            res = requests.get(url_api, timeout=8)

            if res.status_code == 200:
                dados = res.json()
                tag_versao = dados.get("tag_name", "").replace("v", "").strip()

                if tag_versao and tag_versao != APP_VERSION:
                    apk_url = None
                    for asset in dados.get("assets", []):
                        if asset.get("name", "").endswith(".apk"):
                            apk_url = asset.get("browser_download_url")
                            break

                    if apk_url:
                        self.mostrar_status(f"Baixando versão v{tag_versao}...")
                        pasta_dest = get_download_path()

                        # 1. ETAPA AUTOMÁTICA: Apaga qualquer APK antigo da pasta de Download
                        for apk_antigo in glob.glob(os.path.join(pasta_dest, "Conversor_Eronsfire_*.apk")):
                            try:
                                os.remove(apk_antigo)
                            except Exception:
                                pass

                        caminho_apk = os.path.join(pasta_dest, f"Conversor_Eronsfire_v{tag_versao}.apk")

                        # 2. ETAPA AUTOMÁTICA: Baixa a nova versão
                        with requests.get(apk_url, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            total_size = int(r.headers.get('content-length', 0))
                            baixado = 0
                            with open(caminho_apk, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        baixado += len(chunk)
                                        callback_progresso_apk(baixado, total_size)

                        self.mostrar_status("Download pronto! Abrindo instalador...")
                        
                        # 3. ETAPA AUTOMÁTICA: Chama a tela do sistema para Atualizar/Sobrescrever
                        self._chamar_instalador_sistema(caminho_apk)
                    else:
                        self.mostrar_status(f"Nova versão v{tag_versao} sem APK anexo.", True)
                else:
                    self.mostrar_status(f"Seu app já está atualizado (v{APP_VERSION}).")
            else:
                self.mostrar_status("Erro ao consultar lançamentos do GitHub.", True)
        except Exception as err:
            self.mostrar_status(f"Erro no processo: {str(err)}", True)

    def _chamar_instalador_sistema(self, caminho_apk: str):
        """Abre a janela nativa do Android que pergunta: 'Deseja atualizar este aplicativo?'"""
        try:
            cmd = [
                "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", f"file://{caminho_apk}",
                "-t", "application/vnd.android.package-archive",
                "-f", "0x10000000"
            ]
            subprocess.run(cmd, check=True)
        except Exception as e:
            self.mostrar_status(f"Falha ao abrir instalador: {e}", True)