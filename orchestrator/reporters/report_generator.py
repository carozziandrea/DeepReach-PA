"""
Full Analysis Report Generator - Genera report completi in TXT e PDF.

Combina tutte le metriche in un documento permanente:
- Site metadata
- Crawl statistics
- Transparency section analysis
- Reachability metrics
- Usability index
- Privacy analysis summary
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

from models import AnalysisResult
from .base_reporter import BaseReporter


class FullAnalysisTextReporter(BaseReporter):
    """Genera report completo in formato testo."""

    def get_file_extension(self) -> str:
        return "txt"

    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> Path:
        """Genera il report completo in formato testo."""
        filename = filename or "analysis_report"
        output_path = self.get_output_path(filename)

        content = self._generate_report(result)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _generate_report(self, result: AnalysisResult) -> str:
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("                    DEEPREACH-PA: FULL ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        # Site Metadata
        lines.append("SITE METADATA")
        lines.append("-" * 40)
        lines.append(f"Homepage URL: {result.homepage_url}")
        lines.append(f"AT Section Found: {'Yes' if result.at_found else 'No'}")
        if result.at_url:
            lines.append(f"AT URL: {result.at_url}")
        lines.append("")

        # Crawl Statistics
        lines.append("=" * 80)
        lines.append("CRAWL STATISTICS")
        lines.append("=" * 80)
        lines.append("")

        if result.crawl_deep:
            lines.append("Deep Crawl (AT Section):")
            lines.append(f"  Status: {'Success' if result.crawl_deep.success else 'Failed'}")
            lines.append(f"  Pages found: {result.crawl_deep.total_pages}")
            lines.append(f"  Duration: {result.crawl_deep.duration_seconds:.1f} seconds")
            if result.crawl_deep.error_message:
                lines.append(f"  Error: {result.crawl_deep.error_message}")
            lines.append("")

        if result.crawl_shallow:
            lines.append("Shallow Crawl (Homepage):")
            lines.append(f"  Status: {'Success' if result.crawl_shallow.success else 'Failed'}")
            lines.append(f"  Pages found: {result.crawl_shallow.total_pages}")
            lines.append(f"  Duration: {result.crawl_shallow.duration_seconds:.1f} seconds")
            if result.crawl_shallow.error_message:
                lines.append(f"  Error: {result.crawl_shallow.error_message}")
            lines.append("")

        # Reachability Metrics
        if result.reachability_at or result.reachability_main:
            lines.append("=" * 80)
            lines.append("REACHABILITY METRICS")
            lines.append("=" * 80)
            lines.append("")

            if result.reachability_at:
                r = result.reachability_at
                lines.append("AT Section:")
                lines.append(f"  Total pages: {r.total_pages}")
                lines.append(f"  Total files: {r.total_files}")
                lines.append(f"  Average depth: {r.avg_depth:.2f}")
                lines.append(f"  Max depth: {r.max_depth}")
                lines.append(f"  Pages at depth 1: {r.pages_at_depth_1}")
                lines.append(f"  Pages at depth 2: {r.pages_at_depth_2}")
                lines.append(f"  Pages at depth 3+: {r.pages_at_depth_3_plus}")
                lines.append("")

            if result.reachability_main:
                r = result.reachability_main
                lines.append("Homepage/Main:")
                lines.append(f"  Total pages: {r.total_pages}")
                lines.append(f"  Average depth: {r.avg_depth:.2f}")
                lines.append(f"  Max depth: {r.max_depth}")
                lines.append("")

        # Quality Metrics
        if result.quality_at or result.quality_main:
            lines.append("=" * 80)
            lines.append("QUALITY METRICS")
            lines.append("=" * 80)
            lines.append("")

            if result.quality_at:
                q = result.quality_at
                lines.append("AT Section:")
                lines.append(f"  Total nodes: {q.total_nodes}")
                lines.append(f"  Pages OK: {q.pages_ok}")
                lines.append(f"  Pages broken: {q.pages_broken} ({q.broken_percent:.1f}%)")
                lines.append(f"  Files found: {q.files_found}")
                if q.broken_urls:
                    lines.append(f"  Broken URLs (top 10):")
                    for url in q.broken_urls[:10]:
                        lines.append(f"    - {url}")
                lines.append("")

        # Transparency Analysis
        if result.transparency:
            t = result.transparency
            lines.append("=" * 80)
            lines.append("TRANSPARENCY ANALYSIS")
            lines.append("=" * 80)
            lines.append("")
            lines.append(f"Required sections analyzed: {t.total_required_sections}")
            lines.append(f"Sections in AT: {t.sections_in_at} ({t.at_coverage_percent:.1f}%)")
            lines.append(f"Hidden transparency (outside AT): {t.sections_only_in_main}")
            lines.append(f"Missing sections: {t.sections_missing}")
            lines.append("")

            if t.hidden_sections:
                lines.append("Hidden Sections (Trasparenza Sommersa):")
                for section in t.hidden_sections:
                    lines.append(f"  - {section}")
                lines.append("")

            if t.missing_sections:
                lines.append("Missing Sections:")
                for section in t.missing_sections:
                    lines.append(f"  - {section}")
                lines.append("")

            lines.append("Section Details:")
            lines.append("-" * 40)
            for section in t.sections:
                status = "OK (in AT)" if section.found_in_at else "HIDDEN" if section.is_hidden else "MISSING"
                depth_info = ""
                if section.min_depth_in_at is not None:
                    depth_info = f" (depth: {section.min_depth_in_at})"
                lines.append(f"  {section.name}: {status}{depth_info}")
            lines.append("")

        # Usability Index
        if result.usability_index:
            u = result.usability_index
            lines.append("=" * 80)
            lines.append("USABILITY INDEX")
            lines.append("=" * 80)
            lines.append("")
            lines.append(f"Final Score: {u.score:.1f}/100 - {u.rating}")
            lines.append("")
            lines.append("Score Breakdown:")
            lines.append(f"  Base score: {u.base_score:.1f}")
            lines.append(f"  Depth penalty: -{u.depth_penalty:.1f}")
            lines.append(f"  Broken links penalty: -{u.broken_penalty:.1f}")
            lines.append(f"  Hidden sections penalty: -{u.hidden_penalty:.1f}")
            lines.append(f"  Bonus: +{u.bonus:.1f}")
            lines.append("")

        # Privacy Analysis
        if result.privacy:
            p = result.privacy
            lines.append("=" * 80)
            lines.append("PRIVACY ANALYSIS")
            lines.append("=" * 80)
            lines.append("")
            lines.append(f"Nodes scanned: {p.total_scanned}")
            lines.append(f"  - HTML pages: {p.pages_scanned}")
            lines.append(f"  - Files: {p.files_scanned}")
            lines.append("")
            lines.append("Risk Distribution:")
            lines.append(f"  HIGH RISK: {p.high_risk_count}")
            lines.append(f"  MEDIUM RISK: {p.medium_risk_count}")
            lines.append(f"  LOW RISK: {p.low_risk_count}")
            lines.append("")

            if p.findings_by_type:
                lines.append("Findings by Type:")
                for pattern, count in p.findings_by_type.items():
                    lines.append(f"  - {pattern}: {count}")
                lines.append("")

            if p.high_risk_urls:
                lines.append("High Risk URLs (top 10):")
                for url in p.high_risk_urls[:10]:
                    lines.append(f"  - {url}")
                lines.append("")

            lines.append("(See privacy_report.txt/pdf for detailed privacy analysis)")
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("                              END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)


class FullAnalysisPDFReporter(BaseReporter):
    """Genera report completo in formato PDF con grafici e styling professionale."""

    def get_file_extension(self) -> str:
        return "pdf"

    def report(
        self,
        result: AnalysisResult,
        filename: Optional[str] = None,
        graph_png_path: Optional[str] = None
    ) -> Optional[Path]:
        """
        Genera il report completo in formato PDF.

        Args:
            result: Risultato dell'analisi
            filename: Nome del file output (senza estensione)
            graph_png_path: Path opzionale all'immagine PNG del grafo da incorporare
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, Image, KeepTogether
            )
        except ImportError:
            print("Libreria reportlab non installata. Report PDF non generato.")
            return None

        filename = filename or "analysis_report"
        output_path = self.get_output_path(filename)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Colori palette PA
        PA_BLUE = colors.Color(0.145, 0.388, 0.922)  # #2563eb
        PA_GREEN = colors.Color(0.086, 0.639, 0.290)  # #16a34a
        PA_RED = colors.Color(0.863, 0.149, 0.149)    # #dc2626
        PA_ORANGE = colors.Color(0.851, 0.467, 0.024) # #d97706
        LIGHT_GRAY = colors.Color(0.95, 0.95, 0.95)

        # Documento con header/footer
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,  # Spazio per header
            bottomMargin=2.5*cm  # Spazio per footer
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
            canvas.drawString(2*cm, height - 1.5*cm, "DeepReach-PA - Report Analisi Trasparenza")

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
            fontSize=22,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=PA_BLUE
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=PA_BLUE,
            borderPadding=5,
        )
        subsection_style = ParagraphStyle(
            'Subsection',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.darkgrey,
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        story = []

        # ===== PAGINA 1: OVERVIEW =====

        # Title
        story.append(Spacer(1, 20))
        story.append(Paragraph("Report Analisi Trasparenza PA", title_style))
        story.append(Spacer(1, 30))

        # Info box
        info_data = [
            ["Sito analizzato:", result.homepage_url],
            ["Sezione AT:", result.at_url if result.at_url else "Non trovata"],
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
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 30))

        # Usability Index (grande e prominente)
        if result.usability_index:
            u = result.usability_index
            score_color = PA_GREEN if u.score >= 75 else PA_ORANGE if u.score >= 50 else PA_RED

            story.append(Paragraph("Indice di Usabilita", section_style))

            score_data = [[
                Paragraph(f"<font size='28'><b>{u.score:.0f}</b></font><font size='14'>/100</font>",
                         ParagraphStyle('score', alignment=TA_CENTER)),
                Paragraph(f"<font size='16'><b>{u.rating}</b></font>",
                         ParagraphStyle('rating', alignment=TA_CENTER))
            ]]
            score_table = Table(score_data, colWidths=[8*cm, 8*cm])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), score_color),
                ('BACKGROUND', (1, 0), (1, 0), LIGHT_GRAY),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('BOX', (0, 0), (-1, -1), 1, colors.lightgrey),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 20))

            # Breakdown
            breakdown_data = [
                ["Componente", "Valore"],
                ["Punteggio base", f"+{u.base_score:.0f}"],
                ["Penalita profondita", f"-{u.depth_penalty:.0f}"],
                ["Penalita link rotti", f"-{u.broken_penalty:.0f}"],
                ["Penalita trasparenza sommersa", f"-{u.hidden_penalty:.0f}"],
                ["Bonus completezza", f"+{u.bonus:.0f}"],
            ]
            breakdown_table = Table(breakdown_data, colWidths=[10*cm, 4*cm])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ]))
            story.append(breakdown_table)

        # Page break
        story.append(PageBreak())

        # ===== PAGINA 2: TRASPARENZA E GRAFICI =====

        # Transparency Analysis
        if result.transparency:
            t = result.transparency
            story.append(Paragraph("Analisi Trasparenza", section_style))

            # Tabella trasparenza
            trans_data = [
                ["Metrica", "Valore", "Percentuale"],
                ["Sezioni in AT", str(t.sections_in_at), f"{t.at_coverage_percent:.0f}%"],
                ["Trasparenza sommersa", str(t.sections_only_in_main), ""],
                ["Sezioni mancanti", str(t.sections_missing), ""],
            ]
            trans_table = Table(trans_data, colWidths=[7*cm, 4*cm, 4*cm])
            trans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ]))
            story.append(trans_table)
            story.append(Spacer(1, 15))

            # Grafico trasparenza
            try:
                from .chart_utils import create_transparency_bar_chart
                chart_buffer = create_transparency_bar_chart(
                    t.sections_in_at,
                    t.sections_only_in_main,
                    t.sections_missing
                )
                chart_img = Image(chart_buffer, width=12*cm, height=8*cm)
                story.append(chart_img)
                story.append(Spacer(1, 15))
            except Exception as e:
                story.append(Paragraph(f"[Grafico non disponibile: {e}]", normal_style))

            # Dettagli sezioni
            if t.hidden_sections:
                story.append(Paragraph("<b>Sezioni fuori da AT (trasparenza sommersa):</b>", normal_style))
                story.append(Paragraph(", ".join(t.hidden_sections), normal_style))
            if t.missing_sections:
                story.append(Paragraph("<b>Sezioni mancanti:</b>", normal_style))
                story.append(Paragraph(", ".join(t.missing_sections), normal_style))

        story.append(Spacer(1, 20))

        # Privacy Analysis
        if result.privacy:
            p = result.privacy
            story.append(Paragraph("Analisi Privacy", section_style))

            # Tabella privacy
            privacy_data = [
                ["Livello Rischio", "Conteggio", ""],
                ["ALTO", str(p.high_risk_count), ""],
                ["MEDIO", str(p.medium_risk_count), ""],
                ["BASSO", str(p.low_risk_count), ""],
            ]
            privacy_table = Table(privacy_data, colWidths=[6*cm, 3*cm, 6*cm])
            privacy_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (1, 1), colors.Color(1, 0.8, 0.8)),  # Light red
                ('BACKGROUND', (0, 2), (1, 2), colors.Color(1, 0.9, 0.8)),  # Light orange
                ('BACKGROUND', (0, 3), (1, 3), colors.Color(1, 1, 0.8)),    # Light yellow
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(privacy_table)
            story.append(Spacer(1, 15))

            # Grafico privacy
            if p.high_risk_count + p.medium_risk_count + p.low_risk_count > 0:
                try:
                    from .chart_utils import create_privacy_pie_chart
                    chart_buffer = create_privacy_pie_chart(
                        p.high_risk_count,
                        p.medium_risk_count,
                        p.low_risk_count
                    )
                    chart_img = Image(chart_buffer, width=9*cm, height=9*cm)
                    story.append(chart_img)
                except Exception as e:
                    story.append(Paragraph(f"[Grafico non disponibile: {e}]", normal_style))

            story.append(Spacer(1, 10))
            story.append(Paragraph("<i>Vedi privacy_report.pdf per analisi dettagliata.</i>", normal_style))

        # Page break
        story.append(PageBreak())

        # ===== PAGINA 3: CRAWL STATISTICS =====

        story.append(Paragraph("Statistiche Crawl", section_style))

        if result.crawl_deep or result.crawl_shallow:
            crawl_data = [["Tipo Crawl", "Stato", "Pagine", "Durata"]]
            if result.crawl_deep:
                status = "Completato" if result.crawl_deep.success else "Fallito"
                crawl_data.append([
                    "Deep (sezione AT)",
                    status,
                    str(result.crawl_deep.total_pages),
                    f"{result.crawl_deep.duration_seconds:.1f}s"
                ])
            if result.crawl_shallow:
                status = "Completato" if result.crawl_shallow.success else "Fallito"
                crawl_data.append([
                    "Shallow (homepage)",
                    status,
                    str(result.crawl_shallow.total_pages),
                    f"{result.crawl_shallow.duration_seconds:.1f}s"
                ])

            crawl_table = Table(crawl_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
            crawl_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ]))
            story.append(crawl_table)
            story.append(Spacer(1, 20))

        # Reachability metrics
        if result.reachability_at:
            r = result.reachability_at
            story.append(Paragraph("Raggiungibilita Sezione AT", subsection_style))

            reach_data = [
                ["Metrica", "Valore"],
                ["Pagine totali", str(r.total_pages)],
                ["File trovati", str(r.total_files)],
                ["Profondita media", f"{r.avg_depth:.1f} click"],
                ["Profondita massima", f"{r.max_depth} click"],
            ]
            reach_table = Table(reach_data, colWidths=[8*cm, 6*cm])
            reach_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(reach_table)
            story.append(Spacer(1, 15))

        # Quality metrics
        if result.quality_at:
            q = result.quality_at
            story.append(Paragraph("Qualita Strutturale", subsection_style))

            quality_data = [
                ["Metrica", "Valore"],
                ["Nodi totali", str(q.total_nodes)],
                ["Pagine funzionanti", str(q.pages_ok)],
                ["Link rotti", f"{q.pages_broken} ({q.broken_percent:.1f}%)"],
                ["File trovati", str(q.files_found)],
            ]
            quality_table = Table(quality_data, colWidths=[8*cm, 6*cm])
            quality_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(quality_table)

            # Link rotti (se presenti)
            if q.broken_urls:
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b>Link rotti (primi 10):</b>", normal_style))
                for url in q.broken_urls[:10]:
                    display_url = url if len(url) < 70 else url[:67] + "..."
                    story.append(Paragraph(f"- {display_url}", normal_style))

        # ===== PAGINA 4: MAPPA DEL SITO (se disponibile) =====

        if graph_png_path and Path(graph_png_path).exists():
            story.append(PageBreak())
            story.append(Paragraph("Mappa del Sito", section_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                "Visualizzazione del grafo delle pagine analizzate. "
                "I colori indicano: blu = pagine funzionanti, rosso = link rotti/homepage, "
                "verde = file, cyan = sezioni trasparenza.",
                normal_style
            ))
            story.append(Spacer(1, 15))

            try:
                # Dimensione ottimizzata per A4
                graph_img = Image(graph_png_path, width=16*cm, height=11*cm)
                story.append(graph_img)
            except Exception as e:
                story.append(Paragraph(f"[Immagine grafo non disponibile: {e}]", normal_style))

        # Build con header/footer
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        return output_path


def generate_full_reports(
    result: AnalysisResult,
    output_dir: Path = None,
    graph_json_path: str = None
) -> Dict[str, Path]:
    """
    Genera tutti i report completi (TXT e PDF).

    Args:
        result: Risultato dell'analisi
        output_dir: Directory di output
        graph_json_path: Path opzionale al file site_tree.json per generare immagine grafo

    Returns:
        Dizionario con i path dei file generati
    """
    output_dir = output_dir or Path("./output")
    generated = {}

    # Report TXT
    txt_reporter = FullAnalysisTextReporter(output_dir)
    txt_path = txt_reporter.report(result)
    generated['txt'] = txt_path
    print(f"Full analysis report (TXT): {txt_path}")

    # Genera immagine PNG del grafo (se disponibile)
    graph_png_path = None
    if graph_json_path and Path(graph_json_path).exists():
        try:
            # Import qui per evitare dipendenze circolari
            import sys
            scripts_dir = Path(__file__).parent.parent.parent / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))

            from graph_builder import GraphBuilder
            from .chart_utils import export_graph_to_png

            # Carica e costruisci il grafo
            data = GraphBuilder.load_data(graph_json_path)
            tree = data.get("tree", data)
            start_url = GraphBuilder.find_root_node(tree)
            G = GraphBuilder.build_graph(tree, start_url)
            G_spt = GraphBuilder.create_shortest_path_tree(G, start_url)

            # Esporta come PNG
            png_path = output_dir / "graph_image.png"
            result_png = export_graph_to_png(G_spt, png_path)
            if result_png:
                graph_png_path = result_png
                generated['graph_png'] = Path(result_png)
                print(f"Graph image (PNG): {result_png}")
        except Exception as e:
            print(f"[WARN] Impossibile generare immagine grafo: {e}")

    # Report PDF
    pdf_reporter = FullAnalysisPDFReporter(output_dir)
    pdf_path = pdf_reporter.report(result, graph_png_path=graph_png_path)
    if pdf_path:
        generated['pdf'] = pdf_path
        print(f"Full analysis report (PDF): {pdf_path}")

    return generated
