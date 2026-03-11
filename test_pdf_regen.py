"""
Script di test per rigenerare i PDF con le modifiche applicate.
Carica i dati da analysis_report.json e genera i PDF aggiornati.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Aggiungi orchestrator al path
orchestrator_dir = Path(__file__).parent / "orchestrator"
sys.path.insert(0, str(orchestrator_dir))

from models import (
    AnalysisResult, ReachabilityMetrics, QualityMetrics,
    TransparencyMetrics, SectionAnalysis, UsabilityIndex,
    PrivacyMetrics, CrawlInfo
)

def load_analysis_result(json_path: Path) -> AnalysisResult:
    """Ricostruisce AnalysisResult dal file JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data['metadata']
    
    # Crawl info
    crawl_shallow = None
    crawl_deep = None
    if 'crawl_info' in data:
        if 'shallow' in data['crawl_info']:
            s = data['crawl_info']['shallow']
            crawl_shallow = CrawlInfo(
                mode=s['mode'], start_url=s['start_url'],
                output_file=s['output_file'], success=s['success'],
                total_pages=s['total_pages'],
                duration_seconds=s['duration_seconds'],
                error_message=s.get('error_message')
            )
        if 'deep' in data['crawl_info']:
            d = data['crawl_info']['deep']
            crawl_deep = CrawlInfo(
                mode=d['mode'], start_url=d['start_url'],
                output_file=d['output_file'], success=d['success'],
                total_pages=d['total_pages'],
                duration_seconds=d['duration_seconds'],
                error_message=d.get('error_message')
            )
    
    # Reachability
    reach_at = None
    reach_main = None
    if 'reachability' in data:
        if 'at' in data['reachability']:
            r = data['reachability']['at']
            reach_at = ReachabilityMetrics(
                total_pages=r['total_pages'], total_files=r['total_files'],
                avg_depth=r['avg_depth'], max_depth=r['max_depth'],
                min_depth=r.get('min_depth', 0),
                pages_at_depth_1=r['pages_at_depth_1'],
                pages_at_depth_2=r['pages_at_depth_2'],
                pages_at_depth_3_plus=r['pages_at_depth_3_plus']
            )
        if 'main' in data['reachability']:
            r = data['reachability']['main']
            reach_main = ReachabilityMetrics(
                total_pages=r['total_pages'], total_files=r.get('total_files', 0),
                avg_depth=r['avg_depth'], max_depth=r['max_depth'],
                min_depth=r.get('min_depth', 0),
                pages_at_depth_1=r['pages_at_depth_1'],
                pages_at_depth_2=r['pages_at_depth_2'],
                pages_at_depth_3_plus=r['pages_at_depth_3_plus']
            )
    
    # Quality
    quality_at = None
    if 'quality' in data and 'at' in data['quality']:
        q = data['quality']['at']
        quality_at = QualityMetrics(
            total_nodes=q['total_nodes'], pages_ok=q['pages_ok'],
            pages_broken=q['pages_broken'],
            pages_not_visited=q.get('pages_not_visited', 0),
            files_found=q['files_found'],
            broken_percent=q['broken_percent'],
            broken_urls=q.get('broken_urls', [])
        )
    
    # Transparency
    transparency = None
    if 'transparency' in data:
        t = data['transparency']
        sections = []
        for s in t.get('sections_detail', []):
            sections.append(SectionAnalysis(
                name=s['name'],
                found_in_at=s['found_in_at'],
                found_in_main=s['found_in_main'],
                min_depth_in_at=s.get('min_depth_in_at'),
                min_depth_in_main=s.get('min_depth_in_main')
            ))
        transparency = TransparencyMetrics(
            sections=sections,
            total_required_sections=t['total_required_sections'],
            sections_in_at=t['sections_in_at'],
            sections_only_in_main=t['sections_only_in_main'],
            sections_missing=t['sections_missing'],
            at_coverage_percent=t['at_coverage_percent'],
            hidden_transparency_percent=t.get('hidden_transparency_percent', 0),
            hidden_sections=t.get('hidden_sections', []),
            missing_sections=t.get('missing_sections', [])
        )
    
    # Usability
    usability = None
    if 'usability_index' in data:
        u = data['usability_index']
        usability = UsabilityIndex(
            score=u['score'], base_score=u['base_score'],
            depth_penalty=u['depth_penalty'],
            broken_penalty=u['broken_penalty'],
            hidden_penalty=u['hidden_penalty'],
            bonus=u['bonus'], rating=u['rating']
        )
    
    # Privacy
    privacy = None
    if 'privacy' in data:
        p = data['privacy']
        privacy = PrivacyMetrics(
            total_scanned=p['total_scanned'],
            pages_scanned=p['pages_scanned'],
            files_scanned=p['files_scanned'],
            high_risk_count=p['high_risk_count'],
            medium_risk_count=p['medium_risk_count'],
            low_risk_count=p['low_risk_count'],
            high_risk_urls=p.get('high_risk_urls', []),
            medium_risk_urls=p.get('medium_risk_urls', []),
            findings_by_type=p.get('findings_by_type', {})
        )
    
    result = AnalysisResult(
        homepage_url=meta['homepage_url'],
        at_url=meta.get('at_url'),
        at_found=meta.get('at_found', False),
        timestamp=datetime.fromisoformat(meta['timestamp']),
        crawl_shallow=crawl_shallow,
        crawl_deep=crawl_deep,
        reachability_at=reach_at,
        reachability_main=reach_main,
        quality_at=quality_at,
        transparency=transparency,
        usability_index=usability,
        privacy=privacy,
        raw_data=data
    )
    
    return result


if __name__ == '__main__':
    # Carica dati esistenti
    json_path = Path(__file__).parent / "output" / "comune.piedimulera.vb.it" / "analysis_report.json"
    
    if not json_path.exists():
        print(f"File non trovato: {json_path}")
        sys.exit(1)
    
    print(f"Caricamento dati da: {json_path}")
    result = load_analysis_result(json_path)
    
    print(f"  Homepage: {result.homepage_url}")
    print(f"  Score: {result.usability_index.score:.1f}/100 ({result.usability_index.rating})")
    print(f"  Privacy: H={result.privacy.high_risk_count}, M={result.privacy.medium_risk_count}, L={result.privacy.low_risk_count}")
    
    # Output directory per test
    test_output = Path(__file__).parent / "output" / "test_pdf_regen"
    test_output.mkdir(parents=True, exist_ok=True)
    
    # Genera analysis report PDF
    print(f"\n--- Generazione analysis_report.pdf ---")
    from reporters.report_generator import FullAnalysisPDFReporter
    pdf_reporter = FullAnalysisPDFReporter(test_output)
    pdf_path = pdf_reporter.report(result)
    if pdf_path:
        print(f"  OK: {pdf_path}")
    else:
        print("  ERRORE: PDF non generato")
    
    # Genera privacy report PDF
    print(f"\n--- Generazione privacy_report.pdf ---")
    from reporters.privacy_reporter import PrivacyPDFReporter
    privacy_reporter = PrivacyPDFReporter(test_output)
    privacy_path = privacy_reporter.report(result)
    if privacy_path:
        print(f"  OK: {privacy_path}")
    else:
        print("  ERRORE: PDF non generato")
    
    print(f"\n=== PDF generati in: {test_output} ===")
    print("Apri i PDF per verificare:")
    print("  1) Voto centrato verticalmente")
    print("  2) Nuovi colori rischio (bordeaux/ambra/blu)")
    print("  3) Stacked bar chart al posto del pie chart")
