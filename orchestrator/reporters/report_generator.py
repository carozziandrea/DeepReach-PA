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
    """Genera report completo in formato PDF."""

    def get_file_extension(self) -> str:
        return "pdf"

    def report(self, result: AnalysisResult, filename: Optional[str] = None) -> Optional[Path]:
        """Genera il report completo in formato PDF."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        except ImportError:
            print("Libreria reportlab non installata. Report PDF non generato.")
            return None

        filename = filename or "analysis_report"
        output_path = self.get_output_path(filename)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10
        )
        normal_style = styles['Normal']

        story = []

        # Title
        story.append(Paragraph("DEEPREACH-PA: Full Analysis Report", title_style))
        story.append(Spacer(1, 12))

        # Metadata
        story.append(Paragraph(f"<b>Generated:</b> {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Paragraph(f"<b>Homepage:</b> {result.homepage_url}", normal_style))
        story.append(Paragraph(f"<b>AT Found:</b> {'Yes' if result.at_found else 'No'}", normal_style))
        story.append(Spacer(1, 20))

        # Crawl Stats
        if result.crawl_deep or result.crawl_shallow:
            story.append(Paragraph("Crawl Statistics", section_style))
            crawl_data = [["Crawl Type", "Status", "Pages", "Duration"]]
            if result.crawl_deep:
                crawl_data.append([
                    "Deep (AT)",
                    "Success" if result.crawl_deep.success else "Failed",
                    str(result.crawl_deep.total_pages),
                    f"{result.crawl_deep.duration_seconds:.1f}s"
                ])
            if result.crawl_shallow:
                crawl_data.append([
                    "Shallow (Main)",
                    "Success" if result.crawl_shallow.success else "Failed",
                    str(result.crawl_shallow.total_pages),
                    f"{result.crawl_shallow.duration_seconds:.1f}s"
                ])

            crawl_table = Table(crawl_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm])
            crawl_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(crawl_table)
            story.append(Spacer(1, 15))

        # Usability Index (prominent)
        if result.usability_index:
            story.append(Paragraph("Usability Index", section_style))
            u = result.usability_index

            # Score with color
            score_color = colors.green if u.score >= 75 else colors.orange if u.score >= 50 else colors.red
            score_data = [[f"Score: {u.score:.1f}/100", u.rating]]
            score_table = Table(score_data, colWidths=[8*cm, 5*cm])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), score_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 15))

        # Transparency
        if result.transparency:
            story.append(Paragraph("Transparency Analysis", section_style))
            t = result.transparency
            trans_data = [
                ["Metric", "Value"],
                ["Sections in AT", f"{t.sections_in_at}/{t.total_required_sections} ({t.at_coverage_percent:.1f}%)"],
                ["Hidden (outside AT)", str(t.sections_only_in_main)],
                ["Missing", str(t.sections_missing)],
            ]
            trans_table = Table(trans_data, colWidths=[8*cm, 5*cm])
            trans_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            story.append(trans_table)

            if t.hidden_sections or t.missing_sections:
                story.append(Spacer(1, 10))
                if t.hidden_sections:
                    story.append(Paragraph(f"<b>Hidden:</b> {', '.join(t.hidden_sections)}", normal_style))
                if t.missing_sections:
                    story.append(Paragraph(f"<b>Missing:</b> {', '.join(t.missing_sections)}", normal_style))
            story.append(Spacer(1, 15))

        # Privacy Summary
        if result.privacy:
            story.append(Paragraph("Privacy Analysis Summary", section_style))
            p = result.privacy
            privacy_data = [
                ["Risk Level", "Count"],
                ["HIGH", str(p.high_risk_count)],
                ["MEDIUM", str(p.medium_risk_count)],
                ["LOW", str(p.low_risk_count)],
            ]
            privacy_table = Table(privacy_data, colWidths=[8*cm, 5*cm])
            privacy_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 1), (-1, 1), colors.Color(1, 0.6, 0.6)),
                ('BACKGROUND', (0, 2), (-1, 2), colors.Color(1, 0.8, 0.6)),
                ('BACKGROUND', (0, 3), (-1, 3), colors.Color(1, 1, 0.6)),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(privacy_table)
            story.append(Spacer(1, 10))
            story.append(Paragraph("See privacy_report.pdf for detailed analysis.", normal_style))

        doc.build(story)
        return output_path


def generate_full_reports(result: AnalysisResult, output_dir: Path = None) -> Dict[str, Path]:
    """
    Genera tutti i report completi (TXT e PDF).

    Args:
        result: Risultato dell'analisi
        output_dir: Directory di output

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

    # Report PDF
    pdf_reporter = FullAnalysisPDFReporter(output_dir)
    pdf_path = pdf_reporter.report(result)
    if pdf_path:
        generated['pdf'] = pdf_path
        print(f"Full analysis report (PDF): {pdf_path}")

    return generated
