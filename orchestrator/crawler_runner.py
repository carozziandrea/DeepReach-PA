"""
Crawler Runner - Lancia i crawler Scrapy come subprocess.

Questo modulo gestisce l'esecuzione dei crawl shallow e deep.
"""

import subprocess
import time
import os
from pathlib import Path
from typing import Optional, Tuple

from config import OrchestratorConfig, default_config
from models import CrawlInfo


class CrawlerRunner:
    """
    Gestisce l'esecuzione dei crawler Scrapy.
    """

    def __init__(self, config: OrchestratorConfig = None, crawler_dir: Path = None):
        """
        Inizializza il runner.

        Args:
            config: Configurazione
            crawler_dir: Directory root del progetto Scrapy (dove c'è scrapy.cfg)
        """
        self.config = config or default_config

        if crawler_dir:
            self.crawler_dir = Path(crawler_dir).resolve()
        else:
            # Default: risali di una directory da orchestrator/ alla root del progetto
            self.crawler_dir = Path(__file__).resolve().parent.parent

        # Verifica che la directory esista e contenga scrapy.cfg
        if not self.crawler_dir.exists():
            print(f"[WARN] ATTENZIONE: Directory crawler non trovata: {self.crawler_dir}")
        elif not (self.crawler_dir / "scrapy.cfg").exists():
            print(f"[WARN] ATTENZIONE: scrapy.cfg non trovato in: {self.crawler_dir}")
        else:
            print(f"[INFO] Crawler directory: {self.crawler_dir}")

        # Directory dove il spider salva l'output (output/ nella root)
        self.spider_output_dir = self.crawler_dir / "output"

    def cleanup_output_files(self, output_names: list = None) -> None:
        """
        Rimuove i file di output esistenti per evitare dati stale.

        Args:
            output_names: Lista di nomi file da rimuovere (senza .json).
                         Se None, rimuove tutti i file di output standard.
        """
        if output_names is None:
            output_names = [
                self.config.crawl.deep_output_name,
                self.config.crawl.shallow_output_name
            ]

        for output_name in output_names:
            # Pulisci sia dalla directory del spider che dalla directory config
            paths_to_clean = [
                self.spider_output_dir / f"{output_name}.json",
                self.config.crawl.output_dir / f"{output_name}.json",
            ]

            for file_path in paths_to_clean:
                if file_path.exists():
                    try:
                        os.remove(file_path)
                        print(f"[CLEANUP] Rimosso file esistente: {file_path}")
                    except OSError as e:
                        print(f"[WARN] Impossibile rimuovere {file_path}: {e}")

    def _run_scrapy(
        self,
        start_url: str,
        mode: str,
        max_depth: int,
        output_name: str,
        concurrent_requests: int = 4,
        download_delay: float = 0.5,
        output_dir: Optional[Path] = None
    ) -> Tuple[bool, float, str]:
        """
        Esegue scrapy crawl come subprocess.

        Args:
            start_url: URL di partenza
            mode: 'deep' o 'shallow'
            max_depth: Profondità massima
            output_name: Nome file output (senza .json)
            concurrent_requests: Numero di richieste parallele per dominio
            download_delay: Pausa tra richieste (secondi)
            output_dir: Directory di output per i file JSON (opzionale)

        Returns:
            Tupla (success, duration_seconds, error_message)
        """
        cmd = [
            "scrapy", "crawl", self.config.crawl.spider_name,
            "-a", f"start_url={start_url}",
            "-a", f"mode={mode}",
            "-a", f"max_depth={max_depth}",
            "-a", f"output_name={output_name}",
            "-s", "LOG_LEVEL=INFO",  # Mostra progressi senza troppi dettagli
            "-s", f"CONCURRENT_REQUESTS_PER_DOMAIN={concurrent_requests}",
            "-s", f"DOWNLOAD_DELAY={download_delay}",
        ]

        # Aggiungi output_dir se specificata
        if output_dir:
            cmd.extend(["-a", f"output_dir={output_dir}"])

        start_time = time.time()

        # Converti path in stringa assoluta (importante per Windows)
        cwd_path = str(self.crawler_dir.resolve())

        print(f"\n   [RUN] Esecuzione: scrapy crawl {self.config.crawl.spider_name}")
        print(f"   [DIR] Directory: {cwd_path}")
        print("-" * 50)

        # Timeout in secondi (86400 = 24 ore)
        crawl_timeout = 86400

        try:
            # NON catturiamo l'output, così viene mostrato in tempo reale
            result = subprocess.run(
                cmd,
                cwd=cwd_path,
                timeout=crawl_timeout,
                shell=False
                # Senza capture_output, l'output va direttamente al terminale
            )

            print("-" * 50)
            duration = time.time() - start_time

            if result.returncode == 0:
                return True, duration, ""
            else:
                return False, duration, f"Scrapy terminato con codice {result.returncode}"

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            timeout_hours = crawl_timeout / 3600
            return False, duration, f"Timeout: crawl non completato in {timeout_hours:.0f} ore"

        except FileNotFoundError:
            return False, 0, "Scrapy non trovato. Assicurati che sia installato e nel PATH."

        except OSError as e:
            # Errore tipico di Windows quando la directory non è valida
            return False, 0, f"Errore directory: {e}. Verifica che '{cwd_path}' esista e contenga scrapy.cfg"

        except Exception as e:
            duration = time.time() - start_time
            return False, duration, f"Errore: {e}"

    def run_shallow(self, homepage_url: str, thorough: bool = False) -> CrawlInfo:
        """
        Esegue il crawl shallow (homepage, profondità bassa, include nav).

        Args:
            homepage_url: URL della homepage
            thorough: Se True, usa parametri più approfonditi (più lento)

        Returns:
            CrawlInfo con i risultati
        """
        output_name = self.config.crawl.shallow_output_name

        # Scegli parametri in base a modalità
        if thorough:
            max_depth = self.config.crawl.thorough_shallow_depth
            concurrent = self.config.crawl.thorough_concurrent
            delay = self.config.crawl.thorough_delay
            mode_label = "SHALLOW (thorough)"
        else:
            max_depth = self.config.crawl.shallow_max_depth
            concurrent = 4
            delay = 0.5
            mode_label = "SHALLOW"

        # Cleanup file esistenti per evitare dati stale
        self.cleanup_output_files([output_name])

        print(f"\n[CRAWL] Avvio crawl {mode_label}")
        print(f"   URL: {homepage_url}")
        print(f"   Profondita: {max_depth}")
        print(f"   Concorrenza: {concurrent} | Delay: {delay}s")
        print(f"   Output: {output_name}.json")

        success, duration, error = self._run_scrapy(
            start_url=homepage_url,
            mode="shallow",
            max_depth=max_depth,
            output_name=output_name,
            concurrent_requests=concurrent,
            download_delay=delay,
            output_dir=self.config.crawl.output_dir,
        )

        info = CrawlInfo(
            mode="shallow",
            start_url=homepage_url,
            output_file=f"{output_name}.json",
            success=success,
            duration_seconds=duration,
            error_message=error if not success else None
        )

        if success:
            # Conta pagine dal file JSON
            info.total_pages = self._count_pages(output_name)
            print(f"   [OK] Completato in {duration:.1f}s - {info.total_pages} pagine")
        else:
            print(f"   [ERROR] Fallito: {error}")

        return info

    def run_deep(self, at_url: str, thorough: bool = False) -> CrawlInfo:
        """
        Esegue il crawl deep (sezione AT, profondità alta, esclude nav).

        Args:
            at_url: URL della sezione Amministrazione Trasparente
            thorough: Se True, usa parametri più approfonditi (più lento)

        Returns:
            CrawlInfo con i risultati
        """
        output_name = self.config.crawl.deep_output_name

        # Scegli parametri in base a modalità
        if thorough:
            max_depth = self.config.crawl.thorough_deep_depth
            concurrent = self.config.crawl.thorough_concurrent
            delay = self.config.crawl.thorough_delay
            mode_label = "DEEP (thorough)"
        else:
            max_depth = self.config.crawl.deep_max_depth
            concurrent = 4
            delay = 0.5
            mode_label = "DEEP"

        # Cleanup file esistenti per evitare dati stale
        self.cleanup_output_files([output_name])

        print(f"\n[CRAWL] Avvio crawl {mode_label}")
        print(f"   URL: {at_url}")
        print(f"   Profondita: {max_depth}")
        print(f"   Concorrenza: {concurrent} | Delay: {delay}s")
        print(f"   Output: {output_name}.json")

        success, duration, error = self._run_scrapy(
            start_url=at_url,
            mode="deep",
            max_depth=max_depth,
            output_name=output_name,
            concurrent_requests=concurrent,
            download_delay=delay,
            output_dir=self.config.crawl.output_dir,
        )

        info = CrawlInfo(
            mode="deep",
            start_url=at_url,
            output_file=f"{output_name}.json",
            success=success,
            duration_seconds=duration,
            error_message=error if not success else None
        )

        if success:
            info.total_pages = self._count_pages(output_name)
            print(f"   [OK] Completato in {duration:.1f}s - {info.total_pages} pagine")
        else:
            print(f"   [ERROR] Fallito: {error}")

        return info

    def _count_pages(self, output_name: str) -> int:
        """Conta le pagine nel file JSON di output."""
        import json

        # Usa la directory configurata (può essere site-specific in batch mode)
        output_path = self.config.crawl.output_dir / f"{output_name}.json"

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('stats', {}).get('total_pages', 0)
        except Exception:
            return 0

    def run_both(self, homepage_url: str, at_url: str) -> Tuple[CrawlInfo, CrawlInfo]:
        """
        Esegue entrambi i crawl in sequenza.

        Args:
            homepage_url: URL della homepage
            at_url: URL della sezione AT

        Returns:
            Tupla (shallow_info, deep_info)
        """
        shallow_info = self.run_shallow(homepage_url)
        deep_info = self.run_deep(at_url)

        return shallow_info, deep_info


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python crawler_runner.py <homepage_url> <at_url>")
        sys.exit(1)

    homepage = sys.argv[1]
    at = sys.argv[2]

    runner = CrawlerRunner()
    shallow, deep = runner.run_both(homepage, at)

    print(f"\nRisultati:")
    print(f"  Shallow: {'[OK]' if shallow.success else '[FAIL]'} - {shallow.total_pages} pagine")
    print(f"  Deep: {'[OK]' if deep.success else '[FAIL]'} - {deep.total_pages} pagine")
