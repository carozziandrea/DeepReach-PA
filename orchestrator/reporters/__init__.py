"""
Package reporters - Contiene i diversi formati di output.

Per aggiungere un nuovo formato:
1. Crea un nuovo file (es. html_reporter.py)
2. Crea una classe che eredita da BaseReporter
3. Implementa il metodo report()
4. Aggiungi l'import qui sotto
"""

from reporters.base_reporter import BaseReporter
from reporters.console_reporter import ConsoleReporter
from reporters.json_reporter import JsonReporter
from reporters.privacy_reporter import (
    PrivacyTextReporter,
    PrivacyPDFReporter,
    generate_privacy_reports,
)
from reporters.report_generator import (
    FullAnalysisTextReporter,
    FullAnalysisPDFReporter,
    generate_full_reports,
)
from reporters.comparative_reporter import (
    ComparativeReporter,
    generate_batch_reports,
)

__all__ = [
    'BaseReporter',
    'ConsoleReporter',
    'JsonReporter',
    'PrivacyTextReporter',
    'PrivacyPDFReporter',
    'generate_privacy_reports',
    'FullAnalysisTextReporter',
    'FullAnalysisPDFReporter',
    'generate_full_reports',
    'ComparativeReporter',
    'generate_batch_reports',
]
