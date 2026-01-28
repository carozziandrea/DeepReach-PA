"""
Console Reporter - Output formattato su console.

Stampa un report leggibile con emoji e formattazione.
"""

from typing import Optional

from models import AnalysisResult
from reporters.base_reporter import BaseReporter


class ConsoleReporter(BaseReporter):
    """Reporter per output su console."""
    
    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> None:
        """Stampa il report su console."""

        self._print_header(result)
        self._print_crawl_info(result)

        if result.at_found:
            self._print_reachability(result)
            self._print_quality(result)
            self._print_transparency(result)
            self._print_usability(result)

        # Privacy section (shown even if AT not found)
        self._print_privacy(result)

        self._print_footer()
    
    def _print_header(self, result: AnalysisResult) -> None:
        """Stampa l'intestazione del report."""
        print("\n" + "=" * 70)
        print("[REPORT] REPORT ANALISI TRASPARENZA PA")
        print("=" * 70)
        print(f"[DATA] Data: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[HOME] Homepage: {result.homepage_url}")
        
        if result.at_found:
            print(f"[OK] Sezione AT trovata: {result.at_url}")
        else:
            print("[X] Sezione Amministrazione Trasparente NON trovata")
    
    def _print_crawl_info(self, result: AnalysisResult) -> None:
        """Stampa info sui crawl."""
        print("\n" + "-" * 40)
        print("[CRAWL]  CRAWL ESEGUITI")
        print("-" * 40)
        
        if result.crawl_shallow:
            c = result.crawl_shallow
            status = "[OK]" if c.success else "[X]"
            print(f"   Shallow: {status} {c.total_pages} pagine ({c.duration_seconds:.1f}s)")
        
        if result.crawl_deep:
            c = result.crawl_deep
            status = "[OK]" if c.success else "[X]"
            print(f"   Deep:    {status} {c.total_pages} pagine ({c.duration_seconds:.1f}s)")
    
    def _print_reachability(self, result: AnalysisResult) -> None:
        """Stampa metriche di raggiungibilità."""
        print("\n" + "-" * 40)
        print("[REACH] RAGGIUNGIBILITÀ (Sezione AT)")
        print("-" * 40)
        
        if result.reachability_at:
            r = result.reachability_at
            print(f"   Pagine totali:     {r.total_pages}")
            print(f"   File (PDF, etc.):  {r.total_files}")
            print(f"   Profondità media:  {r.avg_depth:.2f} click")
            print(f"   Profondità max:    {r.max_depth} click")
            print(f"\n   Distribuzione:")
            print(f"      Livello 1: {r.pages_at_depth_1} pagine")
            print(f"      Livello 2: {r.pages_at_depth_2} pagine")
            print(f"      Livello 3+: {r.pages_at_depth_3_plus} pagine")
    
    def _print_quality(self, result: AnalysisResult) -> None:
        """Stampa metriche di qualità."""
        print("\n" + "-" * 40)
        print("[QUALITY] QUALITÀ STRUTTURALE")
        print("-" * 40)
        
        if result.quality_at:
            q = result.quality_at
            print(f"   Sezione AT:")
            print(f"      Pagine OK:      {q.pages_ok}")
            print(f"      Link rotti:     {q.pages_broken} ({q.broken_percent:.1f}%)")
            print(f"      Non visitate:   {q.pages_not_visited}")
            
            if q.broken_urls:
                print(f"\n   [!]  Link rotti (primi 5):")
                for url in q.broken_urls[:5]:
                    print(f"      - {url[:60]}...")
        
        if result.quality_main:
            q = result.quality_main
            print(f"\n   Homepage/Main:")
            print(f"      Pagine OK:      {q.pages_ok}")
            print(f"      Link rotti:     {q.pages_broken} ({q.broken_percent:.1f}%)")
    
    def _print_transparency(self, result: AnalysisResult) -> None:
        """Stampa analisi trasparenza sommersa."""
        print("\n" + "-" * 40)
        print("[TRASP] ANALISI TRASPARENZA")
        print("-" * 40)
        
        if result.transparency:
            t = result.transparency
            print(f"   Sezioni obbligatorie: {t.total_required_sections}")
            print(f"   Presenti in AT:       {t.sections_in_at} ({t.at_coverage_percent:.1f}%)")
            print(f"   Solo fuori da AT:     {t.sections_only_in_main} (trasparenza sommersa)")
            print(f"   Mancanti:             {t.sections_missing}")
            
            if t.hidden_sections:
                print(f"\n   [!]  TRASPARENZA SOMMERSA (sezioni fuori da AT):")
                for section in t.hidden_sections:
                    print(f"      - {section}")
            
            if t.missing_sections:
                print(f"\n   [X] SEZIONI MANCANTI:")
                for section in t.missing_sections:
                    print(f"      - {section}")
            
            if t.all_sections_in_at:
                print(f"\n   [OK] Tutte le sezioni obbligatorie sono in AT!")
    
    def _print_usability(self, result: AnalysisResult) -> None:
        """Stampa indice di usabilità."""
        print("\n" + "-" * 40)
        print("[INDEX] INDICE DI USABILITÀ")
        print("-" * 40)
        
        if result.usability_index:
            u = result.usability_index
            
            # Barra visiva
            bar_length = 30
            filled = int(u.score / 100 * bar_length)
            bar = "#" * filled + "-" * (bar_length - filled)
            
            print(f"\n   [{bar}] {u.score:.1f}/100")
            print(f"\n   Giudizio: {u.rating}")
            
            print(f"\n   Dettaglio calcolo:")
            print(f"      Base:                    {u.base_score:+.1f}")
            print(f"      Penalità profondità:     {-u.depth_penalty:+.1f}")
            print(f"      Penalità link rotti:     {-u.broken_penalty:+.1f}")
            print(f"      Penalità trasp. sommersa:{-u.hidden_penalty:+.1f}")
            print(f"      Bonus completezza:       {u.bonus:+.1f}")
            print(f"      -----------------------------")
            print(f"      TOTALE:                  {u.score:.1f}")
    
    def _print_privacy(self, result: AnalysisResult) -> None:
        """Stampa analisi privacy."""
        print("\n" + "-" * 40)
        print("[PRIVACY] ANALISI PRIVACY")
        print("-" * 40)

        if not result.privacy:
            print("   Analisi privacy non eseguita o disabilitata.")
            return

        p = result.privacy

        print(f"   Nodi analizzati:   {p.total_scanned}")
        print(f"      Pagine HTML:    {p.pages_scanned}")
        print(f"      File (PDF...):  {p.files_scanned}")

        print(f"\n   Distribuzione rischio:")
        print(f"      [HIGH] ALTO:   {p.high_risk_count} nodi")
        print(f"      [MED] MEDIO:  {p.medium_risk_count} nodi")
        print(f"      [LOW] BASSO:  {p.low_risk_count} nodi")

        if p.findings_by_type:
            print(f"\n   Tipi di dati sensibili trovati:")
            pattern_labels = {
                "codice_fiscale": "Codici Fiscali",
                "iban": "IBAN",
                "email": "Email",
                "telefono": "Telefoni",
                "indirizzo": "Indirizzi",
            }
            for pattern, count in p.findings_by_type.items():
                label = pattern_labels.get(pattern, pattern)
                print(f"      - {label}: {count}")

        if p.high_risk_urls:
            print(f"\n   [!]  URL ad alto rischio (primi 5):")
            for url in p.high_risk_urls[:5]:
                # Tronca URL lunghi
                display_url = url if len(url) < 55 else url[:52] + "..."
                print(f"      - {display_url}")

        # Mostra errori di scansione se presenti
        if p.scan_errors:
            print(f"\n   [X] Errori durante la scansione ({len(p.scan_errors)}):")
            for error in p.scan_errors[:5]:
                # Tronca errori lunghi
                display_error = error if len(error) < 70 else error[:67] + "..."
                print(f"      - {display_error}")
            if len(p.scan_errors) > 5:
                print(f"      ... e altri {len(p.scan_errors) - 5} errori")

    def _print_footer(self) -> None:
        """Stampa il footer del report."""
        print("\n" + "-" * 40)
        print("[FILES] REPORT SALVATI")
        print("-" * 40)
        print("   I report dettagliati sono disponibili in:")
        print("      - output/analysis_report.txt")
        print("      - output/analysis_report.pdf")
        print("      - output/privacy_report.txt")
        print("      - output/privacy_report.pdf")
        print("\n" + "=" * 70)
        print("Fine report")
        print("=" * 70 + "\n")
