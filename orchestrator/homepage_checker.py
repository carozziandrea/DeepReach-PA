"""
Homepage Checker - Trova il link alla sezione Amministrazione Trasparente.

Questo modulo integra la logica di check_homepage.py nell'orchestratore.
Usa Selenium per renderizzare JavaScript e trovare il link AT.
"""

import time
from typing import Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException, TimeoutException

from config import OrchestratorConfig, default_config


class HomepageChecker:
    """
    Controlla la homepage di un sito PA per trovare il link 
    alla sezione Amministrazione Trasparente.
    """
    
    def __init__(self, config: OrchestratorConfig = None):
        """
        Inizializza il checker.
        
        Args:
            config: Configurazione (usa default se non specificata)
        """
        self.config = config or default_config
        self.driver: Optional[webdriver.Remote] = None
    
    def _init_driver_firefox(self) -> Optional[webdriver.Firefox]:
        """Inizializza driver Firefox."""
        try:
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.set_preference("log.level", "fatal")
            
            service = FirefoxService(log_path=None)
            driver = webdriver.Firefox(service=service, options=options)
            driver.set_page_load_timeout(self.config.crawl.page_load_timeout)
            return driver
        except WebDriverException:
            return None
    
    def _init_driver_chrome(self) -> Optional[webdriver.Chrome]:
        """Inizializza driver Chrome."""
        try:
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(self.config.crawl.page_load_timeout)
            return driver
        except WebDriverException:
            return None
    
    def _init_driver(self) -> bool:
        """
        Inizializza il WebDriver (prova Firefox, poi Chrome).
        
        Returns:
            True se il driver è stato inizializzato, False altrimenti
        """
        # Prova Firefox
        self.driver = self._init_driver_firefox()
        if self.driver:
            return True
        
        # Prova Chrome
        self.driver = self._init_driver_chrome()
        if self.driver:
            return True
        
        return False
    
    def _normalize_url(self, url: str) -> str:
        """Assicura che l'URL abbia lo schema."""
        if not url.startswith('http://') and not url.startswith('https://'):
            return 'https://' + url
        return url
    
    def find_at_link(self, homepage_url: str) -> Tuple[bool, Optional[str], str]:
        """
        Cerca il link alla sezione Amministrazione Trasparente nella homepage.
        
        Args:
            homepage_url: URL della homepage del sito PA
        
        Returns:
            Tupla (found, at_url, message):
            - found: True se il link è stato trovato
            - at_url: URL della sezione AT (None se non trovato)
            - message: Messaggio descrittivo
        """
        homepage_url = self._normalize_url(homepage_url)
        
        # Inizializza driver
        if not self._init_driver():
            return False, None, "Errore: impossibile inizializzare WebDriver (Firefox/Chrome)"
        
        try:
            # Carica la pagina
            self.driver.get(homepage_url)
            
            # Attendi rendering JS
            time.sleep(self.config.crawl.js_render_wait)
            
            # Parsing HTML
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Cerca tutti i link
            links = soup.find_all('a')
            
            if not links:
                return False, None, "Nessun link trovato nella homepage"
            
            # Cerca link AT basandosi SOLO sul testo visibile del link
            # (non sull'href, altrimenti matcheremmo sottopagine)
            
            # Prima passa: cerca match esatti ("amministrazione trasparente")
            for link in links:
                link_text = link.get_text().lower().strip()
                link_text_clean = ' '.join(link_text.split())  # Normalizza spazi
                
                # Match esatto per le keyword più specifiche
                exact_keywords = [
                    "amministrazione trasparente",
                    "amministrazione-trasparente",
                ]
                
                for keyword in exact_keywords:
                    if keyword in link_text_clean:
                        href = link.get('href', '')
                        if href and not href.startswith('#') and not href.startswith('mailto:'):
                            at_url = urljoin(homepage_url, href)
                            return True, at_url, f"Trovato link AT (match esatto): '{link.get_text().strip()}'"
            
            # Seconda passa: cerca match parziali ("trasparenza", "trasparente")
            partial_keywords = ["trasparenza", "trasparente"]
            
            for link in links:
                link_text = link.get_text().lower().strip()
                link_text_clean = ' '.join(link_text.split())
                
                for keyword in partial_keywords:
                    if keyword in link_text_clean:
                        # Evita falsi positivi: il testo non deve essere troppo lungo
                        # (es. "Nuove regole sulla trasparenza" è una news, non il link AT)
                        if len(link_text_clean) < 50:
                            href = link.get('href', '')
                            if href and not href.startswith('#') and not href.startswith('mailto:'):
                                at_url = urljoin(homepage_url, href)
                                return True, at_url, f"Trovato link AT (match parziale): '{link.get_text().strip()}'"
            
            return False, None, "Nessun link Amministrazione Trasparente trovato"
        
        except TimeoutException:
            return False, None, f"Timeout: pagina non caricata entro {self.config.crawl.page_load_timeout}s"
        
        except WebDriverException as e:
            return False, None, f"Errore WebDriver: {str(e).splitlines()[0]}"
        
        except Exception as e:
            return False, None, f"Errore imprevisto: {e}"
        
        finally:
            self.close()
    
    def close(self) -> None:
        """Chiude il WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


def check_homepage(url: str, config: OrchestratorConfig = None) -> Tuple[bool, Optional[str], str]:
    """
    Funzione di convenienza per controllare una homepage.
    
    Args:
        url: URL della homepage
        config: Configurazione opzionale
    
    Returns:
        Tupla (found, at_url, message)
    """
    checker = HomepageChecker(config)
    return checker.find_at_link(url)


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python homepage_checker.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"Controllo: {url}")
    
    found, at_url, message = check_homepage(url)
    
    print(f"Risultato: {message}")
    if found:
        print(f"URL AT: {at_url}")