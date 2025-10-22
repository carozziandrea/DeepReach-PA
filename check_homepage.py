import sys
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import WebDriverException, TimeoutException

KEYWORDS = [
    #TODO: regex
    "amministrazione trasparente",
    "amministrazione-trasparente",
    "amministrazione.trasparente",
    "amministrazione_trasparente"
    "trasparenza",
    "trasparente"
]


PAGE_LOAD_TIMEOUT = 20
JS_RENDER_WAIT = 5

def lettura_file(filepath):
    try:
        with open(filepath, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        if not urls:
            print(f"Attenzione: Il file '{filepath}' è vuoto.")
        return urls
    except FileNotFoundError:
        print(f"Errore: File non trovato al percorso '{filepath}'")
        return []
    except Exception as e:
        print(f"Errore imprevisto durante la lettura del file: {e}")
        return []

def inizializza_driver():
    ff_options = FirefoxOptions()
    ff_options.add_argument("--headless")
    ff_options.add_argument("--disable-gpu")
    ff_options.add_argument("--window-size=1920,1080")
    
    ff_options.add_argument("-log")
    ff_options.set_preference("log.level", "fatal")

    service = FirefoxService(log_path=None) 
    
    try:
        driver = webdriver.Firefox(service=service, options=ff_options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        return driver
    except WebDriverException as e:
        print("\n" + "="*30)
        print("ERRORE CRITICO: Impossibile avviare Selenium/WebDriver.")
        print("Assicurati che 'geckodriver' sia nella stessa cartella di questo script.")
        print(f"Dettaglio errore: {e}")
        print("="*30)
        return None
    except Exception as e:
        print(f"\nERRORE CRITICO: Errore imprevisto nell'avvio del driver: {e}")
        return None


def controlla_url_con_selenium(driver, url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url_https = 'https://' + url
        print(f"Aggiungo 'https://' -> {url_https}")
        url = url_https
        
    try:
        driver.get(url)
        
        print(f"Attendo {JS_RENDER_WAIT} sec per il rendering del JavaScript...")
        time.sleep(JS_RENDER_WAIT)

        html_content = driver.page_source
        
        soup = BeautifulSoup(html_content, 'html.parser')

        links = soup.find_all('a')
        
        if not links:
            print("INFO: Nessun tag <a> trovato nell'HTML renderizzato.")
            return False

        for link in links:
            link_text = link.get_text().lower().strip()
            link_href = str(link.get('href')).lower()

            for keyword in KEYWORDS:
                if keyword in link_text:
                    print(f"TROVATO (Testo: '{link.get_text().strip()}')")
                    return True

        print("NON TROVATO")
        return False

    except TimeoutException:
        print(f"ERRORE: Timeout caricamento pagina dopo {PAGE_LOAD_TIMEOUT} secondi.")
        return False
    except WebDriverException as e:
        print(f"ERRORE: Problema di Selenium/WebDriver durante il caricamento.")
        print(f"  Dettaglio: {str(e).splitlines()[0]}")
        return False
    except Exception as e:
        print(f"ERRORE: Analisi fallita ({e})")
        return False

def main():
    filepath = "./lista_siti.txt"
    
    urls = lettura_file(filepath)
    
    if not urls:
        print("Nessun URL da analizzare. Uscita.")
        return

    print("\nAvvio del browser in background (headless)...")
    driver = inizializza_driver()
    
    if driver is None:
        sys.exit(1)

    print("Browser avviato. Inizio analisi...")
    
    trovati = 0
    non_trovati = 0
    
    for url in urls:
        print("-" * 30)
        print(f"Analisi: {url}")
        
        if controlla_url_con_selenium(driver, url):
            trovati += 1
        else:
            non_trovati += 1

    driver.quit()

    print("\n" + "=" * 30)
    print("--- ANALISI COMPLETATA ---")
    print(f"Siti con link Trasparenza: {trovati}")
    print(f"Siti senza link / Errori:   {non_trovati}")
    print("=" * 30)

if __name__ == "__main__":
    main()