"""
Analizzatore privacy per contenuti web.

Questo modulo orchestra la scansione privacy di:
1. Contenuti HTML delle pagine (estratti durante il crawl)
2. File PDF scaricati post-crawl

Il processo avviene DOPO il crawl principale per non rallentarlo.
"""

import json
import time
import tempfile
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import urlparse

from content_scanner import ContentScanner, PrivacyScanResult, PrivacyFinding


@dataclass
class PrivacyAnalysisConfig:
    """Configurazione per l'analisi privacy."""

    # Download settings
    download_delay: float = 0.5  # Secondi tra i download
    download_timeout: int = 30  # Timeout per singolo download
    max_file_size_mb: int = 50  # Max dimensione file da scaricare
    max_pdfs_per_site: int = 0  # Max PDF da scansionare per sito (0 = nessun limite)

    # Scan settings
    scan_html: bool = True  # Scansiona contenuto HTML
    scan_files: bool = True  # Scarica e scansiona PDF/docs
    max_content_length: int = 100000  # Max caratteri per scansione HTML

    # File types to scan
    scannable_extensions: List[str] = field(default_factory=lambda: [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".odt", ".ods"
    ])


@dataclass
class PrivacyAnalysisSummary:
    """Riepilogo dell'analisi privacy."""

    total_scanned: int = 0
    pages_scanned: int = 0
    files_scanned: int = 0
    files_downloaded: int = 0
    files_failed: int = 0

    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0

    high_risk_urls: List[str] = field(default_factory=list)
    medium_risk_urls: List[str] = field(default_factory=list)

    # Ritrovamenti per tipo
    findings_by_type: Dict[str, int] = field(default_factory=dict)

    # Errori
    errors: List[str] = field(default_factory=list)

    # Suggerimenti di remediation
    remediation_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "total_scanned": self.total_scanned,
            "pages_scanned": self.pages_scanned,
            "files_scanned": self.files_scanned,
            "files_downloaded": self.files_downloaded,
            "files_failed": self.files_failed,
            "high_risk_count": self.high_risk_count,
            "medium_risk_count": self.medium_risk_count,
            "low_risk_count": self.low_risk_count,
            "high_risk_urls": self.high_risk_urls[:20],  # Limita per report
            "medium_risk_urls": self.medium_risk_urls[:20],
            "findings_by_type": self.findings_by_type,
            "errors": self.errors[:10],
        }


class PrivacyAnalyzer:
    """
    Analizzatore privacy per siti web.

    Workflow:
    1. Carica site_tree.json dal crawl
    2. Scansiona contenuti HTML salvati nei nodi
    3. Scarica e scansiona file PDF/doc uno alla volta
    4. Aggiorna i nodi con informazioni privacy
    5. Salva site_tree aggiornato
    """

    def __init__(self, config: PrivacyAnalysisConfig = None):
        self.config = config or PrivacyAnalysisConfig()
        self.scanner = ContentScanner()
        self.summary = PrivacyAnalysisSummary()

    def analyze_tree(self, tree: Dict[str, Any], base_url: str = None) -> Tuple[Dict[str, Any], PrivacyAnalysisSummary]:
        """
        Analizza l'intero site tree per privacy.

        Args:
            tree: Dizionario con la struttura del sito
            base_url: URL base del sito (per costruire URL assoluti)

        Returns:
            Tuple di (tree aggiornato, summary)
        """
        self.summary = PrivacyAnalysisSummary()

        # Fase 1: Scansiona contenuti HTML
        if self.config.scan_html:
            print("\n[Privacy] Scansione contenuti HTML...")
            self._scan_html_content(tree)

        # Fase 2: Scarica e scansiona file
        if self.config.scan_files:
            print("\n[Privacy] Download e scansione file...")
            self._scan_files(tree, base_url)

        # Calcola conteggi finali
        self._update_summary_counts(tree)

        return tree, self.summary

    def _scan_html_content(self, tree: Dict[str, Any]) -> None:
        """Scansiona i contenuti HTML salvati nei nodi."""
        for url, node_data in tree.items():
            if not isinstance(node_data, dict):
                continue

            # Salta file
            if node_data.get("status") == "file":
                continue

            # Cerca contenuto HTML salvato
            content = node_data.get("content_text", "")
            if not content:
                continue

            # Limita lunghezza
            if len(content) > self.config.max_content_length:
                content = content[:self.config.max_content_length]

            # Scansiona
            result = self.scanner.scan_text(content)
            self.summary.pages_scanned += 1

            # Aggiorna nodo con risultati
            if result.has_sensitive_data:
                self._update_node_privacy(node_data, result)
            else:
                node_data["privacy_risk"] = "none"
                node_data["privacy_findings"] = []

    def _scan_files(self, tree: Dict[str, Any], base_url: str = None) -> None:
        """Scarica e scansiona i file PDF/doc."""
        try:
            import requests
        except ImportError:
            self.summary.errors.append(
                "Libreria 'requests' non installata. Scansione file saltata."
            )
            return

        # Raccogli URL file da scansionare
        file_urls = []
        for url, node_data in tree.items():
            if not isinstance(node_data, dict):
                continue

            if node_data.get("status") == "file":
                # Recupera file_type gestendo eventuali valori None
                file_type = (node_data.get("file_type") or "").lower()
                url_lower = url.lower()
                
                # Se il tipo è mancante, prova a dedurlo dall'URL (es. .pdf/ o .pdf?)
                if not file_type:
                    for ext in self.config.scannable_extensions:
                        if (ext + "/") in url_lower or (ext + "?") in url_lower:
                            file_type = ext
                            node_data["file_type"] = ext  # Aggiorna il nodo per i passaggi success
                            break
                
                # Usa le estensioni configurate
                if any(file_type.endswith(ext) or ext in file_type for ext in self.config.scannable_extensions):
                    file_urls.append((url, node_data))

        total_found = len(file_urls)

        # Limita numero PDF se configurato
        if self.config.max_pdfs_per_site > 0 and total_found > self.config.max_pdfs_per_site:
            file_urls = file_urls[:self.config.max_pdfs_per_site]
            print(f"[Privacy] Trovati {total_found} file, limitato a {self.config.max_pdfs_per_site}")
        else:
            print(f"[Privacy] Trovati {total_found} file da analizzare")

        if not file_urls:
            return

        # Scarica e scansiona uno alla volta
        scanned_count = 0
        failed_count = 0
        for url, node_data in file_urls:
            # Check if already has privacy data (skip re-scan)
            if "privacy_risk" in node_data and node_data.get("privacy_scanned"):
                continue

            result = self._download_and_scan(url, (node_data.get("file_type") or ""))

            if result.error:
                self.summary.files_failed += 1
                self.summary.errors.append(f"{url}: {result.error}")
                node_data["privacy_risk"] = "unknown"
                node_data["privacy_error"] = result.error
                failed_count += 1
                # Mostra primo errore come diagnostica
                if failed_count == 1:
                    print(f"  [X] Primo errore: {result.error}")
            else:
                self.summary.files_downloaded += 1
                self.summary.files_scanned += 1
                scanned_count += 1

                if result.has_sensitive_data:
                    self._update_node_privacy(node_data, result)
                else:
                    node_data["privacy_risk"] = "none"
                    node_data["privacy_findings"] = []

            node_data["privacy_scanned"] = True

            # Progress ogni 50 file
            processed = scanned_count + failed_count
            if processed % 50 == 0:
                print(f"  [Privacy] Progresso: {processed}/{len(file_urls)} file processati")

            # Delay tra download
            time.sleep(self.config.download_delay)

        # Riepilogo finale
        print(f"[Privacy] Completato: {scanned_count} scansionati, {failed_count} falliti")

    def _download_and_scan(self, url: str, file_type: str) -> PrivacyScanResult:
        """Scarica un file e lo scansiona per dati sensibili."""
        try:
            import requests
        except ImportError:
            return PrivacyScanResult(error="Libreria requests non disponibile")

        try:
            print(f"  Scaricando: {url[:80]}...")

            # Download con timeout
            response = requests.get(
                url,
                timeout=self.config.download_timeout,
                stream=True,
                headers={
                    "User-Agent": "Mozilla/5.0 DeepReach-PA Privacy Scanner"
                }
            )
            response.raise_for_status()

            # Controlla dimensione
            content_length = response.headers.get("content-length")
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > self.config.max_file_size_mb:
                    return PrivacyScanResult(
                        error=f"File troppo grande: {size_mb:.1f}MB"
                    )

            # Leggi contenuto
            content = response.content

            # Scansiona in base al tipo
            if ".pdf" in file_type.lower():
                return self.scanner.scan_pdf_from_bytes(content)
            else:
                # Per altri formati, prova estrazione base
                # (TODO: supporto DOC/DOCX con python-docx)
                return PrivacyScanResult(
                    error=f"Formato {file_type} non ancora supportato"
                )

        except requests.Timeout:
            return PrivacyScanResult(error="Timeout durante il download")
        except requests.RequestException as e:
            return PrivacyScanResult(error=f"Errore download: {str(e)}")
        except Exception as e:
            return PrivacyScanResult(error=f"Errore imprevisto: {str(e)}")

    def _update_node_privacy(self, node_data: Dict, result: PrivacyScanResult) -> None:
        """Aggiorna un nodo con i risultati privacy."""
        node_data["privacy_risk"] = result.risk_level
        node_data["privacy_findings"] = [f.to_dict() for f in result.findings]
        node_data["privacy_total_findings"] = result.total_findings

    def _update_summary_counts(self, tree: Dict[str, Any]) -> None:
        """Aggiorna i conteggi nel summary."""
        for url, node_data in tree.items():
            if not isinstance(node_data, dict):
                continue

            risk = node_data.get("privacy_risk", "none")

            if risk == "high":
                self.summary.high_risk_count += 1
                self.summary.high_risk_urls.append(url)
            elif risk == "medium":
                self.summary.medium_risk_count += 1
                self.summary.medium_risk_urls.append(url)
            elif risk == "low":
                self.summary.low_risk_count += 1

            # Conta findings per tipo
            for finding in node_data.get("privacy_findings", []):
                pattern_type = finding.get("type", "unknown")
                count = finding.get("count", 0)
                if pattern_type in self.summary.findings_by_type:
                    self.summary.findings_by_type[pattern_type] += count
                else:
                    self.summary.findings_by_type[pattern_type] = count

        self.summary.total_scanned = (
            self.summary.pages_scanned + self.summary.files_scanned
        )

        # Genera suggerimenti di remediation basati sui tipi di dati trovati
        self.summary.remediation_suggestions = self.scanner.get_remediation_suggestions(
            self.summary.findings_by_type,
            has_high_risk=(self.summary.high_risk_count > 0)
        )


def analyze_site_tree_privacy(
    tree_path: str,
    output_path: str = None,
    config: PrivacyAnalysisConfig = None
) -> Tuple[Dict[str, Any], PrivacyAnalysisSummary]:
    """
    Funzione di utilità per analizzare un site_tree.json esistente.

    Args:
        tree_path: Percorso al file site_tree.json
        output_path: Percorso per salvare il tree aggiornato (opzionale)
        config: Configurazione opzionale

    Returns:
        Tuple di (tree aggiornato, summary)
    """
    # Carica tree
    with open(tree_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tree = data.get("tree", data)

    # Estrai base URL
    base_url = None
    if "metadata" in data:
        base_url = data["metadata"].get("start_url")

    # Analizza
    analyzer = PrivacyAnalyzer(config)
    updated_tree, summary = analyzer.analyze_tree(tree, base_url)

    # Salva se richiesto
    if output_path:
        output_data = data.copy() if isinstance(data, dict) else {"tree": updated_tree}
        output_data["tree"] = updated_tree
        output_data["privacy_summary"] = summary.to_dict()

        # Assicura che la cartella di output esista
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n[Privacy] Tree aggiornato salvato in: {output_path}")

    return updated_tree, summary
