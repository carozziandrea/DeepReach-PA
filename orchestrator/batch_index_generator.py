"""
Batch Index Generator - Genera pagina indice HTML per risultati batch.

Crea un index.html navigabile con:
- Lista siti analizzati
- Score e rating per ogni sito
- Link ai grafici di ogni sito
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent))

from models import BatchResult
from utils import extract_domain


class BatchIndexGenerator:
    """Genera pagina indice HTML per navigare i risultati batch."""

    def __init__(self, output_dir: Path = None):
        """
        Inizializza il generatore.

        Args:
            output_dir: Directory di output (default: ./output)
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./output")

    def generate_index(
        self,
        batch_result: BatchResult,
        filename: str = "index.html"
    ) -> Optional[str]:
        """
        Genera la pagina indice HTML.

        Args:
            batch_result: Risultato dell'analisi batch
            filename: Nome del file di output

        Returns:
            Path al file generato, o None se errore
        """
        output_path = self.output_dir / filename

        try:
            html_content = self._generate_html(batch_result)

            # Assicura che la cartella di output esista
            self.output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"[INDEX] Pagina indice generata: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"[ERROR] Errore generazione indice: {e}")
            return None

    def _generate_html(self, batch_result: BatchResult) -> str:
        """Genera il contenuto HTML."""
        timestamp = batch_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # Genera righe tabella per ogni sito
        rows_html = self._generate_table_rows(batch_result)

        # Genera righe per siti falliti
        failed_html = self._generate_failed_rows(batch_result)

        html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepReach-PA - Risultati Batch</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --gray: #6b7280;
            --light: #f3f4f6;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--light);
            color: #1f2937;
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}

        h1 {{
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}

        .subtitle {{
            color: var(--gray);
            font-size: 0.9rem;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}

        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
        }}

        .stat-label {{
            color: var(--gray);
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}

        .stat-card.success .stat-value {{ color: var(--success); }}
        .stat-card.warning .stat-value {{ color: var(--warning); }}
        .stat-card.danger .stat-value {{ color: var(--danger); }}

        table {{
            width: 100%;
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-collapse: collapse;
            overflow: hidden;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--light);
        }}

        th {{
            background: var(--primary);
            color: white;
            font-weight: 600;
        }}

        tr:hover {{
            background: #f9fafb;
        }}

        .score {{
            font-weight: bold;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}

        .score.ottimo {{ background: #dcfce7; color: #166534; }}
        .score.buono {{ background: #dbeafe; color: #1e40af; }}
        .score.sufficiente {{ background: #fef9c3; color: #854d0e; }}
        .score.insufficiente {{ background: #fed7aa; color: #9a3412; }}
        .score.critico {{ background: #fee2e2; color: #991b1b; }}
        .score.na {{ background: var(--light); color: var(--gray); }}

        .links a {{
            display: inline-block;
            padding: 0.35rem 0.75rem;
            background: var(--primary);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.85rem;
            margin-right: 0.5rem;
            margin-bottom: 0.25rem;
            transition: background 0.2s;
        }}

        .links a:hover {{
            background: #1d4ed8;
        }}

        .links a.secondary {{
            background: var(--gray);
        }}

        .links a.secondary:hover {{
            background: #4b5563;
        }}

        .failed-section {{
            margin-top: 2rem;
        }}

        .failed-section h2 {{
            color: var(--danger);
            margin-bottom: 1rem;
        }}

        .error-text {{
            color: var(--danger);
            font-size: 0.85rem;
        }}

        footer {{
            text-align: center;
            margin-top: 2rem;
            color: var(--gray);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DeepReach-PA</h1>
            <p class="subtitle">Report Analisi Batch - {timestamp}</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{batch_result.total_sites}</div>
                <div class="stat-label">Siti Totali</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{batch_result.successful}</div>
                <div class="stat-label">Completati</div>
            </div>
            <div class="stat-card danger">
                <div class="stat-value">{batch_result.failed}</div>
                <div class="stat-label">Falliti</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{batch_result.avg_usability_score:.1f}</div>
                <div class="stat-label">Score Medio</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Sito</th>
                    <th>Score</th>
                    <th>AT Coverage</th>
                    <th>Trasparenza Sommersa</th>
                    <th>Grafici</th>
                </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
        </table>

{failed_html}

        <footer>
            <p>Generato da DeepReach-PA Batch Analyzer</p>
        </footer>
    </div>
</body>
</html>'''
        return html

    def _generate_table_rows(self, batch_result: BatchResult) -> str:
        """Genera le righe della tabella per i siti analizzati."""
        rows = []

        for i, ranking in enumerate(batch_result.ranking, 1):
            domain = extract_domain(ranking.url)
            score_class = self._get_score_class(ranking.rating)
            hidden_text = f"Si ({ranking.hidden_sections_count})" if ranking.has_hidden_transparency else "No"

            row = f'''                <tr>
                    <td>{i}</td>
                    <td>
                        <strong>{domain}</strong><br>
                        <small style="color: var(--gray);">{ranking.url}</small>
                    </td>
                    <td><span class="score {score_class}">{ranking.usability_score:.1f}/100</span></td>
                    <td>{ranking.at_coverage_percent:.1f}%</td>
                    <td>{hidden_text}</td>
                    <td class="links">
                        <a href="{domain}/deep_graph.html" target="_blank">Grafo AT</a>
                        <a href="{domain}/analysis_report.pdf" class="secondary" target="_blank">Report PDF</a>
                        <a href="{domain}/privacy_report.pdf" class="secondary" target="_blank">Privacy PDF</a>
                        <a href="{domain}/analysis_report.json" class="secondary" target="_blank">JSON</a>
                    </td>
                </tr>'''
            rows.append(row)

        return '\n'.join(rows)

    def _generate_failed_rows(self, batch_result: BatchResult) -> str:
        """Genera la sezione per i siti falliti."""
        if not batch_result.failed_sites:
            return ""

        rows = []
        for site in batch_result.failed_sites:
            domain = extract_domain(site.get('url', ''))
            error = site.get('error', 'Errore sconosciuto')
            rows.append(f'''                <tr>
                    <td>{domain}</td>
                    <td class="error-text">{error}</td>
                </tr>''')

        return f'''
        <div class="failed-section">
            <h2>Siti Falliti</h2>
            <table>
                <thead>
                    <tr>
                        <th>Sito</th>
                        <th>Errore</th>
                    </tr>
                </thead>
                <tbody>
{chr(10).join(rows)}
                </tbody>
            </table>
        </div>'''

    def _get_score_class(self, rating: str) -> str:
        """Restituisce la classe CSS per il rating."""
        rating_map = {
            "Ottimo": "ottimo",
            "Buono": "buono",
            "Sufficiente": "sufficiente",
            "Insufficiente": "insufficiente",
            "Critico": "critico",
        }
        return rating_map.get(rating, "na")


def generate_batch_index(
    batch_result: BatchResult,
    output_dir: Path = None,
    filename: str = "index.html"
) -> Optional[str]:
    """
    Funzione di convenienza per generare l'indice batch.

    Args:
        batch_result: Risultato dell'analisi batch
        output_dir: Directory di output
        filename: Nome del file

    Returns:
        Path al file generato
    """
    generator = BatchIndexGenerator(output_dir)
    return generator.generate_index(batch_result, filename)
