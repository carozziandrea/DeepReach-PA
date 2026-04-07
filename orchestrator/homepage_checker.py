"""
Homepage Checker - Trova il link alla sezione Amministrazione Trasparente.

Questo modulo usa Playwright per renderizzare JavaScript e trovare il link AT.
"""

import asyncio
from typing import Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from config import OrchestratorConfig, default_config


class HomepageChecker:
    """
    Controlla la homepage di un sito PA per trovare il link
    alla sezione Amministrazione Trasparente.

    Usa Playwright per il rendering JavaScript, consistente con il crawler.
    """

    def __init__(self, config: OrchestratorConfig = None):
        """
        Inizializza il checker.

        Args:
            config: Configurazione (usa default se non specificata)
        """
        self.config = config or default_config

    def _normalize_url(self, url: str) -> str:
        """Assicura che l'URL abbia lo schema."""
        if not url.startswith('http://') and not url.startswith('https://'):
            return 'https://' + url
        return url

    async def _find_at_link_async(self, homepage_url: str) -> Tuple[bool, Optional[str], str]:
        """
        Versione async della ricerca del link AT.

        Args:
            homepage_url: URL della homepage del sito PA

        Returns:
            Tupla (found, at_url, message)
        """
        homepage_url = self._normalize_url(homepage_url)

        async with async_playwright() as p:
            browser = None
            try:
                # Lancia browser headless
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                    ]
                )

                # Crea contesto con viewport e user agent
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
                )

                page = await context.new_page()

                # Naviga alla homepage
                timeout_ms = self.config.crawl.page_load_timeout * 1000
                try:
                    await page.goto(
                        homepage_url,
                        wait_until='networkidle',
                        timeout=timeout_ms
                    )
                except PlaywrightTimeout:
                    # Fallback: usa domcontentloaded per siti che non raggiungono networkidle
                    await page.goto(
                        homepage_url,
                        wait_until='domcontentloaded',
                        timeout=timeout_ms
                    )

                # Attendi rendering JS
                wait_ms = self.config.crawl.js_render_wait * 1000
                await page.wait_for_timeout(wait_ms)

                # Ottieni HTML renderizzato
                html_content = await page.content()

                # Parse con BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                # Cerca tutti i link
                links = soup.find_all('a')

                if not links:
                    return False, None, "Nessun link trovato nella homepage"

                # Cerca link AT basandosi SOLO sul testo visibile del link
                # (non sull'href, altrimenti matcheremmo sottopagine)

                exact_keywords = [
                    "amministrazione trasparente",
                    "amministrazione-trasparente",
                ]
                partial_keywords = ["trasparenza", "trasparente"]
                href_keywords = [
                    "amministrazione-trasparente",
                    "amministrazione_trasparente",
                    "amministrazione.trasparente",
                    "amm-trasp",
                    "amm_trasp",
                ]

                # Prima passa: cerca match esatti nel testo visibile del link
                for link in links:
                    link_text = link.get_text().lower().strip()
                    link_text_clean = ' '.join(link_text.split())
                    for keyword in exact_keywords:
                        if keyword in link_text_clean:
                            href = link.get('href', '')
                            if href and not href.startswith('#') and not href.startswith('mailto:'):
                                at_url = urljoin(homepage_url, href)
                                return True, at_url, f"Trovato link AT (match esatto testo): '{link.get_text().strip()}'"

                # Seconda passa: cerca match parziali nel testo visibile
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
                                    return True, at_url, f"Trovato link AT (match parziale testo): '{link.get_text().strip()}'"

                # Terza passa: cerca match nell'href (per link con testo non descrittivo o icone)
                for link in links:
                    href = link.get('href', '').lower()
                    if not href or href.startswith('#') or href.startswith('mailto:'):
                        continue
                    for keyword in href_keywords:
                        if keyword in href:
                            at_url = urljoin(homepage_url, link.get('href', ''))
                            return True, at_url, f"Trovato link AT (match href): '{href}'"

                return False, None, "Nessun link Amministrazione Trasparente trovato"

            except PlaywrightTimeout:
                return False, None, f"Timeout: pagina non caricata entro {self.config.crawl.page_load_timeout}s"

            except Exception as e:
                error_msg = str(e).splitlines()[0] if str(e) else "Errore sconosciuto"
                return False, None, f"Errore Playwright: {error_msg}"

            finally:
                if browser:
                    await browser.close()

    def find_at_link(self, homepage_url: str) -> Tuple[bool, Optional[str], str]:
        """
        Cerca il link alla sezione Amministrazione Trasparente nella homepage.

        Wrapper sincrono per compatibilità con il resto del codice.

        Args:
            homepage_url: URL della homepage del sito PA

        Returns:
            Tupla (found, at_url, message):
            - found: True se il link è stato trovato
            - at_url: URL della sezione AT (None se non trovato)
            - message: Messaggio descrittivo
        """
        return asyncio.run(self._find_at_link_async(homepage_url))


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
