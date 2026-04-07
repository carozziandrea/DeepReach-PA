"""
Metrics Calculator - Calcola le metriche di analisi.

Questo modulo contiene le funzioni per calcolare:
- Metriche di raggiungibilità
- Metriche di qualità strutturale
- Indice di usabilità
"""

from typing import Dict, Any, List
from collections import Counter

from config import OrchestratorConfig, default_config
from models import (
    ReachabilityMetrics,
    QualityMetrics,
    UsabilityIndex,
)


class MetricsCalculator:
    """Calcola le metriche dai dati del crawl."""
    
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or default_config
    
    def calculate_reachability(self, tree_data: Dict[str, Any]) -> ReachabilityMetrics:
        """
        Calcola le metriche di raggiungibilità.
        
        Args:
            tree_data: Dizionario 'tree' dal JSON del crawl
        
        Returns:
            ReachabilityMetrics popolato
        """
        metrics = ReachabilityMetrics()
        
        if not tree_data:
            return metrics
        
        depths = []
        files_count = 0
        
        for url, info in tree_data.items():
            depth = info.get('depth', 0)
            status = info.get('status', '')
            
            if status == 'file':
                files_count += 1
            else:
                depths.append(depth)
        
        if depths:
            metrics.total_pages = len(depths)
            metrics.total_files = files_count
            metrics.avg_depth = sum(depths) / len(depths)
            metrics.max_depth = max(depths)
            metrics.min_depth = min(depths)
            
            # Distribuzione per profondità
            metrics.depth_distribution = dict(Counter(depths))
            
            # Conteggi specifici
            metrics.pages_at_depth_1 = sum(1 for d in depths if d == 1)
            metrics.pages_at_depth_2 = sum(1 for d in depths if d == 2)
            metrics.pages_at_depth_3_plus = sum(1 for d in depths if d >= 3)
        
        return metrics
    
    def calculate_quality(self, tree_data: Dict[str, Any]) -> QualityMetrics:
        """
        Calcola le metriche di qualità strutturale.
        
        Args:
            tree_data: Dizionario 'tree' dal JSON del crawl
        
        Returns:
            QualityMetrics popolato
        """
        metrics = QualityMetrics()
        
        if not tree_data:
            return metrics
        
        metrics.total_nodes = len(tree_data)
        
        for url, info in tree_data.items():
            status = info.get('status', '')
            parents = info.get('parents', [])
            
            if status == 'ok':
                metrics.pages_ok += 1
            elif status == 'broken':
                metrics.pages_broken += 1
                metrics.broken_urls.append(url)
            elif status == 'not_visited':
                metrics.pages_not_visited += 1
            elif status == 'file':
                metrics.files_found += 1
            
            # Pagine orfane (senza parent, escluso root)
            depth = info.get('depth', 0)
            if depth > 0 and not parents:
                metrics.orphan_urls.append(url)
        
        # Percentuale link rotti
        if metrics.total_nodes > 0:
            metrics.broken_percent = (metrics.pages_broken / metrics.total_nodes) * 100
        
        return metrics
    
    def calculate_usability_index(
        self,
        reachability: ReachabilityMetrics,
        quality: QualityMetrics,
        hidden_sections_count: int,
        missing_sections_count: int,
        sections_in_at: int,
        total_required_sections: int,
        sections_detail: list,
    ) -> UsabilityIndex:
        """
        Calcola l'indice di usabilità (0-100).

        Il punteggio finale è una media ponderata tra:
        - score_conformità: percentuale di sezioni obbligatorie presenti in AT
        - score_usabilità: qualità tecnica (profondità, link rotti, sezioni sommerse/mancanti)

        Args:
            reachability: Metriche di raggiungibilità
            quality: Metriche di qualità
            hidden_sections_count: Numero di sezioni fuori da AT
            missing_sections_count: Numero di sezioni completamente assenti
            sections_in_at: Numero di sezioni correttamente in AT
            total_required_sections: Numero totale di sezioni obbligatorie
            sections_detail: Lista di SectionAnalysis con min_depth_in_at

        Returns:
            UsabilityIndex popolato
        """
        weights = self.config.usability_weights
        index = UsabilityIndex()
        index.base_score = weights.base_score

        # Score conformità normativa
        if total_required_sections > 0:
            index.conformity_score = (sections_in_at / total_required_sections) * 100
        else:
            index.conformity_score = 0.0

        # Profondità media delle sezioni obbligatorie trovate in AT
        depths = [
            s.min_depth_in_at
            for s in sections_detail
            if s.found_in_at and s.min_depth_in_at is not None
        ]
        avg_section_depth = sum(depths) / len(depths) if depths else 0.0

        if avg_section_depth > weights.ideal_depth:
            excess = avg_section_depth - weights.ideal_depth
            index.depth_penalty = excess * weights.penalty_per_depth_level

        index.broken_penalty = quality.broken_percent * weights.penalty_per_broken_percent
        index.hidden_penalty = hidden_sections_count * weights.penalty_per_hidden_section
        index.missing_penalty = missing_sections_count * weights.penalty_per_missing_section

        # Bonus graduale proporzionale alla copertura AT
        if total_required_sections > 0:
            index.bonus = (sections_in_at / total_required_sections) * weights.bonus_all_sections_in_at
        else:
            index.bonus = 0.0

        index.usability_score = (
            index.base_score
            - index.depth_penalty
            - index.broken_penalty
            - index.hidden_penalty
            - index.missing_penalty
            + index.bonus
        )
        index.usability_score = max(weights.min_score, min(index.usability_score, weights.max_score))

        # Score finale ponderato
        index.score = (
            index.conformity_score * weights.weight_conformity +
            index.usability_score * weights.weight_usability
        )
        index.score = max(weights.min_score, min(index.score, weights.max_score))

        index.rating = UsabilityIndex.get_rating(index.score)
        return index


def calculate_all_metrics(
    tree_data: Dict[str, Any],
    hidden_sections_count: int = 0,
    missing_sections_count: int = 0,
    sections_in_at: int = 0,
    total_required_sections: int = 23,
    sections_detail: list = None,
    config: OrchestratorConfig = None
) -> tuple:
    """
    Funzione di convenienza per calcolare tutte le metriche.

    Returns:
        Tupla (reachability, quality, usability)
    """
    calculator = MetricsCalculator(config)

    reachability = calculator.calculate_reachability(tree_data)
    quality = calculator.calculate_quality(tree_data)
    usability = calculator.calculate_usability_index(
        reachability,
        quality,
        hidden_sections_count,
        missing_sections_count,
        sections_in_at,
        total_required_sections,
        sections_detail or [],
    )

    return reachability, quality, usability
