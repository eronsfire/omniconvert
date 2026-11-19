import os
import glob
import hashlib
import requests
import webbrowser
from config import APP_VERSION, GITHUB_REPO
from utils import obter_pasta_downloads, obter_pasta_dados, esta_no_android, versao_menor

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
        - Android: baixa o APK para a pasta privada do app, confere o SHA-256 (se a
          release publicar .sha256), grava um marcador de instalação e a Activity nativa
          abre a tela de instalação do Android em segundos (1 toque do usuário — o
          Android não permite instalação 100% silenciosa fora da Play Store).
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

            if not versao_menor(APP_VERSION, tag_versao):
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
            # Em Android usa a pasta privada do app (onde o FileProvider pode servi-lo);
            # no PC usa Downloads normal (mas o PC cai no fluxo de navegador antes).
            pasta_dest = obter_pasta_dados() if esta_no_android() else obter_pasta_downloads()

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

            self.mostrar_status("Download pronto! Verificando e preparando instalação...")
            print(f"[DEBUG] APK salvo em: {caminho_apk}")
            self._chamar_instalador_sistema(caminho_apk)

        except Exception as err:
            self.mostrar_status(f"Erro no processo: {str(err)}", True)

    def _chamar_instalador_sistema(self, caminho_apk: str):
        """
        Android: grava um marcador de instalação pendente na pasta de dados do app.

        A Activity nativa (MainActivity.kt, recurso do build) faz polling desse
        marcador e abre o instalador do Android com o APK via FileProvider
        (content://…) com permissão lida concedida — único jeito de um app comum
        abrir o instalador. O usuário ainda dá o toque final em "Instalar"
        (exigido pelo Android fora da Play Store), mas não precisa ir à pasta
        Downloads nem tocar no APK.

        No PC/navegador, só informa o caminho (desktop não instala APK).
        """
        if esta_no_android():
            pasta = os.path.dirname(caminho_apk)
            marcador = os.path.join(pasta, "install_pending.txt")
            try:
                with open(marcador, "w", encoding="utf-8") as f:
                    f.write(caminho_apk)
                print(f"[INFO] Marcador de instalação gravado: {marcador} -> {caminho_apk}")
                self.mostrar_status(
                    "APK baixado e verificado! A tela de instalação do Android "
                    "será aberta em instantes. Confirme em Instalar.",
                    e_erro=False,
                )
            except Exception as e:
                self.mostrar_status(
                    f"APK baixado, mas não foi possível iniciar o instalador "
                    f"({e}). Abra o arquivo manualmente: {caminho_apk}",
                    True,
                )
            return

        # Desktop: apenas informar (desktop não instala APK)
        self.mostrar_status(f"APK salvo em: {caminho_apk}")
