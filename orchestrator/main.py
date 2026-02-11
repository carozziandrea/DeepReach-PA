#!/usr/bin/env python3
"""
DeepReach-PA Orchestrator

Script principale che orchestra l'intero processo di analisi:
1. Trova il link Amministrazione Trasparente nella homepage
2. Esegue i crawl (shallow + deep)
3. Analizza i risultati
4. Genera il report

Uso:
    python main.py <homepage_url>
    python main.py https://comune.esempio.it/

Opzioni:
    --skip-crawl    Salta i crawl e analizza solo i JSON esistenti
    --shallow-only  Esegue solo il crawl shallow
    --deep-only     Esegue solo il crawl deep (richiede URL AT)
    --output-dir    Directory per l'output (default: ./output)
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Aggiungi la directory corrente al path per gli import
sys.path.insert(0, str(Path(__file__).parent))

from config import OrchestratorConfig, default_config
from homepage_checker import HomepageChecker
from crawler_runner import CrawlerRunner
from analyzer import Analyzer
from models import AnalysisResult, CrawlInfo
from reporters import (
    ConsoleReporter,
    JsonReporter,
    generate_privacy_reports,
    generate_full_reports,
    generate_batch_reports,
)
from visualizer import Visualizer
from batch_runner import BatchRunner
from utils import extract_domain, ensure_directory, get_site_output_dir


class Orchestrator:
    """
    Orchestratore principale del processo di analisi.
    """

    def __init__(self, config: OrchestratorConfig = None, crawler_dir: Path = None):
        """
        Inizializza l'orchestratore.

        Args:
            config: Configurazione (usa default se non specificata)
            crawler_dir: Directory dove si trova il crawler
        """
        self.config = config or default_config
        self.crawler_dir = crawler_dir or Path(__file__).parent.parent

        # Componenti
        self.homepage_checker = HomepageChecker(self.config)
        self.crawler_runner = CrawlerRunner(self.config, self.crawler_dir)
        self.analyzer = Analyzer(self.config)
        self.visualizer = Visualizer(self.config.crawl.output_dir)

        # Reporter
        self.reporters = [
            ConsoleReporter(self.config.report_output_dir),
            JsonReporter(self.config.report_output_dir),
        ]

    def _load_crawl_info_from_json(
        self,
        output_name: str,
        start_url: str,
        mode: str
    ) -> CrawlInfo:
        """
        Carica CrawlInfo da un file JSON esistente.

        Usato quando --skip-crawl per avere stats reali invece di valori dummy.
        """
        import json

        json_path = self.config.crawl.output_dir / f"{output_name}.json"

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            stats = data.get('stats', {})

            return CrawlInfo(
                mode=mode,
                start_url=start_url,
                output_file=f"{output_name}.json",
                success=True,
                total_pages=stats.get('total_pages', 0),
                duration_seconds=0.0,  # Non disponibile nel JSON
            )
        except FileNotFoundError:
            print(f"[WARN] File non trovato: {json_path}")
            return CrawlInfo(
                mode=mode,
                start_url=start_url,
                output_file=f"{output_name}.json",
                success=False,
                error_message=f"File non trovato: {json_path}",
            )
        except Exception as e:
            print(f"[WARN] Errore lettura {json_path}: {e}")
            return CrawlInfo(
                mode=mode,
                start_url=start_url,
                output_file=f"{output_name}.json",
                success=False,
                error_message=str(e),
            )

    def run(
        self,
        homepage_url: str,
        skip_crawl: bool = False,
        shallow_only: bool = False,
        deep_only: bool = False,
        at_url_override: Optional[str] = None,
        thorough: bool = False,
        site_output_dir: Optional[Path] = None
    ) -> AnalysisResult:
        """
        Esegue l'intero processo di analisi.

        Args:
            homepage_url: URL della homepage del sito PA
            skip_crawl: Se True, salta i crawl e usa JSON esistenti
            shallow_only: Se True, esegue solo crawl shallow
            deep_only: Se True, esegue solo crawl deep
            at_url_override: URL AT manuale (salta la ricerca automatica)
            thorough: Se True, usa analisi approfondita
            site_output_dir: Directory di output specifica per questo sito

        Returns:
            AnalysisResult con i risultati dell'analisi
        """
        print("\n" + "=" * 70)
        print("DeepReach-PA - Analisi Trasparenza PA")
        print("=" * 70)

        # Se specificata una directory per sito, usala per output
        if site_output_dir:
            site_output_dir = Path(site_output_dir)
            ensure_directory(site_output_dir)
            # Aggiorna temporaneamente le directory di output
            original_crawl_output = self.config.crawl.output_dir
            original_report_output = self.config.report_output_dir
            self.config.crawl.output_dir = site_output_dir
            self.config.report_output_dir = site_output_dir
            # Ricrea i componenti con le nuove directory
            self.crawler_runner = CrawlerRunner(self.config, self.crawler_dir)
            self.visualizer = Visualizer(site_output_dir)
            self.reporters = [
                ConsoleReporter(site_output_dir),
                JsonReporter(site_output_dir),
            ]
            # Ricrea anche l'analyzer con la nuova configurazione
            self.analyzer = Analyzer(self.config)
            print(f"[OUTPUT] Directory: {site_output_dir}")

        # Normalizza URL
        if not homepage_url.startswith('http'):
            homepage_url = 'https://' + homepage_url

        at_url = at_url_override
        crawl_shallow = None
        crawl_deep = None

        # Step 1: Trova link AT (se non fornito)
        # Cerca SEMPRE AT, anche in shallow-only (per info nel report)
        if not at_url:
            print(f"\n[SEARCH] Ricerca sezione Amministrazione Trasparente...")
            print(f"   Homepage: {homepage_url}")

            found, at_url, message = self.homepage_checker.find_at_link(homepage_url)
            print(f"   {message}")
            if found:
                print(f"   URL AT: {at_url}")

            if not found and not shallow_only:
                # In modalita' completa, AT e' obbligatorio
                print("\n[ERROR] Impossibile trovare la sezione AT.")
                print("   Opzioni:")
                print("   1. Specifica l'URL AT manualmente con --at-url")
                print("   2. Esegui solo il crawl shallow con --shallow-only")

                # Crea risultato vuoto
                result = AnalysisResult(
                    homepage_url=homepage_url,
                    at_url=None,
                    at_found=False,
                )
                self._generate_reports(result)
                # Ripristina configurazione se necessario
                if site_output_dir:
                    self.config.crawl.output_dir = original_crawl_output
                    self.config.report_output_dir = original_report_output
                return result
            elif not found and shallow_only:
                # In shallow-only, AT non trovato non e' un errore fatale
                print("\n[WARN] Sezione AT non trovata, continuo con solo shallow crawl")

        # Step 2: Esegui crawl
        if not skip_crawl:
            if not deep_only:
                # Crawl shallow
                crawl_shallow = self.crawler_runner.run_shallow(homepage_url, thorough=thorough)

            if at_url and not shallow_only:
                # Crawl deep
                crawl_deep = self.crawler_runner.run_deep(at_url, thorough=thorough)
        else:
            print("\n[SKIP] Skip crawl - uso JSON esistenti")
            # Leggi stats dai JSON esistenti
            crawl_shallow = self._load_crawl_info_from_json(
                self.config.crawl.shallow_output_name,
                homepage_url,
                "shallow"
            )
            if at_url:
                crawl_deep = self._load_crawl_info_from_json(
                    self.config.crawl.deep_output_name,
                    at_url,
                    "deep"
                )

        # Step 3: Analizza risultati
        print("\n[ANALYSIS] Analisi in corso...")
        result = self.analyzer.analyze(
            homepage_url=homepage_url,
            at_url=at_url,
            crawl_shallow=crawl_shallow,
            crawl_deep=crawl_deep,
        )

        # Step 4: Genera report
        self._generate_reports(result)

        # Ripristina configurazione originale se era stata modificata
        if site_output_dir:
            self.config.crawl.output_dir = original_crawl_output
            self.config.report_output_dir = original_report_output
            # Ripristina componenti originali
            self.crawler_runner = CrawlerRunner(self.config, self.crawler_dir)
            self.visualizer = Visualizer(self.config.crawl.output_dir)
            self.reporters = [
                ConsoleReporter(self.config.report_output_dir),
                JsonReporter(self.config.report_output_dir),
            ]

        return result

    def _generate_reports(self, result: AnalysisResult) -> None:
        """Genera i report usando tutti i reporter configurati."""
        # Report console e JSON standard
        for reporter in self.reporters:
            try:
                reporter.report(result, self.config.report_filename)
            except Exception as e:
                print(f"[WARN] Errore generazione report {type(reporter).__name__}: {e}")

        # Report permanenti (TXT + PDF)
        print("\n" + "-" * 40)
        print("[REPORT] Generazione report permanenti...")
        print("-" * 40)

        try:
            # Determina quale grafo JSON usare per l'immagine PNG
            graph_json_path = None
            if result.crawl_deep and result.crawl_deep.success:
                graph_json_path = str(
                    self.config.crawl.output_dir / f"{self.config.crawl.deep_output_name}.json"
                )
            elif result.crawl_shallow and result.crawl_shallow.success:
                graph_json_path = str(
                    self.config.crawl.output_dir / f"{self.config.crawl.shallow_output_name}.json"
                )

            # Report analisi completa (con grafo PNG se disponibile)
            generate_full_reports(result, self.config.report_output_dir, graph_json_path)
        except Exception as e:
            print(f"[WARN] Errore generazione report analisi: {e}")

        try:
            # Report privacy dettagliato
            if result.privacy:
                generate_privacy_reports(result, self.config.report_output_dir)
        except Exception as e:
            print(f"[WARN] Errore generazione report privacy: {e}")

        # Step 5: Genera visualizzazione grafo
        self._generate_visualization(result)

    def _generate_visualization(self, result: AnalysisResult) -> None:
        """Genera la visualizzazione interattiva del grafo."""
        # Genera grafo per crawl deep (AT) se disponibile
        if result.crawl_deep and result.crawl_deep.success:
            crawl_name = self.config.crawl.deep_output_name
            output_name = "deep"  # visualizer aggiunge "_graph.html" → deep_graph.html
            self.visualizer.generate_for_crawl(crawl_name, output_name)

        # Genera anche grafo per crawl shallow se disponibile
        if result.crawl_shallow and result.crawl_shallow.success:
            crawl_name = self.config.crawl.shallow_output_name
            output_name = "shallow"  # visualizer aggiunge "_graph.html" → shallow_graph.html
            self.visualizer.generate_for_crawl(crawl_name, output_name)

    def add_reporter(self, reporter) -> None:
        """Aggiunge un reporter custom."""
        self.reporters.append(reporter)


def parse_args():
    """Parse degli argomenti da linea di comando."""
    parser = argparse.ArgumentParser(
        description="DeepReach-PA - Analisi trasparenza siti PA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python main.py https://comune.esempio.it/
  python main.py comune.esempio.it --skip-crawl
  python main.py comune.esempio.it --at-url https://comune.esempio.it/amm_trasp/
  python main.py --batch --sites-file ./input/lista_siti.txt
        """
    )

    parser.add_argument(
        "homepage_url",
        nargs="?",  # Opzionale in modalità batch
        default=None,
        help="URL della homepage del sito PA (non richiesto in modalità --batch)"
    )

    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Salta i crawl e analizza i JSON esistenti"
    )

    parser.add_argument(
        "--shallow-only",
        action="store_true",
        help="Esegue solo il crawl shallow (homepage)"
    )

    parser.add_argument(
        "--deep-only",
        action="store_true",
        help="Esegue solo il crawl deep (richiede --at-url)"
    )

    parser.add_argument(
        "--at-url",
        type=str,
        default=None,
        help="URL della sezione AT (salta la ricerca automatica)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Directory per l'output (default: ./output)"
    )

    parser.add_argument(
        "--crawler-dir",
        type=str,
        default=None,
        help="Directory dove si trova sitemap_spider.py"
    )

    # Opzioni modalità batch
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Modalità batch: analizza tutti i siti da un file"
    )

    parser.add_argument(
        "--sites-file",
        type=str,
        default="./input/lista_siti.txt",
        help="File con lista siti, uno per riga (default: ./input/lista_siti.txt)"
    )

    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="In modalità batch, ferma l'esecuzione al primo errore"
    )

    parser.add_argument(
        "--thorough",
        action="store_true",
        help="Analisi approfondita: depth maggiore, crawl più lento (per tesi)"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="In modalità batch, riprende saltando i siti già analizzati"
    )

    parser.add_argument(
        "--limit-pdf",
        type=int,
        default=0,
        help="Limita il numero di PDF da scansionare per sito (0 = nessun limite)"
    )

    return parser.parse_args()


def run_batch_mode(args, config, crawler_dir):
    """
    Esegue l'analisi in modalità batch.

    Args:
        args: Argomenti da linea di comando
        config: Configurazione
        crawler_dir: Directory del crawler

    Returns:
        BatchResult con i risultati
    """
    orchestrator = Orchestrator(config, crawler_dir)
    batch_runner = BatchRunner(orchestrator)

    # Carica siti dal file
    sites_file = Path(args.sites_file)
    if not sites_file.exists():
        print(f"[ERROR] File non trovato: {sites_file}")
        sys.exit(1)

    sites = batch_runner.load_sites(sites_file)

    if not sites:
        print(f"[ERROR] Nessun sito trovato in: {sites_file}")
        sys.exit(1)

    print(f"[INFO] Trovati {len(sites)} siti da analizzare")

    # Esegui batch
    batch_result = batch_runner.run_batch(
        sites=sites,
        continue_on_error=not args.stop_on_error,
        skip_crawl=args.skip_crawl,
        shallow_only=args.shallow_only,
        thorough=args.thorough,
        resume=args.resume,
    )

    # Genera report comparativo
    generate_batch_reports(batch_result, config.report_output_dir)

    return batch_result


def main():
    """Entry point principale."""
    args = parse_args()

    # Configura
    config = OrchestratorConfig()
    # NON sovrascrivere config.crawl.output_dir - deve corrispondere a dove il spider salva
    # Solo il report_output_dir viene configurato dall'utente
    config.report_output_dir = Path(args.output_dir)

    # Limite PDF per sito
    if args.limit_pdf > 0:
        config.privacy.max_pdfs_per_site = args.limit_pdf

    # Crawler directory
    crawler_dir = Path(args.crawler_dir) if args.crawler_dir else None

    # Modalità batch
    if args.batch:
        try:
            batch_result = run_batch_mode(args, config, crawler_dir)

            # Exit code basato sul risultato
            if batch_result.successful > 0:
                sys.exit(0)
            else:
                sys.exit(1)

        except KeyboardInterrupt:
            print("\n\n[WARN] Interrotto dall'utente")
            sys.exit(130)

        except Exception as e:
            print(f"\n[ERROR] ERRORE FATALE: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Modalità singolo sito
    if not args.homepage_url:
        print("[ERROR] Specificare URL del sito o usare --batch")
        print("Uso: python main.py <homepage_url>")
        print("     python main.py --batch --sites-file ./input/lista_siti.txt")
        sys.exit(1)

    # Valida argomenti
    if args.deep_only and not args.at_url:
        print("[ERROR] --deep-only richiede --at-url")
        sys.exit(1)

    # Esegui
    orchestrator = Orchestrator(config, crawler_dir)

    try:
        result = orchestrator.run(
            homepage_url=args.homepage_url,
            skip_crawl=args.skip_crawl,
            shallow_only=args.shallow_only,
            deep_only=args.deep_only,
            at_url_override=args.at_url,
            thorough=args.thorough,
        )

        # Exit code basato sul risultato
        if result.at_found or args.shallow_only:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[WARN] Interrotto dall'utente")
        sys.exit(130)

    except Exception as e:
        print(f"\n[ERROR] ERRORE FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
