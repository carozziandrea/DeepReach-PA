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
        all_sections_in_at: bool
    ) -> UsabilityIndex:
        """
        Calcola l'indice di usabilità (0-100).
        
        Formula:
            score = base - penalità_profondità - penalità_broken - penalità_hidden + bonus
        
        Args:
            reachability: Metriche di raggiungibilità
            quality: Metriche di qualità
            hidden_sections_count: Numero di sezioni fuori da AT
            all_sections_in_at: True se tutte le sezioni sono in AT
        
        Returns:
            UsabilityIndex popolato
        """
        weights = self.config.usability_weights
        index = UsabilityIndex()
        
        index.base_score = weights.base_score
        
        # Penalità profondità
        if reachability.avg_depth > weights.ideal_depth:
            excess_depth = reachability.avg_depth - weights.ideal_depth
            index.depth_penalty = excess_depth * weights.penalty_per_depth_level
        
        # Penalità link rotti
        index.broken_penalty = quality.broken_percent * weights.penalty_per_broken_percent
        
        # Penalità trasparenza sommersa
        index.hidden_penalty = hidden_sections_count * weights.penalty_per_hidden_section
        
        # Bonus
        if all_sections_in_at:
            index.bonus = weights.bonus_all_sections_in_at
        
        # Calcola punteggio finale
        index.score = (
            index.base_score
            - index.depth_penalty
            - index.broken_penalty
            - index.hidden_penalty
            + index.bonus
        )
        
        # Applica floor/ceiling
        index.score = max(weights.min_score, min(index.score, weights.max_score))
        
        # Rating testuale
        index.rating = UsabilityIndex.get_rating(index.score)
        
        return index


def calculate_all_metrics(
    tree_data: Dict[str, Any],
    hidden_sections_count: int = 0,
    all_sections_in_at: bool = False,
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
        all_sections_in_at
    )
    
    return reachability, quality, usability
