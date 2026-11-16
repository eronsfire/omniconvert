import os
import glob
import hashlib
import requests
import subprocess
import webbrowser
from config import APP_VERSION, GITHUB_REPO
from utils import obter_pasta_downloads, esta_no_android

class AppUpdater:
    def __init__(self, callback_status):
        self.mostrar_status = callback_status

    def _api_url(self) -> str:
        return f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def _pagina_releases(self) -> str:
        return f"https://github.com/{GITHUB_REPO}/releases/latest"

    def _achar_asset(self, assets, extensao):
        for asset in assets:
            if asset.get("name", "").lower().endswith(extensao):
                return asset
        return None

    def _verificar_sha256(self, caminho: str, hash_esperado: str) -> bool:
        """Confere o SHA-256 do arquivo baixado com o hash publicado na release."""
        sha256 = hashlib.sha256()
        with open(caminho, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)
        calculado = sha256.hexdigest().lower()
        esperado = hash_esperado.strip().split()[0].lower()
        return calculado == esperado

    def checar_e_atualizar(self, callback_progresso_apk):
        """
        Verifica a release mais recente no GitHub.

        - Desktop (PC): não dá para instalar APK — abre a página de releases no navegador.
        - Android: baixa o APK para a pasta Downloads, confere o SHA-256 (se a release
          publicar .sha256) e abre o instalador. O APK fica no aparelho; APKs antigos
          do app são removidos antes do próximo download.
        """
        try:
            res = requests.get(self._api_url(), timeout=8)

            if res.status_code != 200:
                self.mostrar_status("Erro ao consultar lançamentos do GitHub.", True)
                return

            dados = res.json()
            tag_versao = dados.get("tag_name", "").lstrip("v").strip()

            if not tag_versao:
                self.mostrar_status("Release sem tag de versão.", True)
                return

            if tag_versao == APP_VERSION:
                self.mostrar_status(f"Seu app já está atualizado (v{APP_VERSION}).")
                return

            assets = dados.get("assets", [])
            apk_asset = self._achar_asset(assets, ".apk")
            sha_asset = self._achar_asset(assets, ".apk.sha256") or self._achar_asset(assets, ".sha256")
            release_url = dados.get("html_url", self._pagina_releases())

            # --- Desktop: atualização manual (APK não instala no PC) ---
            if not esta_no_android():
                self.mostrar_status(
                    f"Nova versão v{tag_versao} disponível. Abrindo a página de releases no navegador..."
                )
                try:
                    webbrowser.open(release_url)
                except Exception:
                    self.mostrar_status(f"Nova versão v{tag_versao}: {release_url}")
                return

            # --- Android: baixa, confere e abre o instalador ---
            if not apk_asset:
                self.mostrar_status(f"Nova versão v{tag_versao} sem APK anexo.", True)
                return

            apk_url = apk_asset.get("browser_download_url")
            pasta_dest = obter_pasta_downloads()

            # Remove APKs antigos DESTE APP antes de baixar o novo
            for apk_antigo in glob.glob(os.path.join(pasta_dest, "Conversor_Eronsfire_*.apk")):
                try:
                    os.remove(apk_antigo)
                    print(f"[DEBUG] APK antigo removido: {apk_antigo}")
                except Exception as e:
                    print(f"[DEBUG] Não conseguiu remover APK antigo: {e}")

            caminho_apk = os.path.join(pasta_dest, f"Conversor_Eronsfire_v{tag_versao}.apk")

            self.mostrar_status(f"Baixando versão v{tag_versao}...")
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

            # --- Verificação de integridade (SHA-256) ---
            if sha_asset:
                try:
                    res_sha = requests.get(sha_asset.get("browser_download_url"), timeout=15)
                    res_sha.raise_for_status()
                    hash_esperado = res_sha.text.strip()
                    if not self._verificar_sha256(caminho_apk, hash_esperado):
                        os.remove(caminho_apk)
                        self.mostrar_status(
                            "APK baixado não confere com o hash SHA-256 da release. "
                            "Arquivo descartado por segurança.",
                            True,
                        )
                        return
                    print("[DEBUG] SHA-256 do APK confere com a release.")
                except Exception as e:
                    os.remove(caminho_apk)
                    self.mostrar_status(f"Não foi possível verificar a integridade do APK: {e}", True)
                    return
            else:
                print("[WARN] Release sem arquivo .sha256 — verificação de integridade pulada.")

            self.mostrar_status("Download pronto! Abrindo instalador...")
            print(f"[DEBUG] APK salvo em: {caminho_apk}")
            self._chamar_instalador_sistema(caminho_apk)

        except Exception as err:
            self.mostrar_status(f"Erro no processo: {str(err)}", True)

    def _chamar_instalador_sistema(self, caminho_apk: str):
        """
        Tenta abrir o instalador de pacotes do Android.
        Em aparelhos onde o intent file:// não funciona (Android 7+),
        orienta o usuário a abrir o APK manualmente pela pasta Downloads.
        """
        try:
            cmd = [
                "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", f"file://{caminho_apk}",
                "-t", "application/vnd.android.package-archive",
                "-f", "0x10000001"  # FLAG_ACTIVITY_NEW_TASK | FLAG_GRANT_READ_URI_PERMISSION
            ]
            resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if resultado.returncode == 0:
                print("[INFO] Instalador aberto no Android")
                self.mostrar_status("Instalador aberto. Confirme a instalação.")
            else:
                raise RuntimeError(resultado.stderr.strip() or f"am start retornou {resultado.returncode}")
        except Exception as e:
            self.mostrar_status(
                "Não foi possível abrir o instalador automaticamente. "
                f"Abra o arquivo manualmente: {caminho_apk} ({e})",
                True,
            )
            print(f"[ERROR] Falha ao abrir instalador: {e}")
