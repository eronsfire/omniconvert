import os
import glob
import time
import requests
import subprocess
import threading
from config import get_download_path, APP_VERSION, GITHUB_REPO

class AppUpdater:
    def __init__(self, callback_status):
        self.mostrar_status = callback_status
        self.aguardando_instalacao = False

    def checar_e_atualizar(self, callback_progresso_apk):
        """Automação completa: Limpa velhos, baixa novo, abre instalador e apaga após instalar."""
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
                                print(f"[DEBUG] APK antigo removido: {apk_antigo}")
                            except Exception as e:
                                print(f"[DEBUG] Não conseguiu remover APK antigo: {e}")

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
                        print(f"[DEBUG] APK salvo em: {caminho_apk}")
                        
                        # 3. ETAPA AUTOMÁTICA: Chama o instalador do sistema
                        self._chamar_instalador_sistema(caminho_apk)
                        
                        # 4. ETAPA AUTOMÁTICA: Inicia limpeza automática em background
                        threading.Thread(
                            target=self._limpar_apk_apos_instalacao,
                            args=(caminho_apk,),
                            daemon=True
                        ).start()
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
            eh_android = 'ANDROID_STORAGE' in os.environ or 'ANDROID_ARGUMENT' in os.environ
            
            if eh_android:
                # Android: Usa am start
                cmd = [
                    "am", "start",
                    "-a", "android.intent.action.VIEW",
                    "-d", f"file://{caminho_apk}",
                    "-t", "application/vnd.android.package-archive",
                    "-f", "0x10000000"
                ]
                subprocess.run(cmd, check=True)
                print("[INFO] Instalador aberto no Android")
            else:
                # PC Windows: Executa o APK com aplicativo padrão
                os.startfile(caminho_apk)
                print("[INFO] Instalador aberto no PC")
                
        except Exception as e:
            self.mostrar_status(f"Falha ao abrir instalador: {e}", True)
            print(f"[ERROR] Stack trace: {e}")

    def _limpar_apk_apos_instalacao(self, caminho_apk: str):
        """
        Monitora a instalação e deleta o APK após o processo terminar.
        Aguarda 30 segundos após o download começar (tempo estimado de instalação).
        """
        try:
            print(f"[DEBUG] Iniciando monitoramento de limpeza para: {caminho_apk}")
            
            # Aguarda 30 segundos (tempo para o usuário confirmar/instalar)
            time.sleep(30)
            
            # Tenta deletar o arquivo
            if os.path.exists(caminho_apk):
                try:
                    os.remove(caminho_apk)
                    self.mostrar_status(f"✓ APK temporário removido automaticamente")
                    print(f"[SUCCESS] APK apagado: {caminho_apk}")
                except PermissionError:
                    # Arquivo ainda está em uso, tenta novamente
                    print(f"[DEBUG] APK em uso, tentando novamente em 10s...")
                    time.sleep(10)
                    try:
                        os.remove(caminho_apk)
                        self.mostrar_status(f"✓ APK removido após instalação")
                        print(f"[SUCCESS] APK apagado na segunda tentativa: {caminho_apk}")
                    except Exception as e:
                        print(f"[WARN] Não foi possível remover APK: {e}")
                except Exception as e:
                    print(f"[ERROR] Erro ao remover APK: {e}")
            else:
                print(f"[DEBUG] APK já foi deletado ou movido: {caminho_apk}")
                
        except Exception as e:
            print(f"[ERROR] Erro no processo de limpeza: {e}")