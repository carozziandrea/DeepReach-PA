"""
Privacy Reporter - Genera report privacy in formato TXT e PDF.

Produce report permanenti con i risultati dell'analisi privacy:
- privacy_report.txt: Report testuale human-readable
- privacy_report.pdf: Report PDF per archiviazione
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

from models import AnalysisResult, PrivacyMetrics
from .base_reporter import BaseReporter


class PrivacyTextReporter(BaseReporter):
    """Genera report privacy in formato testo."""

    def get_file_extension(self) -> str:
        return "txt"

    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> Path:
        """
        Genera il report privacy in formato testo.

        Args:
            result: Risultato dell'analisi completa
            filename: Nome del file (default: privacy_report)

        Returns:
            Path del file generato
        """
        filename = filename or "privacy_report"
        output_path = self.get_output_path(filename)

        # Genera contenuto
        content = self._generate_text_report(result)

        # Salva
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _generate_text_report(self, result: AnalysisResult) -> str:
        """Genera il contenuto del report testuale."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("                    DEEPREACH-PA: PRIVACY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Site: {result.homepage_url}")
        if result.at_url:
            lines.append(f"AT Section: {result.at_url}")
        lines.append("=" * 80)
        lines.append("")

        # Se non ci sono metriche privacy
        if not result.privacy:
            lines.append("Privacy analysis was not performed or no data available.")
            lines.append("")
            lines.append("=" * 80)
            lines.append("                              END OF REPORT")
            lines.append("=" * 80)
            return "\n".join(lines)

        privacy = result.privacy

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total nodes scanned: {privacy.total_scanned}")
        lines.append(f"  - HTML pages: {privacy.pages_scanned}")
        lines.append(f"  - Files (PDF, DOC, etc.): {privacy.files_scanned}")
        lines.append("")

        # Risk distribution
        total = privacy.total_scanned or 1
        lines.append("Privacy Risk Distribution:")
        lines.append(f"  HIGH RISK:   {privacy.high_risk_count} nodes ({privacy.high_risk_count / total * 100:.1f}%)")
        lines.append(f"  MEDIUM RISK: {privacy.medium_risk_count} nodes ({privacy.medium_risk_count / total * 100:.1f}%)")
        lines.append(f"  LOW RISK:    {privacy.low_risk_count} nodes ({privacy.low_risk_count / total * 100:.1f}%)")
        no_risk = total - privacy.high_risk_count - privacy.medium_risk_count - privacy.low_risk_count
        lines.append(f"  NO RISK:     {no_risk} nodes ({no_risk / total * 100:.1f}%)")
        lines.append("")

        # High risk items
        if privacy.high_risk_urls:
            lines.append("=" * 80)
            lines.append("HIGH RISK ITEMS (Detailed)")
            lines.append("=" * 80)
            lines.append("")

            for i, url in enumerate(privacy.high_risk_urls[:50], 1):  # Max 50
                lines.append(f"[{i}] {url}")
                # Get node data if available in raw_data
                node_data = self._get_node_data(result, url)
                if node_data:
                    lines.append(f"    Type: {node_data.get('status', 'page')}")
                    if node_data.get('file_type'):
                        lines.append(f"    File type: {node_data['file_type']}")
                    findings = node_data.get('privacy_findings', [])
                    if findings:
                        lines.append("    Findings:")
                        for finding in findings:
                            pattern = finding.get('type', 'unknown')
                            count = finding.get('count', 0)
                            samples = finding.get('samples', [])
                            lines.append(f"      - {pattern}: {count} occurrences")
                            if samples:
                                lines.append(f"        Samples: {', '.join(samples[:3])}")
                lines.append("")

        # Medium risk items
        if privacy.medium_risk_urls:
            lines.append("=" * 80)
            lines.append("MEDIUM RISK ITEMS")
            lines.append("=" * 80)
            lines.append("")

            for i, url in enumerate(privacy.medium_risk_urls[:30], 1):  # Max 30
                lines.append(f"[{i}] {url}")
                node_data = self._get_node_data(result, url)
                if node_data:
                    findings = node_data.get('privacy_findings', [])
                    if findings:
                        findings_str = ", ".join(
                            f"{f.get('type', '?')}: {f.get('count', 0)}"
                            for f in findings
                        )
                        lines.append(f"    Findings: {findings_str}")
            lines.append("")

        # Findings by pattern type
        if privacy.findings_by_type:
            lines.append("=" * 80)
            lines.append("FINDINGS BY PATTERN TYPE")
            lines.append("=" * 80)
            lines.append("")

            pattern_labels = {
                "codice_fiscale": "Codice Fiscale (Italian Tax Code)",
                "iban": "IBAN",
                "email": "Email",
                "telefono": "Phone",
                "indirizzo": "Address",
            }

            for pattern, count in sorted(privacy.findings_by_type.items(), key=lambda x: -x[1]):
                label = pattern_labels.get(pattern, pattern)
                lines.append(f"{label}: {count} total occurrences")
            lines.append("")

        # Errors if any
        if privacy.scan_errors:
            lines.append("=" * 80)
            lines.append("SCAN ERRORS")
            lines.append("=" * 80)
            lines.append("")
            for error in privacy.scan_errors[:20]:
                lines.append(f"  - {error}")
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("                              END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _get_node_data(self, result: AnalysisResult, url: str) -> Optional[Dict]:
        """Recupera i dati del nodo dal raw_data."""
        for tree_key in ['at', 'main']:
            if tree_key in result.raw_data:
                tree = result.raw_data[tree_key].get('tree', {})
                if url in tree:
                    return tree[url]
        return None


class PrivacyPDFReporter(BaseReporter):
    """Genera report privacy in formato PDF."""

    def get_file_extension(self) -> str:
        return "pdf"

    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> Optional[Path]:
        """
        Genera il report privacy in formato PDF.

        Richiede la libreria reportlab.

        Args:
            result: Risultato dell'analisi completa
            filename: Nome del file (default: privacy_report)

        Returns:
            Path del file generato o None se reportlab non disponibile
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            print("Libreria reportlab non installata. Report PDF non generato.")
            print("Installa con: pip install reportlab")
            return None

        filename = filename or "privacy_report"
        output_path = self.get_output_path(filename)

        # Crea directory se non esiste
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Genera PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        )
        normal_style = styles['Normal']

        # Contenuto
        story = []

        # Titolo
        story.append(Paragraph("DEEPREACH-PA: Privacy Analysis Report", title_style))
        story.append(Spacer(1, 12))

        # Metadata
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Paragraph(f"<b>Site:</b> {result.homepage_url}", normal_style))
        if result.at_url:
            story.append(Paragraph(f"<b>AT Section:</b> {result.at_url}", normal_style))
        story.append(Spacer(1, 20))

        if not result.privacy:
            story.append(Paragraph("Privacy analysis was not performed or no data available.", normal_style))
        else:
            privacy = result.privacy

            # Summary section
            story.append(Paragraph("Summary", heading_style))

            summary_data = [
                ["Total scanned", str(privacy.total_scanned)],
                ["HTML pages", str(privacy.pages_scanned)],
                ["Files (PDF, DOC, etc.)", str(privacy.files_scanned)],
            ]
            summary_table = Table(summary_data, colWidths=[10*cm, 5*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 15))

            # Risk distribution
            story.append(Paragraph("Risk Distribution", heading_style))
            total = privacy.total_scanned or 1
            no_risk = total - privacy.high_risk_count - privacy.medium_risk_count - privacy.low_risk_count

            risk_data = [
                ["Risk Level", "Count", "Percentage"],
                ["HIGH", str(privacy.high_risk_count), f"{privacy.high_risk_count/total*100:.1f}%"],
                ["MEDIUM", str(privacy.medium_risk_count), f"{privacy.medium_risk_count/total*100:.1f}%"],
                ["LOW", str(privacy.low_risk_count), f"{privacy.low_risk_count/total*100:.1f}%"],
                ["NONE", str(no_risk), f"{no_risk/total*100:.1f}%"],
            ]
            risk_table = Table(risk_data, colWidths=[5*cm, 5*cm, 5*cm])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 1), (-1, 1), colors.Color(1, 0.6, 0.6)),  # Light red for HIGH
                ('BACKGROUND', (0, 2), (-1, 2), colors.Color(1, 0.8, 0.6)),  # Light orange for MEDIUM
                ('BACKGROUND', (0, 3), (-1, 3), colors.Color(1, 1, 0.6)),    # Light yellow for LOW
                ('BACKGROUND', (0, 4), (-1, 4), colors.Color(0.8, 1, 0.8)),  # Light green for NONE
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(risk_table)
            story.append(Spacer(1, 15))

            # Findings by type
            if privacy.findings_by_type:
                story.append(Paragraph("Findings by Pattern Type", heading_style))
                findings_data = [["Pattern Type", "Total Occurrences"]]
                pattern_labels = {
                    "codice_fiscale": "Codice Fiscale",
                    "iban": "IBAN",
                    "email": "Email",
                    "telefono": "Phone",
                    "indirizzo": "Address",
                }
                for pattern, count in sorted(privacy.findings_by_type.items(), key=lambda x: -x[1]):
                    label = pattern_labels.get(pattern, pattern)
                    findings_data.append([label, str(count)])

                findings_table = Table(findings_data, colWidths=[10*cm, 5*cm])
                findings_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                story.append(findings_table)
                story.append(Spacer(1, 15))

            # High risk URLs
            if privacy.high_risk_urls:
                story.append(Paragraph("High Risk URLs", heading_style))
                for i, url in enumerate(privacy.high_risk_urls[:20], 1):
                    # Tronca URL lunghi
                    display_url = url if len(url) < 80 else url[:77] + "..."
                    story.append(Paragraph(f"{i}. {display_url}", normal_style))
                if len(privacy.high_risk_urls) > 20:
                    story.append(Paragraph(
                        f"... and {len(privacy.high_risk_urls) - 20} more (see TXT report for full list)",
                        normal_style
                    ))

        # Build PDF
        doc.build(story)

        return output_path


def generate_privacy_reports(result: AnalysisResult, output_dir: Path = None) -> Dict[str, Path]:
    """
    Genera tutti i report privacy (TXT e PDF).

    Args:
        result: Risultato dell'analisi
        output_dir: Directory di output

    Returns:
        Dizionario con i path dei file generati
    """
    output_dir = output_dir or Path("./output")
    generated = {}

    # Report TXT
    txt_reporter = PrivacyTextReporter(output_dir)
    txt_path = txt_reporter.report(result)
    generated['txt'] = txt_path
    print(f"Privacy report (TXT): {txt_path}")

    # Report PDF
    pdf_reporter = PrivacyPDFReporter(output_dir)
    pdf_path = pdf_reporter.report(result)
    if pdf_path:
        generated['pdf'] = pdf_path
        print(f"Privacy report (PDF): {pdf_path}")

    return generated
