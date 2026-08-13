import os
import json
import time
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.firefox import GeckoDriverManager
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    webdriver = None
    By = None
    WebDriverWait = None
    EC = None
    ChromeOptions = FirefoxOptions = None
    FirefoxService = ChromeService = None
    GeckoDriverManager = ChromeDriverManager = None


def _esta_no_android() -> bool:
    """Detecta ambiente Android/serious_python para evitar uso de navegador em APK."""
    return (
        os.getenv("ANDROID_ROOT") is not None
        or os.getenv("ANDROID_DATA") is not None
        or os.getenv("ANDROID_STORAGE") is not None
        or os.path.exists("/system/build.prop")
        or os.path.exists("/sdcard")
    )


class YouTubeAuthenticator:
    """Gerencia login automático no YouTube e captura de cookies."""

    def __init__(self, callback_status=None):
        self.callback_status = callback_status or print
        self.cookies_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "youtube_cookies.txt"
        )
        self.login_status_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "youtube_login_status.json"
        )

    def marcar_login_confirmado(self) -> bool:
        """Marca que o usuário confirmou o login manual no navegador."""
        try:
            payload = {
                "confirmado": True,
                "data": datetime.utcnow().isoformat(timespec="seconds") + "Z"
            }
            with open(self.login_status_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            return True
        except Exception as exc:
            print(f"[ERROR] Falha ao gravar confirmação de login: {exc}")
            return False

    def login_confirmado_recentemente(self) -> bool:
        """Retorna True se o login foi confirmado dentro de 7 dias."""
        if not os.path.exists(self.login_status_path):
            return False
        try:
            with open(self.login_status_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            data_str = dados.get("data")
            if not data_str:
                return False
            data = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            return datetime.now(data.tzinfo) - data < timedelta(days=7)
        except Exception:
            return False

    def atualizar_status(self, mensagem: str, eh_erro: bool = False):
        """Atualiza o status na UI ou imprime no console."""
        if eh_erro:
            print(f"[ERRO] {mensagem}")
        else:
            print(f"[INFO] {mensagem}")
        
        if self.callback_status:
            try:
                self.callback_status(mensagem, eh_erro)
            except:
                pass

    def verificar_cookies_validos(self) -> bool:
        """Verifica se existem cookies salvos ou confirmação recente de login manual."""
        if os.path.exists(self.cookies_path):
            try:
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    conteudo = f.read().strip()
                    if len(conteudo) > 0:
                        return True
            except Exception:
                pass

        return self.login_confirmado_recentemente()

    def fazer_login_youtube(self, usar_firefox: bool = False) -> bool:
        """
        Abre navegador e permite login manual no YouTube.
        Captura cookies automaticamente após o login.
        
        Args:
            usar_firefox: Se True, usa Firefox. Se False, usa Chrome.
        
        Returns:
            True se login foi bem-sucedido, False caso contrário.
        """
        if _esta_no_android():
            try:
                webbrowser.open("https://www.youtube.com")
                self.atualizar_status(
                    "Navegador aberto. Faça login no YouTube e depois toque em Confirmar login.",
                    eh_erro=False,
                )
                return True
            except Exception as exc:
                self.atualizar_status(
                    f"Não foi possível abrir o navegador do sistema: {exc}",
                    eh_erro=True,
                )
                return False

        if webdriver is None or GeckoDriverManager is None or ChromeDriverManager is None:
            self.atualizar_status(
                "Dependências do navegador não estão disponíveis nesta build.",
                eh_erro=True,
            )
            return False

        driver = None
        try:
            self.atualizar_status("Iniciando navegador para login...")
            
            # Configurar opções do navegador
            if usar_firefox:
                options = FirefoxOptions()
                # Remover flags que causam fechamento automático
                options.add_argument("--new-instance")
                options.headless = False  # Modo visual, não headless
                options.set_preference("dom.webdriver.enabled", False)
                options.set_preference("useAutomationExtension", False)
                
                # Usar GeckoDriverManager para gerenciar o driver
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            else:
                options = ChromeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_argument("--start-maximized")
                
                # Usar ChromeDriverManager para gerenciar o driver
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)

            self.atualizar_status("Abrindo YouTube...")
            driver.get("https://www.youtube.com")
            
            # Aguarda o usuário fazer login
            self.atualizar_status("Por favor, faça login no YouTube no navegador que se abriu.")
            self.atualizar_status("Você tem até 5 minutos para completar o login...")
            
            # Espera até 5 minutos pelo login (verifica a presença do perfil)
            wait = WebDriverWait(driver, 300)  # 5 minutos
            try:
                # Aguarda um indicador de que o usuário está logado
                wait.until(
                    EC.presence_of_element_located((By.XPATH, "//yt-icon-button[@aria-label*='Conta']"))
                )
            except:
                # Alternativa: procura por outros indicadores de login
                try:
                    wait.until(
                        EC.presence_of_element_located((By.XPATH, "//img[@alt='Perfil']"))
                    )
                except:
                    # Se nenhum indicador foi encontrado, tenta verificar cookies
                    time.sleep(5)

            self.atualizar_status("Login detectado! Capturando cookies...")
            
            # Capturar todos os cookies
            cookies = driver.get_cookies()
            
            if not cookies:
                self.atualizar_status("Nenhum cookie foi capturado. Tente novamente.", eh_erro=True)
                return False

            # Salvar cookies em formato Netscape (compatível com yt-dlp)
            self.salvar_cookies_netscape(cookies)
            
            self.atualizar_status(
                f"✓ Login realizado com sucesso! {len(cookies)} cookies salvos.",
                eh_erro=False
            )
            return True

        except Exception as e:
            self.atualizar_status(f"Erro durante login: {str(e)}", eh_erro=True)
            print(f"[DEBUG] Stack trace: {type(e).__name__}: {e}")
            return False

        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def salvar_cookies_netscape(self, cookies: list):
        """
        Salva cookies em formato Netscape (compatível com yt-dlp).
        
        Args:
            cookies: Lista de cookies do Selenium
        """
        try:
            with open(self.cookies_path, 'w') as f:
                # Cabeçalho do formato Netscape
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# Cookies capturados para YouTube\n")
                f.write("# Domínio\tFlag\tCaminho\tSeguro\tExpiração\tNome\tValor\n\n")

                for cookie in cookies:
                    # Pular cookies sem name ou value
                    if 'name' not in cookie or 'value' not in cookie:
                        continue

                    domain = cookie.get('domain', '.youtube.com')
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    path = cookie.get('path', '/')
                    secure = '1' if cookie.get('secure', False) else '0'
                    
                    # Expiração (timestamp Unix)
                    expires = cookie.get('expiry', 9999999999)
                    
                    # Formato: domínio TAB flag TAB caminho TAB secure TAB expiry TAB nome TAB valor
                    linha = f"{domain}\tTRUE\t{path}\t{secure}\t{expires}\t{name}\t{value}\n"
                    f.write(linha)

            os.chmod(self.cookies_path, 0o600)  # Permissão segura
            print(f"[SUCCESS] Cookies salvos em: {self.cookies_path}")

        except Exception as e:
            print(f"[ERROR] Falha ao salvar cookies: {e}")
            raise

    def limpar_cookies(self) -> bool:
        """Remove o arquivo de cookies."""
        try:
            if os.path.exists(self.cookies_path):
                os.remove(self.cookies_path)
                self.atualizar_status("Cookies removidos com sucesso.")
                return True
            return False
        except Exception as e:
            self.atualizar_status(f"Erro ao remover cookies: {e}", eh_erro=True)
            return False

    def obter_info_cookies(self) -> dict:
        """Retorna informações sobre o arquivo de cookies."""
        if not os.path.exists(self.cookies_path):
            return {
                "existe": False,
                "mensagem": "Nenhum cookie salvo. Faça login primeiro."
            }
        
        try:
            tamanho = os.path.getsize(self.cookies_path)
            mod_time = os.path.getmtime(self.cookies_path)
            from datetime import datetime
            data_mod = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M:%S")
            
            # Contar número de cookies
            with open(self.cookies_path, 'r') as f:
                linhas = f.readlines()
                num_cookies = len([l for l in linhas if l.strip() and not l.startswith('#')])
            
            return {
                "existe": True,
                "tamanho_bytes": tamanho,
                "num_cookies": num_cookies,
                "ultima_modificacao": data_mod,
                "caminho": self.cookies_path
            }
        except Exception as e:
            return {
                "existe": True,
                "erro": str(e)
            }
