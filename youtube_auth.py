import os
import time
import shutil
import webbrowser
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.firefox import GeckoDriverManager
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    webdriver = None
    ChromeOptions = FirefoxOptions = None
    FirefoxService = ChromeService = None
    GeckoDriverManager = ChromeDriverManager = None

from utils import esta_no_android, obter_pasta_dados, caminho_cookies_youtube

# Cookies que comprovam login ativo no YouTube/Google
MARCADORES_LOGIN = (
    "SID",
    "HSID",
    "SSID",
    "LOGIN_INFO",
    "__Secure-1PSID",
    "__Secure-3PSID",
    "__Host-1PLSID",
    "__Host-3PLSID",
)

class YouTubeAuthenticator:
    """
    Gerencia a autenticação no YouTube para o yt-dlp.

    Fluxos suportados:
      - Desktop (PC): abre o Chrome/Firefox via Selenium, aguarda o login e
        captura os cookies reais automaticamente.
      - Android (APK): não existe API pública para ler cookies do Chrome no
        Android. O fluxo honesto é: abrir o YouTube no Chrome para o usuário
        logar e depois IMPORTAR um cookies.txt exportado do navegador
        (extensão "Get cookies.txt LOCALLY"), que é usado pelo yt-dlp.

    Em ambos os casos, o arquivo de cookies fica num diretório gravável
    (ver utils.obter_pasta_dados) e segue o formato Netscape exigido pelo yt-dlp.
    """

    def __init__(self, callback_status=None):
        self.callback_status = callback_status or print
        self.data_dir = obter_pasta_dados()
        self.cookies_path = caminho_cookies_youtube()
        self._migrar_cookies_antigos()

    # ---------- utilidades internas ----------

    def _migrar_cookies_antigos(self) -> None:
        """Copia cookies salvos ao lado do código-fonte (versões antigas) para o data dir."""
        try:
            antigo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_cookies.txt")
            if antigo != self.cookies_path and os.path.exists(antigo) and not os.path.exists(self.cookies_path):
                os.makedirs(self.data_dir, exist_ok=True)
                shutil.copy2(antigo, self.cookies_path)
                print(f"[AUTH] Cookies antigos migrados para: {self.cookies_path}")
        except Exception as exc:
            print(f"[AUTH] Não foi possível migrar cookies antigos: {exc}")

    # Prefixos de linha no formato Netscape que representam cookies (não comentários)
    @staticmethod
    def _linhas_cookies(conteudo: str) -> list[str]:
        linhas = []
        for bruta in conteudo.splitlines():
            linha = bruta.rstrip("\n").rstrip()
            if not linha:
                continue
            # Exportadores marcam cookies HttpOnly com "#HttpOnly_" — isso NÃO é comentário
            if linha.startswith("#HttpOnly_"):
                linha = linha[len("#HttpOnly_"):]
            elif linha.startswith("#"):
                continue  # comentário/cabeçalho
            linhas.append(linha)
        return linhas

    @classmethod
    def analisar_cookies_netscape(cls, conteudo: str) -> dict:
        """
        Valida um texto no formato Netscape (cookies.txt).
        Retorna dict com: total, youtube, marcadores (lista dos marcadores de login achados).
        """
        resultado = {"total": 0, "youtube": 0, "marcadores": []}
        linhas = cls._linhas_cookies(conteudo)
        cookies_yt = []
        for linha in linhas:
            partes = linha.split("\t")
            if len(partes) < 7:
                continue
            resultado["total"] += 1
            dominio = partes[0].lower()
            if "youtube.com" in dominio or "google.com" in dominio:
                resultado["youtube"] += 1
                cookies_yt.append((dominio, partes))
        marcadores = set()
        for _, partes in cookies_yt:
            nome = partes[5] if len(partes) > 5 else ""
            for marcador in MARCADORES_LOGIN:
                if nome == marcador:
                    marcadores.add(marcador)
        resultado["marcadores"] = sorted(marcadores)
        return resultado

    @staticmethod
    def _contem_marcador_login(cookies: list) -> bool:
        """Verifica se a lista de cookies do Selenium contém algum marcador de login."""
        nomes = {c.get("name", "") for c in cookies}
        return any(marcador in nomes for marcador in MARCADORES_LOGIN)

    def atualizar_status(self, mensagem: str, eh_erro: bool = False):
        """Atualiza o status na UI ou imprime no console."""
        prefixo = "[ERRO]" if eh_erro else "[AUTH]"
        print(f"{prefixo} {mensagem}")
        if self.callback_status:
            try:
                self.callback_status(mensagem, eh_erro)
            except Exception:
                pass

    # ---------- API pública ----------

    def verificar_cookies_validos(self) -> bool:
        """
        True somente se existir um cookies.txt gravável com cookies de login
        reais do YouTube/Google. Nada de 'confirmação manual' sem cookies:
        sem marcador de login o yt-dlp continuará bloqueado como bot.
        """
        if not os.path.exists(self.cookies_path):
            return False
        try:
            with open(self.cookies_path, "r", encoding="utf-8", errors="ignore") as f:
                conteudo = f.read()
            info = self.analisar_cookies_netscape(conteudo)
            return info["youtube"] > 0 and len(info["marcadores"]) > 0
        except Exception:
            return False

    def importar_cookies(self, dados: bytes) -> tuple[bool, str]:
        """
        Valida e salva um cookies.txt (bytes, como vem do seletor de arquivos).
        Usado tanto no Android quanto no desktop.

        Retorna (sucesso, mensagem_para_o_usuario).
        """
        try:
            conteudo = dados.decode("utf-8", errors="ignore")
        except Exception:
            return False, "O arquivo não é um texto válido (cookies.txt)."

        info = self.analisar_cookies_netscape(conteudo)

        if info["total"] == 0:
            return False, (
                "O arquivo não parece um cookies.txt no formato Netscape. "
                "Exporte com a extensão 'Get cookies.txt LOCALLY' (Chrome/Firefox)."
            )
        if info["youtube"] == 0:
            return False, (
                "Nenhuma cookie do YouTube/Google encontrada no arquivo. "
                "Abra o YouTube logado antes de exportar."
            )
        if not info["marcadores"]:
            return False, (
                "Cookies do YouTube encontradas, mas sem as de login "
                f"({', '.join(MARCADORES_LOGIN[:4])}...). "
                "Exporte o arquivo ENQUANTO estiver logado no YouTube."
            )

        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.cookies_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(conteudo)
            try:
                os.chmod(self.cookies_path, 0o600)  # permissão restrita (PC/Linux/Android)
            except Exception:
                pass  # Windows/Android podem ignorar chmod
            print(f"[AUTH] Cookies importadas e salvas em: {self.cookies_path}")
            return True, (
                f"✓ {info['youtube']} cookies do YouTube importadas "
                f"(login detectado: {', '.join(info['marcadores'])}). "
                "O bloqueio de suspeita de bot deve sumir."
            )
        except Exception as exc:
            return False, f"Não foi possível salvar as cookies: {exc}"

    def fazer_login_youtube(self, usar_firefox: bool = False) -> bool:
        """
        Inicia o fluxo de login.

        - Android: abre o YouTube no Chrome do aparelho. Depois o usuário
          exporta o cookies.txt (extensão) e usa 'Importar cookies' no app.
          Retorna True se o navegador abriu.
        - Desktop: abre Chrome/Firefox via Selenium e aguarda o login; captura
          os cookies reais automaticamente (até 5 minutos).
        """
        if esta_no_android():
            return self._fluxo_login_android()
        return self._fluxo_login_desktop(usar_firefox=usar_firefox)

    def _fluxo_login_android(self) -> bool:
        try:
            self.atualizar_status("Abrindo o YouTube no navegador...")
            abriu = webbrowser.open("https://www.youtube.com")
            if abriu:
                self.atualizar_status(
                    "Chrome aberto. Faça login no YouTube e depois toque em "
                    "'Importar cookies' (ícone de upload) com o cookies.txt "
                    "exportado pela extensão do navegador."
                )
                return True
            self.atualizar_status(
                "Não foi possível abrir o navegador. Tente abrir o YouTube manualmente.",
                eh_erro=True,
            )
            return False
        except Exception as exc:
            self.atualizar_status(f"Erro ao abrir o navegador: {exc}", eh_erro=True)
            return False

    def _criar_driver(self, usar_firefox: bool):
        """Cria o WebDriver: tenta o selenium-manager embutido; cai para webdriver-manager."""
        if usar_firefox:
            options = FirefoxOptions()
            options.add_argument("--new-instance")
            options.headless = False
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            try:
                return webdriver.Firefox(options=options)  # selenium-manager cuida do driver
            except Exception:
                service = FirefoxService(GeckoDriverManager().install())
                return webdriver.Firefox(service=service, options=options)
        else:
            options = ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--start-maximized")
            try:
                return webdriver.Chrome(options=options)  # selenium-manager cuida do driver
            except Exception:
                service = ChromeService(ChromeDriverManager().install())
                return webdriver.Chrome(service=service, options=options)

    def _fluxo_login_desktop(self, usar_firefox: bool = False) -> bool:
        if webdriver is None:
            self.atualizar_status(
                "Selenium não está disponível. Use 'Importar cookies' como alternativa.",
                eh_erro=True,
            )
            return False

        driver = None
        try:
            self.atualizar_status("Iniciando navegador para login...")
            driver = self._criar_driver(usar_firefox)
        except Exception as exc:
            self.atualizar_status(
                f"Não foi possível abrir o navegador ({exc}). "
                "Use 'Importar cookies' como alternativa.",
                eh_erro=True,
            )
            return False

        try:
            self.atualizar_status("Abrindo YouTube... Faça login na janela que abriu.")
            self.atualizar_status("Você tem até 5 minutos para concluir o login.")
            driver.get("https://www.youtube.com")

            deadline = time.time() + 300
            while time.time() < deadline:
                try:
                    cookies = driver.get_cookies()
                except Exception:
                    cookies = []
                if cookies and self._contem_marcador_login(cookies):
                    self.salvar_cookies_netscape(cookies)
                    self.atualizar_status(
                        f"✓ Login confirmado! {len(cookies)} cookies salvas. "
                        "O bloqueio de suspeita de bot deve sumir."
                    )
                    return True
                time.sleep(2)

            self.atualizar_status(
                "Tempo esgotado aguardando o login (5 min). Tente novamente.",
                eh_erro=True,
            )
            return False
        except Exception as exc:
            self.atualizar_status(f"Erro durante o login: {exc}", eh_erro=True)
            print(f"[AUTH] Stack trace: {type(exc).__name__}: {exc}")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    # ---------- gravação/leitura do arquivo ----------

    def salvar_cookies_netscape(self, cookies: list) -> None:
        """Salva cookies do Selenium no formato Netscape (compatível com yt-dlp)."""
        os.makedirs(self.data_dir, exist_ok=True)
        linhas = [
            "# Netscape HTTP Cookie File",
            "# Cookies capturados do YouTube pelo Conversor Eronsfire",
            "# Domínio\tFlag\tCaminho\tSeguro\tExpiração\tNome\tValor",
            "",
        ]
        for cookie in cookies:
            if "name" not in cookie or "value" not in cookie:
                continue
            domain = cookie.get("domain", ".youtube.com")
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            flag = "TRUE" if domain.startswith(".") else "FALSE"
            expires = cookie.get("expiry", 9999999999)
            linhas.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}")

        conteudo = "\n".join(linhas) + "\n"
        with open(self.cookies_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(conteudo)
        try:
            os.chmod(self.cookies_path, 0o600)
        except Exception:
            pass
        print(f"[AUTH] Cookies salvas em: {self.cookies_path}")

    def limpar_cookies(self) -> bool:
        """Remove o arquivo de cookies."""
        try:
            if os.path.exists(self.cookies_path):
                os.remove(self.cookies_path)
                self.atualizar_status("Cookies removidas com sucesso.")
                return True
            return False
        except Exception as exc:
            self.atualizar_status(f"Erro ao remover cookies: {exc}", eh_erro=True)
            return False

    def obter_info_cookies(self) -> dict:
        """Retorna informações sobre o arquivo de cookies."""
        if not os.path.exists(self.cookies_path):
            return {
                "existe": False,
                "mensagem": "Nenhum cookie salvo. Faça login primeiro ou importe um cookies.txt.",
            }
        try:
            tamanho = os.path.getsize(self.cookies_path)
            mod_time = os.path.getmtime(self.cookies_path)
            data_mod = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M:%S")
            with open(self.cookies_path, "r", encoding="utf-8", errors="ignore") as f:
                info = self.analisar_cookies_netscape(f.read())
            return {
                "existe": True,
                "tamanho_bytes": tamanho,
                "num_cookies": info["total"],
                "cookies_youtube": info["youtube"],
                "marcadores_login": info["marcadores"],
                "login_valido": bool(info["marcadores"]),
                "ultima_modificacao": data_mod,
                "caminho": self.cookies_path,
            }
        except Exception as exc:
            return {"existe": True, "erro": str(exc)}
