"""
DeepReach-PA Orchestrator

Pacchetto per l'analisi automatica della trasparenza dei siti della PA.
"""

from config import OrchestratorConfig, default_config
from models import AnalysisResult
from homepage_checker import HomepageChecker
from crawler_runner import CrawlerRunner
from analyzer import Analyzer

__version__ = "0.1.0"
__all__ = [
    'OrchestratorConfig',
    'default_config',
    'AnalysisResult',
    'HomepageChecker',
    'CrawlerRunner',
    'Analyzer',
]
