"""
Scanner per rilevamento dati personali sensibili.

Questo modulo analizza il contenuto testuale di pagine HTML e file PDF
per identificare dati personali come codici fiscali, IBAN, email, ecc.

Solo il contenuto effettivo viene analizzato, non gli URL.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# I pattern e i suggerimenti sono definiti in privacy_patterns.py
# per permettere facile personalizzazione da parte di manutentori/utilizzatori.
from privacy_patterns import (
    PRIVACY_PATTERNS,
    TABLE_HEADER_PATTERNS,
    REMEDIATION_SUGGESTIONS,
    GENERAL_HIGH_RISK_SUGGESTIONS,
    PRIVACY_RESOURCES,
)


@dataclass
class PrivacyFinding:
    """Singolo ritrovamento di dato sensibile."""

    pattern_type: str  # "codice_fiscale", "email", ecc.
    count: int  # Quante occorrenze trovate
    samples: List[str] = field(default_factory=list)  # Esempi (parzialmente oscurati)

    def to_dict(self) -> Dict:
        return {
            "type": self.pattern_type,
            "count": self.count,
            "samples": self.samples[:5],  # Max 5 esempi
        }


@dataclass
class PrivacyScanResult:
    """Risultato della scansione privacy di un contenuto."""

    has_sensitive_data: bool = False
    risk_level: str = "none"  # none, low, medium, high
    findings: List[PrivacyFinding] = field(default_factory=list)
    total_findings: int = 0
    scanned_chars: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "has_sensitive_data": self.has_sensitive_data,
            "risk_level": self.risk_level,
            "total_findings": self.total_findings,
            "findings": [f.to_dict() for f in self.findings],
            "scanned_chars": self.scanned_chars,
            "error": self.error,
        }


class ContentScanner:
    """
    Scanner per rilevamento dati personali sensibili nel contenuto.

    Analizza testo estratto da HTML o PDF e identifica pattern
    di dati personali italiani.
    """

    def __init__(self, patterns: Dict[str, str] = None):
        """
        Inizializza lo scanner con i pattern configurati.

        Args:
            patterns: Dizionario di pattern regex. Se None, usa i default.
        """
        self.patterns = patterns or PRIVACY_PATTERNS
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compila i pattern regex per performance migliori."""
        for name, pattern in self.patterns.items():
            try:
                self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                print(f"Errore compilazione pattern '{name}': {e}")

    def _redact_sample(self, text: str, pattern_type: str) -> str:
        """
        Oscura parzialmente un campione per il report.

        Es: "RSSMRA85M01H501Z" -> "RSS***85M01H***Z"
        Es: "mario.rossi@email.it" -> "mar***@email.it"
        """
        if pattern_type == "codice_fiscale" and len(text) == 16:
            return f"{text[:3]}***{text[6:11]}***{text[15]}"
        elif pattern_type == "iban" and len(text) >= 20:
            return f"{text[:4]}****{text[-4:]}"
        elif pattern_type == "email" and "@" in text:
            local, domain = text.split("@", 1)
            if len(local) > 3:
                return f"{local[:3]}***@{domain}"
            return f"***@{domain}"
        elif pattern_type == "telefono":
            if len(text) > 6:
                return f"{text[:3]}***{text[-3:]}"
            return "***"
        elif pattern_type == "indirizzo":
            # Oscura il numero civico
            parts = text.rsplit(" ", 1)
            if len(parts) == 2:
                return f"{parts[0]} ***"
            return text
        return text[:5] + "***" if len(text) > 5 else "***"

    def scan_text(self, text: str, max_samples: int = 5) -> PrivacyScanResult:
        """
        Scansiona testo per dati personali sensibili.

        Args:
            text: Testo da analizzare
            max_samples: Numero massimo di campioni da includere per pattern

        Returns:
            PrivacyScanResult con i ritrovamenti
        """
        if not text or not text.strip():
            return PrivacyScanResult(scanned_chars=0)

        result = PrivacyScanResult(scanned_chars=len(text))
        findings: Dict[str, PrivacyFinding] = {}

        # Scansione per ogni tipo di pattern
        for pattern_name, compiled_pattern in self._compiled_patterns.items():
            matches = compiled_pattern.findall(text)

            if matches:
                # Rimuovi duplicati mantenendo l'ordine
                unique_matches = list(dict.fromkeys(matches))

                # Crea campioni oscurati
                samples = [
                    self._redact_sample(m, pattern_name)
                    for m in unique_matches[:max_samples]
                ]

                findings[pattern_name] = PrivacyFinding(
                    pattern_type=pattern_name,
                    count=len(matches),
                    samples=samples
                )

        # Calcola risultato
        if findings:
            result.has_sensitive_data = True
            result.findings = list(findings.values())
            result.total_findings = sum(f.count for f in result.findings)
            result.risk_level = self._calculate_risk_level(findings)

        return result

    def _calculate_risk_level(self, findings: Dict[str, PrivacyFinding]) -> str:
        """
        Calcola il livello di rischio in base ai ritrovamenti.

        Logica:
        - HIGH: Codici fiscali O IBAN trovati (dati identificativi diretti)
        - MEDIUM: Email multiple O telefoni multipli in formato lista
        - LOW: Singoli contatti (1-2 email/telefoni)
        - NONE: Nessun dato sensibile
        """
        # HIGH: dati identificativi diretti
        if "codice_fiscale" in findings or "iban" in findings:
            return "high"

        # Conta email e telefoni
        email_count = findings.get("email", PrivacyFinding("email", 0)).count
        phone_count = findings.get("telefono", PrivacyFinding("telefono", 0)).count
        address_count = findings.get("indirizzo", PrivacyFinding("indirizzo", 0)).count

        # MEDIUM: liste di contatti
        if email_count > 3 or phone_count > 3 or (email_count + phone_count) > 5:
            return "medium"

        # MEDIUM: indirizzi multipli
        if address_count > 2:
            return "medium"

        # LOW: singoli contatti
        if email_count > 0 or phone_count > 0 or address_count > 0:
            return "low"

        return "none"

    def get_remediation_suggestions(
        self,
        findings_by_type: Dict[str, int],
        has_high_risk: bool = False
    ) -> List[str]:
        """
        Genera suggerimenti di remediation basati sui tipi di dati trovati.

        Args:
            findings_by_type: Dizionario {pattern_type: count}
            has_high_risk: True se ci sono nodi ad alto rischio

        Returns:
            Lista di suggerimenti unici
        """
        suggestions = []
        seen = set()

        # Suggerimenti per ogni tipo di dato trovato
        for pattern_type, count in findings_by_type.items():
            if pattern_type in REMEDIATION_SUGGESTIONS:
                for suggestion in REMEDIATION_SUGGESTIONS[pattern_type]:
                    if suggestion not in seen:
                        suggestions.append(suggestion)
                        seen.add(suggestion)

        # Suggerimenti generali per rischio alto
        if has_high_risk:
            for suggestion in GENERAL_HIGH_RISK_SUGGESTIONS:
                if suggestion not in seen:
                    suggestions.append(suggestion)
                    seen.add(suggestion)

        return suggestions

    def scan_html(self, html_content: str) -> PrivacyScanResult:
        """
        Estrae testo da HTML e lo scansiona.

        Args:
            html_content: Contenuto HTML grezzo

        Returns:
            PrivacyScanResult con i ritrovamenti
        """
        # Rimuovi tag HTML per estrarre solo testo
        text = self._extract_text_from_html(html_content)
        return self.scan_text(text)

    def _extract_text_from_html(self, html: str) -> str:
        """Estrae testo pulito da HTML."""
        import re

        # Rimuovi script e style
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Rimuovi tag HTML
        text = re.sub(r'<[^>]+>', ' ', html)

        # Normalizza spazi
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def scan_pdf(self, pdf_path: str) -> PrivacyScanResult:
        """
        Estrae testo da PDF e lo scansiona.

        Args:
            pdf_path: Percorso al file PDF

        Returns:
            PrivacyScanResult con i ritrovamenti
        """
        try:
            import pdfplumber
        except ImportError:
            return PrivacyScanResult(
                error="Libreria pdfplumber non installata. Esegui: pip install pdfplumber"
            )

        try:
            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            full_text = "\n".join(text_parts)
            return self.scan_text(full_text)

        except Exception as e:
            return PrivacyScanResult(error=f"Errore lettura PDF: {str(e)}")

    def scan_pdf_from_bytes(self, pdf_bytes: bytes) -> PrivacyScanResult:
        """
        Scansiona un PDF da bytes (utile per file scaricati in memoria).

        Args:
            pdf_bytes: Contenuto del PDF in bytes

        Returns:
            PrivacyScanResult con i ritrovamenti
        """
        try:
            import pdfplumber
            from io import BytesIO
        except ImportError:
            return PrivacyScanResult(
                error="Libreria pdfplumber non installata. Esegui: pip install pdfplumber"
            )

        try:
            text_parts = []

            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            full_text = "\n".join(text_parts)
            return self.scan_text(full_text)

        except Exception as e:
            return PrivacyScanResult(error=f"Errore lettura PDF: {str(e)}")


# Funzioni di utilità
def merge_scan_results(results: List[PrivacyScanResult]) -> PrivacyScanResult:
    """
    Unisce più risultati di scansione in uno solo.

    Utile quando si scansionano più pagine/file.
    """
    if not results:
        return PrivacyScanResult()

    merged = PrivacyScanResult()
    findings_by_type: Dict[str, PrivacyFinding] = {}

    for result in results:
        merged.scanned_chars += result.scanned_chars

        for finding in result.findings:
            if finding.pattern_type in findings_by_type:
                # Somma i conteggi
                existing = findings_by_type[finding.pattern_type]
                existing.count += finding.count
                # Aggiungi nuovi campioni unici
                for sample in finding.samples:
                    if sample not in existing.samples and len(existing.samples) < 10:
                        existing.samples.append(sample)
            else:
                findings_by_type[finding.pattern_type] = PrivacyFinding(
                    pattern_type=finding.pattern_type,
                    count=finding.count,
                    samples=finding.samples.copy()
                )

    merged.findings = list(findings_by_type.values())
    merged.total_findings = sum(f.count for f in merged.findings)
    merged.has_sensitive_data = merged.total_findings > 0

    # Ricalcola risk level
    if merged.has_sensitive_data:
        scanner = ContentScanner()
        merged.risk_level = scanner._calculate_risk_level(findings_by_type)

    return merged
