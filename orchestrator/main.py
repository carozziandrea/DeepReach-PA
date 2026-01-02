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
)


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
            print(f"⚠️ File non trovato: {json_path}")
            return CrawlInfo(
                mode=mode,
                start_url=start_url,
                output_file=f"{output_name}.json",
                success=False,
                error_message=f"File non trovato: {json_path}",
            )
        except Exception as e:
            print(f"⚠️ Errore lettura {json_path}: {e}")
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
        at_url_override: Optional[str] = None
    ) -> AnalysisResult:
        """
        Esegue l'intero processo di analisi.
        
        Args:
            homepage_url: URL della homepage del sito PA
            skip_crawl: Se True, salta i crawl e usa JSON esistenti
            shallow_only: Se True, esegue solo crawl shallow
            deep_only: Se True, esegue solo crawl deep
            at_url_override: URL AT manuale (salta la ricerca automatica)
        
        Returns:
            AnalysisResult con i risultati dell'analisi
        """
        print("\n" + "=" * 70)
        print("🚀 DeepReach-PA - Analisi Trasparenza PA")
        print("=" * 70)
        
        # Normalizza URL
        if not homepage_url.startswith('http'):
            homepage_url = 'https://' + homepage_url
        
        at_url = at_url_override
        crawl_shallow = None
        crawl_deep = None
        
        # Step 1: Trova link AT (se non fornito)
        if not at_url and not shallow_only:
            print(f"\n🔍 Ricerca sezione Amministrazione Trasparente...")
            print(f"   Homepage: {homepage_url}")
            
            found, at_url, message = self.homepage_checker.find_at_link(homepage_url)
            print(f"   {message}")
            print(f"Url a cui è stato trovato: {at_url}")
            
            if not found:
                print("\n❌ ERRORE: Impossibile trovare la sezione AT.")
                print("   Opzioni:")
                print("   1. Specifica l'URL AT manualmente con --at-url")
                print("   2. Esegui solo il crawl shallow con --shallow-only")
                
                if not shallow_only:
                    # Crea risultato vuoto
                    result = AnalysisResult(
                        homepage_url=homepage_url,
                        at_url=None,
                        at_found=False,
                    )
                    self._generate_reports(result)
                    return result
        
        # Step 2: Esegui crawl
        if not skip_crawl:
            if not deep_only:
                # Crawl shallow
                crawl_shallow = self.crawler_runner.run_shallow(homepage_url)
            
            if at_url and not shallow_only:
                # Crawl deep
                crawl_deep = self.crawler_runner.run_deep(at_url)
        else:
            print("\n⏭️  Skip crawl - uso JSON esistenti")
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
        print("\n📊 Analisi in corso...")
        result = self.analyzer.analyze(
            homepage_url=homepage_url,
            at_url=at_url,
            crawl_shallow=crawl_shallow,
            crawl_deep=crawl_deep,
        )
        
        # Step 4: Genera report
        self._generate_reports(result)
        
        return result
    
    def _generate_reports(self, result: AnalysisResult) -> None:
        """Genera i report usando tutti i reporter configurati."""
        # Report console e JSON standard
        for reporter in self.reporters:
            try:
                reporter.report(result, self.config.report_filename)
            except Exception as e:
                print(f"⚠️ Errore generazione report {type(reporter).__name__}: {e}")

        # Report permanenti (TXT + PDF)
        print("\n" + "-" * 40)
        print("📝 Generazione report permanenti...")
        print("-" * 40)

        try:
            # Report analisi completa
            generate_full_reports(result, self.config.report_output_dir)
        except Exception as e:
            print(f"⚠️ Errore generazione report analisi: {e}")

        try:
            # Report privacy dettagliato
            if result.privacy:
                generate_privacy_reports(result, self.config.report_output_dir)
        except Exception as e:
            print(f"⚠️ Errore generazione report privacy: {e}")
    
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
        """
    )
    
    parser.add_argument(
        "homepage_url",
        help="URL della homepage del sito PA"
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
    
    return parser.parse_args()


def main():
    """Entry point principale."""
    args = parse_args()

    # Configura
    config = OrchestratorConfig()
    # NON sovrascrivere config.crawl.output_dir - deve corrispondere a dove il spider salva
    # Solo il report_output_dir viene configurato dall'utente
    config.report_output_dir = Path(args.output_dir)
    
    # Valida argomenti
    if args.deep_only and not args.at_url:
        print("❌ ERRORE: --deep-only richiede --at-url")
        sys.exit(1)
    
    # Crawler directory
    crawler_dir = Path(args.crawler_dir) if args.crawler_dir else None
    
    # Esegui
    orchestrator = Orchestrator(config, crawler_dir)
    
    try:
        result = orchestrator.run(
            homepage_url=args.homepage_url,
            skip_crawl=args.skip_crawl,
            shallow_only=args.shallow_only,
            deep_only=args.deep_only,
            at_url_override=args.at_url,
        )
        
        # Exit code basato sul risultato
        if result.at_found or args.shallow_only:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrotto dall'utente")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ ERRORE FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
