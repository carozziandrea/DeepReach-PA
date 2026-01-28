"""
Comparative Reporter - Genera report comparativo per analisi batch.

Produce report TXT e JSON con:
- Classifica dei siti per usability score
- Statistiche aggregate
- Confronto sezioni trasparenza
- Siti con trasparenza sommersa
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import BatchResult


class ComparativeReporter:
    """
    Genera report comparativo per i risultati di un'analisi batch.
    """

    def __init__(self, output_dir: Path = None):
        """
        Inizializza il reporter.

        Args:
            output_dir: Directory per l'output (default: ./output)
        """
        self.output_dir = output_dir or Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def report(
        self,
        batch_result: BatchResult,
        filename: str = "batch_report"
    ) -> None:
        """
        Genera i report comparativi (TXT e JSON).

        Args:
            batch_result: Risultato dell'analisi batch
            filename: Nome base del file (senza estensione)
        """
        # Genera report TXT
        self._generate_txt_report(batch_result, filename)

        # Genera report JSON
        self._generate_json_report(batch_result, filename)

        # Stampa riepilogo su console
        self._print_summary(batch_result)

    def _generate_txt_report(self, batch_result: BatchResult, filename: str) -> None:
        """Genera report in formato TXT."""
        output_path = self.output_dir / f"{filename}.txt"

        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("DEEPREACH-PA - REPORT COMPARATIVO BATCH")
        lines.append("=" * 70)
        lines.append(f"Data: {batch_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Riepilogo
        lines.append("-" * 70)
        lines.append("RIEPILOGO")
        lines.append("-" * 70)
        lines.append(f"Siti totali:      {batch_result.total_sites}")
        lines.append(f"Analisi riuscite: {batch_result.successful}")
        lines.append(f"Analisi fallite:  {batch_result.failed}")
        lines.append("")

        # Statistiche aggregate
        lines.append("-" * 70)
        lines.append("STATISTICHE AGGREGATE")
        lines.append("-" * 70)
        lines.append(f"Usability score medio:    {batch_result.avg_usability_score:.1f}/100")
        lines.append(f"AT coverage medio:        {batch_result.avg_at_coverage:.1f}%")
        lines.append(f"Siti con trasp. sommersa: {batch_result.sites_with_hidden_transparency}")
        lines.append("")

        # Classifica
        lines.append("-" * 70)
        lines.append("CLASSIFICA PER USABILITY SCORE")
        lines.append("-" * 70)

        if batch_result.ranking:
            # Header tabella
            lines.append(f"{'Pos':<4} {'Score':<8} {'Rating':<12} {'AT Cov.':<10} {'Trasp.Som.':<12} URL")
            lines.append("-" * 70)

            for i, r in enumerate(batch_result.ranking, 1):
                hidden_str = f"Si ({r.hidden_sections_count})" if r.has_hidden_transparency else "No"
                lines.append(
                    f"{i:<4} {r.usability_score:<8.1f} {r.rating:<12} "
                    f"{r.at_coverage_percent:<10.1f} {hidden_str:<12} {r.url}"
                )
        else:
            lines.append("Nessun sito analizzato con successo.")

        lines.append("")

        # Siti falliti
        if batch_result.failed_sites:
            lines.append("-" * 70)
            lines.append("SITI FALLITI")
            lines.append("-" * 70)

            for site in batch_result.failed_sites:
                lines.append(f"URL:    {site['url']}")
                lines.append(f"Errore: {site['error']}")
                lines.append("")

        # Footer
        lines.append("=" * 70)
        lines.append("Fine report")
        lines.append("=" * 70)

        # Scrivi file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"[REPORT] TXT salvato in: {output_path}")

    def _generate_json_report(self, batch_result: BatchResult, filename: str) -> None:
        """Genera report in formato JSON."""
        output_path = self.output_dir / f"{filename}.json"

        data = batch_result.to_dict()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[REPORT] JSON salvato in: {output_path}")

    def _print_summary(self, batch_result: BatchResult) -> None:
        """Stampa riepilogo su console."""
        print("\n" + "=" * 70)
        print("RIEPILOGO BATCH")
        print("=" * 70)

        print(f"\nSiti analizzati: {batch_result.successful}/{batch_result.total_sites}")

        if batch_result.failed > 0:
            print(f"Siti falliti: {batch_result.failed}")

        print(f"\nUsability score medio: {batch_result.avg_usability_score:.1f}/100")
        print(f"AT coverage medio: {batch_result.avg_at_coverage:.1f}%")

        if batch_result.sites_with_hidden_transparency > 0:
            print(f"Siti con trasparenza sommersa: {batch_result.sites_with_hidden_transparency}")

        # Top 5 classifica
        if batch_result.ranking:
            print("\n--- TOP 5 CLASSIFICA ---")
            for i, r in enumerate(batch_result.ranking[:5], 1):
                emoji = self._get_rating_emoji(r.rating)
                print(f"{i}. {r.url}")
                print(f"   {emoji} {r.usability_score:.1f}/100 ({r.rating})")

        print("\n" + "=" * 70)

    def _get_rating_emoji(self, rating: str) -> str:
        """Restituisce emoji per il rating (fallback a testo se non supportato)."""
        rating_map = {
            "Ottimo": "[*****]",
            "Buono": "[****-]",
            "Sufficiente": "[***--]",
            "Insufficiente": "[**---]",
            "Critico": "[*----]",
        }
        return rating_map.get(rating, "[-----]")


def generate_batch_reports(
    batch_result: BatchResult,
    output_dir: Path = None,
    filename: str = "batch_report"
) -> None:
    """
    Funzione di convenienza per generare tutti i report batch.

    Args:
        batch_result: Risultato dell'analisi batch
        output_dir: Directory per l'output
        filename: Nome base del file
    """
    reporter = ComparativeReporter(output_dir)
    reporter.report(batch_result, filename)
