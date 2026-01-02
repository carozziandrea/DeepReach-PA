"""
Analyzer - Analizza i risultati dei crawl e confronta AT vs Main.

Questo modulo:
- Carica i JSON prodotti dai crawler
- Analizza la presenza delle sezioni obbligatorie
- Identifica la trasparenza sommersa
- Calcola tutte le metriche
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import OrchestratorConfig, default_config
from models import (
    AnalysisResult,
    CrawlInfo,
    SectionAnalysis,
    TransparencyMetrics,
    ReachabilityMetrics,
    QualityMetrics,
    UsabilityIndex,
    PrivacyMetrics,
)
from metrics import MetricsCalculator
from privacy_analyzer import PrivacyAnalyzer, PrivacyAnalysisConfig


class Analyzer:
    """Analizza i risultati dei crawl."""
    
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or default_config
        self.metrics_calculator = MetricsCalculator(config)
        self.privacy_analyzer = None
        if self.config.privacy.enabled:
            privacy_config = PrivacyAnalysisConfig(
                scan_html=self.config.privacy.scan_html_content,
                scan_files=self.config.privacy.scan_pdf_files,
                max_content_length=self.config.privacy.max_content_chars,
                max_file_size_mb=self.config.privacy.max_file_size_mb,
                download_delay=self.config.privacy.download_delay_seconds,
                download_timeout=self.config.privacy.download_timeout_seconds,
            )
            self.privacy_analyzer = PrivacyAnalyzer(privacy_config)
    
    def load_crawl_data(self, output_name: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati di un crawl dal file JSON.
        
        Args:
            output_name: Nome del file (senza .json)
        
        Returns:
            Dizionario con i dati o None se errore
        """
        file_path = self.config.crawl.output_dir / f"{output_name}.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ File non trovato: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️ Errore parsing JSON {file_path}: {e}")
            return None
    
    def find_section_in_tree(
        self,
        tree: Dict[str, Any],
        keywords: List[str]
    ) -> Tuple[bool, List[str], Optional[int]]:
        """
        Cerca una sezione nel tree in base alle keyword.
        
        Args:
            tree: Dizionario 'tree' dal JSON
            keywords: Lista di keyword da cercare negli URL
        
        Returns:
            Tupla (found, matching_urls, min_depth)
        """
        matching_urls = []
        min_depth = None
        
        for url, info in tree.items():
            url_lower = url.lower()
            
            # Controlla se l'URL contiene una delle keyword
            for keyword in keywords:
                if keyword.lower() in url_lower:
                    matching_urls.append(url)
                    depth = info.get('depth', 0)
                    
                    if min_depth is None or depth < min_depth:
                        min_depth = depth
                    
                    break  # Evita duplicati per lo stesso URL
        
        found = len(matching_urls) > 0
        return found, matching_urls, min_depth
    
    def analyze_sections(
        self,
        tree_at: Optional[Dict[str, Any]],
        tree_main: Optional[Dict[str, Any]]
    ) -> TransparencyMetrics:
        """
        Analizza la presenza delle sezioni obbligatorie in entrambi i tree.
        
        Args:
            tree_at: Tree della sezione AT
            tree_main: Tree della homepage/sito principale
        
        Returns:
            TransparencyMetrics con l'analisi completa
        """
        metrics = TransparencyMetrics()
        metrics.total_required_sections = len(self.config.required_sections)
        
        for section_name, keywords in self.config.required_sections.items():
            section = SectionAnalysis(name=section_name, keywords=keywords)
            
            # Cerca in AT
            if tree_at:
                found, urls, min_depth = self.find_section_in_tree(tree_at, keywords)
                section.found_in_at = found
                section.urls_in_at = urls
                section.min_depth_in_at = min_depth
            
            # Cerca in Main
            if tree_main:
                found, urls, min_depth = self.find_section_in_tree(tree_main, keywords)
                section.found_in_main = found
                section.urls_in_main = urls
                section.min_depth_in_main = min_depth
            
            metrics.sections.append(section)
            
            # Aggiorna conteggi
            if section.found_in_at:
                metrics.sections_in_at += 1
            
            if section.is_hidden:
                metrics.sections_only_in_main += 1
                metrics.hidden_sections.append(section_name)
            
            if section.is_missing:
                metrics.sections_missing += 1
                metrics.missing_sections.append(section_name)
        
        # Calcola percentuali
        if metrics.total_required_sections > 0:
            metrics.at_coverage_percent = (
                metrics.sections_in_at / metrics.total_required_sections
            ) * 100

            metrics.hidden_transparency_percent = (
                metrics.sections_only_in_main / metrics.total_required_sections
            ) * 100

        return metrics

    def analyze_privacy(
        self,
        tree: Dict[str, Any],
        base_url: str = None
    ) -> Optional[PrivacyMetrics]:
        """
        Analizza il tree per problemi di privacy.

        Scansiona contenuti HTML e PDF per rilevare dati personali sensibili.

        Args:
            tree: Dizionario 'tree' dal JSON del crawl
            base_url: URL base del sito

        Returns:
            PrivacyMetrics con i risultati o None se privacy disabilitata
        """
        if not self.privacy_analyzer:
            return None

        print("\n" + "=" * 60)
        print("ANALISI PRIVACY")
        print("=" * 60)

        # Esegui analisi privacy
        updated_tree, summary = self.privacy_analyzer.analyze_tree(tree, base_url)

        # Converti summary in PrivacyMetrics
        metrics = PrivacyMetrics(
            total_scanned=summary.total_scanned,
            pages_scanned=summary.pages_scanned,
            files_scanned=summary.files_scanned,
            high_risk_count=summary.high_risk_count,
            medium_risk_count=summary.medium_risk_count,
            low_risk_count=summary.low_risk_count,
            high_risk_urls=summary.high_risk_urls,
            medium_risk_urls=summary.medium_risk_urls,
            findings_by_type=summary.findings_by_type,
            scan_errors=summary.errors,
        )

        # Stampa riepilogo
        print(f"\nScansionati: {metrics.pages_scanned} pagine, {metrics.files_scanned} file")
        print(f"Rischio ALTO: {metrics.high_risk_count} nodi")
        print(f"Rischio MEDIO: {metrics.medium_risk_count} nodi")
        print(f"Rischio BASSO: {metrics.low_risk_count} nodi")

        if metrics.findings_by_type:
            print("\nRitrovamenti per tipo:")
            for pattern_type, count in metrics.findings_by_type.items():
                print(f"  - {pattern_type}: {count}")

        return metrics
    
    def analyze(
        self,
        homepage_url: str,
        at_url: Optional[str],
        crawl_shallow: Optional[CrawlInfo],
        crawl_deep: Optional[CrawlInfo]
    ) -> AnalysisResult:
        """
        Esegue l'analisi completa.
        
        Args:
            homepage_url: URL della homepage
            at_url: URL della sezione AT (None se non trovato)
            crawl_shallow: Info crawl shallow
            crawl_deep: Info crawl deep
        
        Returns:
            AnalysisResult con tutti i dati
        """
        result = AnalysisResult(
            homepage_url=homepage_url,
            at_url=at_url,
            at_found=at_url is not None,
            crawl_shallow=crawl_shallow,
            crawl_deep=crawl_deep,
        )
        
        # Carica dati JSON
        data_at = None
        data_main = None
        tree_at = None
        tree_main = None
        
        if crawl_deep and crawl_deep.success:
            data_at = self.load_crawl_data(self.config.crawl.deep_output_name)
            if data_at:
                tree_at = data_at.get('tree', {})
                result.raw_data['at'] = data_at
        
        if crawl_shallow and crawl_shallow.success:
            data_main = self.load_crawl_data(self.config.crawl.shallow_output_name)
            if data_main:
                tree_main = data_main.get('tree', {})
                result.raw_data['main'] = data_main
        
        # Analisi sezioni (trasparenza sommersa)
        result.transparency = self.analyze_sections(tree_at, tree_main)
        
        # Metriche raggiungibilità e qualità - AT
        if tree_at:
            result.reachability_at = self.metrics_calculator.calculate_reachability(tree_at)
            result.quality_at = self.metrics_calculator.calculate_quality(tree_at)
        
        # Metriche raggiungibilità e qualità - Main
        if tree_main:
            result.reachability_main = self.metrics_calculator.calculate_reachability(tree_main)
            result.quality_main = self.metrics_calculator.calculate_quality(tree_main)
        
        # Indice di usabilità (basato principalmente su AT)
        if result.reachability_at and result.quality_at and result.transparency:
            result.usability_index = self.metrics_calculator.calculate_usability_index(
                result.reachability_at,
                result.quality_at,
                result.transparency.sections_only_in_main,
                result.transparency.all_sections_in_at
            )

        # Analisi privacy (post-processing)
        # Usa tree_at se disponibile, altrimenti tree_main
        privacy_tree = tree_at if tree_at else tree_main
        if privacy_tree and self.config.privacy.enabled:
            result.privacy = self.analyze_privacy(privacy_tree, homepage_url)

            # Salva tree aggiornato con dati privacy
            if result.privacy and data_at:
                self._save_updated_tree(data_at, self.config.crawl.deep_output_name)
            elif result.privacy and data_main:
                self._save_updated_tree(data_main, self.config.crawl.shallow_output_name)

        return result

    def _save_updated_tree(self, data: Dict[str, Any], output_name: str) -> None:
        """Salva il tree aggiornato con i dati privacy."""
        file_path = self.config.crawl.output_dir / f"{output_name}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nTree aggiornato salvato in: {file_path}")
        except Exception as e:
            print(f"Errore salvataggio tree: {e}")


def analyze_crawls(
    homepage_url: str,
    at_url: Optional[str],
    crawl_shallow: Optional[CrawlInfo],
    crawl_deep: Optional[CrawlInfo],
    config: OrchestratorConfig = None
) -> AnalysisResult:
    """
    Funzione di convenienza per analizzare i crawl.
    """
    analyzer = Analyzer(config)
    return analyzer.analyze(homepage_url, at_url, crawl_shallow, crawl_deep)
