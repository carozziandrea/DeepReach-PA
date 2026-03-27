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

        # Remediation suggestions
        if privacy.remediation_suggestions:
            lines.append("=" * 80)
            lines.append("SUGGERIMENTI DI REMEDIATION")
            lines.append("=" * 80)
            lines.append("")
            lines.append("In base ai dati sensibili trovati, si consiglia di:")
            lines.append("")
            for i, suggestion in enumerate(privacy.remediation_suggestions, 1):
                lines.append(f"  [{i}] {suggestion}")
            lines.append("")
            lines.append("Risorse utili:")
            lines.append("  - Garante Privacy: https://www.garanteprivacy.it/faq")
            lines.append("  - ANAC Trasparenza: https://www.anticorruzione.it/trasparenza")
            lines.append("  - Normativa: D.Lgs. 33/2013 (Decreto Trasparenza)")
            lines.append("")
            lines.append("NOTA: Questi suggerimenti non sostituiscono la consulenza del DPO.")
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
    """Genera report privacy in formato PDF con styling professionale."""

    def get_file_extension(self) -> str:
        return "pdf"

    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> Optional[Path]:
        """
        Genera il report privacy in formato PDF con styling professionale.

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
            from reportlab.lib.enums import TA_CENTER
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, Image
            )
        except ImportError:
            print("Libreria reportlab non installata. Report PDF non generato.")
            print("Installa con: pip install reportlab")
            return None

        filename = filename or "privacy_report"
        output_path = self.get_output_path(filename)

        # Crea directory se non esiste
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Colori palette PA
        PA_BLUE = colors.Color(0.145, 0.388, 0.922)  # #2563eb
        PA_RED = colors.Color(0.863, 0.149, 0.149)    # #dc2626
        PA_ORANGE = colors.Color(0.851, 0.467, 0.024) # #d97706
        LIGHT_GRAY = colors.Color(0.95, 0.95, 0.95)

        # Genera PDF con header/footer
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2.5*cm
        )

        # Funzione header/footer
        def add_header_footer(canvas, doc):
            canvas.saveState()
            width, height = A4

            # Header - linea blu
            canvas.setStrokeColor(PA_BLUE)
            canvas.setLineWidth(2)
            canvas.line(2*cm, height - 2*cm, width - 2*cm, height - 2*cm)

            # Header - titolo
            canvas.setFont('Helvetica-Bold', 10)
            canvas.setFillColor(PA_BLUE)
            canvas.drawString(2*cm, height - 1.5*cm, "DeepReach-PA - Report Privacy")

            # Header - data
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.gray)
            canvas.drawRightString(width - 2*cm, height - 1.5*cm,
                                   result.timestamp.strftime('%d/%m/%Y'))

            # Footer - linea
            canvas.setStrokeColor(colors.lightgrey)
            canvas.setLineWidth(0.5)
            canvas.line(2*cm, 2*cm, width - 2*cm, 2*cm)

            # Footer - numero pagina
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.gray)
            canvas.drawCentredString(width / 2, 1.3*cm, f"Pagina {doc.page}")

            # Footer - URL
            canvas.setFont('Helvetica', 7)
            url_display = result.homepage_url[:60] + "..." if len(result.homepage_url) > 60 else result.homepage_url
            canvas.drawString(2*cm, 1.3*cm, url_display)

            canvas.restoreState()

        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=PA_BLUE
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=PA_BLUE,
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        # Contenuto
        story = []

        # Titolo
        story.append(Spacer(1, 15))
        story.append(Paragraph("Report Analisi Privacy", title_style))
        story.append(Spacer(1, 20))

        # Info box
        info_data = [
            ["Sito analizzato:", result.homepage_url],
            ["Sezione AT:", result.at_url if result.at_url else "Non analizzata"],
            ["Data analisi:", result.timestamp.strftime('%d/%m/%Y %H:%M')],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 25))

        if not result.privacy:
            story.append(Paragraph("Analisi privacy non eseguita o dati non disponibili.", normal_style))
        else:
            privacy = result.privacy

            # Summary section
            story.append(Paragraph("Riepilogo Scansione", section_style))

            summary_data = [
                ["Metrica", "Valore"],
                ["Nodi totali analizzati", str(privacy.total_scanned)],
                ["Pagine HTML", str(privacy.pages_scanned)],
                ["File (PDF, DOC, etc.)", str(privacy.files_scanned)],
            ]
            summary_table = Table(summary_data, colWidths=[10*cm, 5*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))

            # Risk distribution with table and chart
            story.append(Paragraph("Distribuzione Rischio Privacy", section_style))
            total = privacy.total_scanned or 1
            no_risk = total - privacy.high_risk_count - privacy.medium_risk_count - privacy.low_risk_count

            risk_data = [
                ["Livello Rischio", "Conteggio", "Percentuale"],
                ["ALTO", str(privacy.high_risk_count), f"{privacy.high_risk_count/total*100:.1f}%"],
                ["MEDIO", str(privacy.medium_risk_count), f"{privacy.medium_risk_count/total*100:.1f}%"],
                ["BASSO", str(privacy.low_risk_count), f"{privacy.low_risk_count/total*100:.1f}%"],
                ["NESSUNO", str(no_risk), f"{no_risk/total*100:.1f}%"],
            ]
            risk_table = Table(risk_data, colWidths=[5*cm, 5*cm, 5*cm])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.92, 0.82, 0.84)),  # Bordeaux chiaro
                ('BACKGROUND', (0, 2), (-1, 2), colors.Color(0.95, 0.88, 0.78)),  # Ambra chiaro
                ('BACKGROUND', (0, 3), (-1, 3), colors.Color(0.85, 0.93, 0.87)),  # Verde salvia chiaro - rischio basso
                ('BACKGROUND', (0, 4), (-1, 4), colors.Color(0.82, 0.89, 0.94)),  # Blu acciaio chiaro - nessun rischio
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(risk_table)
            story.append(Spacer(1, 20))

            # Tipi di dati sensibili trovati (stessa pagina della distribuzione rischio)
            pattern_labels = {
                "codice_fiscale": "Codice Fiscale",
                "iban": "IBAN",
                "email": "Email",
                "telefono": "Telefono",
                "indirizzo": "Indirizzo",
            }
            if privacy.findings_by_type:
                story.append(Paragraph("Tipi di Dati Sensibili Trovati", section_style))
                findings_data = [["Tipo Pattern", "Occorrenze Totali"]]
                for pattern, count in sorted(privacy.findings_by_type.items(), key=lambda x: -x[1]):
                    label = pattern_labels.get(pattern, pattern.capitalize())
                    findings_data.append([label, str(count)])

                findings_table = Table(findings_data, colWidths=[10*cm, 5*cm])
                findings_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ]))
                story.append(findings_table)
                story.append(Spacer(1, 10))

            # Pagina con grafici a barre derivati dalle due tabelle
            story.append(PageBreak())
            story.append(Paragraph("Visualizzazioni Grafiche", section_style))
            story.append(Spacer(1, 15))
            try:
                from .chart_utils import create_privacy_risk_chart, create_findings_chart

                no_risk_chart = total - privacy.high_risk_count - privacy.medium_risk_count - privacy.low_risk_count

                # Grafico 1: distribuzione rischio privacy
                # figsize=(5, 2.5) → ratio 2:1 → 16cm × 8cm
                chart1_buf = create_privacy_risk_chart(
                    privacy.high_risk_count, privacy.medium_risk_count,
                    privacy.low_risk_count, no_risk_chart
                )
                chart1_img = Image(chart1_buf, width=16*cm, height=8*cm)

                if privacy.findings_by_type:
                    # Grafico 2: tipi di dati sensibili (stesso stile di chart1, colore blu PA)
                    # figsize=(5, 2.5) → ratio 2:1 → 16cm × 8cm
                    chart2_buf = create_findings_chart(privacy.findings_by_type)
                    chart2_img = Image(chart2_buf, width=16*cm, height=8*cm)

                    # Grafici uno sopra l'altro
                    story.append(chart1_img)
                    story.append(Spacer(1, 40))
                    story.append(chart2_img)
                else:
                    story.append(chart1_img)

            except Exception as e:
                story.append(Paragraph(f"[Grafici non disponibili: {e}]", normal_style))
            story.append(Spacer(1, 20))

            # Sezione Suggerimenti di Adeguamento
            if privacy.remediation_suggestions:
                # Colore arancione warning
                WARNING_ORANGE = colors.Color(0.98, 0.9, 0.8)  # Light orange background

                # Box con suggerimenti
                suggestions_data = []
                for i, suggestion in enumerate(privacy.remediation_suggestions, 1):
                    suggestions_data.append([f"{i}.", suggestion])

                keep_elements = [
                    Paragraph("Suggerimenti per l'Adeguamento", section_style),
                    Paragraph(
                        "<i>In base ai dati sensibili trovati, si consiglia di:</i>",
                        normal_style
                    ),
                    Spacer(1, 8),
                ]

                if suggestions_data:
                    suggestions_table = Table(suggestions_data, colWidths=[1*cm, 14*cm])
                    suggestions_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), WARNING_ORANGE),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('BOX', (0, 0), (-1, -1), 1, PA_ORANGE),
                    ]))
                    keep_elements.append(suggestions_table)

                from reportlab.platypus import KeepTogether
                story.append(KeepTogether(keep_elements))

                story.append(Spacer(1, 10))

                # Link risorse
                story.append(Paragraph("<b>Risorse utili:</b>", normal_style))
                story.append(Paragraph(
                    "- Garante Privacy: <link href='https://www.garanteprivacy.it/faq'>garanteprivacy.it/faq</link>",
                    normal_style
                ))
                story.append(Paragraph(
                    "- ANAC Trasparenza: <link href='https://www.anticorruzione.it/trasparenza'>"
                    "anticorruzione.it/trasparenza</link>",
                    normal_style
                ))
                story.append(Paragraph(
                    "- Normativa: D.Lgs. 33/2013 (Decreto Trasparenza)",
                    normal_style
                ))
                story.append(Spacer(1, 8))
                story.append(Paragraph(
                    "<i><font size='8'>Nota: Questi suggerimenti non sostituiscono la consulenza del DPO.</font></i>",
                    normal_style
                ))
                story.append(Spacer(1, 15))

            # High risk URLs (con page break se ci sono molti)
            if privacy.high_risk_urls:
                story.append(PageBreak())
                story.append(Paragraph("URL ad Alto Rischio", section_style))
                story.append(Paragraph(
                    "<i>Queste pagine/file contengono potenziali dati personali sensibili.</i>",
                    normal_style
                ))
                story.append(Spacer(1, 10))

                for i, url in enumerate(privacy.high_risk_urls[:30], 1):
                    display_url = url if len(url) < 75 else url[:72] + "..."
                    story.append(Paragraph(
                        f"<b>{i}.</b> <link href='{url}'>{display_url}</link>",
                        normal_style
                    ))

                if len(privacy.high_risk_urls) > 30:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(
                        f"<i>... e altri {len(privacy.high_risk_urls) - 30} URL "
                        "(vedere privacy_report.txt per lista completa)</i>",
                        normal_style
                    ))

            # Medium risk URLs
            if privacy.medium_risk_urls:
                story.append(Spacer(1, 20))
                story.append(Paragraph("URL a Rischio Medio", section_style))
                for i, url in enumerate(privacy.medium_risk_urls[:20], 1):
                    display_url = url if len(url) < 75 else url[:72] + "..."
                    story.append(Paragraph(
                        f"<b>{i}.</b> <link href='{url}'>{display_url}</link>",
                        normal_style
                    ))

                if len(privacy.medium_risk_urls) > 20:
                    story.append(Paragraph(
                        f"<i>... e altri {len(privacy.medium_risk_urls) - 20} URL</i>",
                        normal_style
                    ))

        # Build PDF con header/footer
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

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
    # Path assoluto: da reporters/ → orchestrator/ → Tesi/ → output/
    output_dir = output_dir or Path(__file__).parent.parent.parent / "output"
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
