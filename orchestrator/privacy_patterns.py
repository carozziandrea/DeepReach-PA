"""
Configurazione dei pattern per il rilevamento di dati personali sensibili.

=============================================================================
  ISTRUZIONI PER MANUTENTORI / UTILIZZATORI
=============================================================================

Questo file contiene le regole (espressioni regolari) usate dal sistema
per rilevare dati personali sensibili nelle pagine e nei documenti di un
sito della Pubblica Amministrazione.

COME MODIFICARE LE REGOLE:
  - Ogni voce di PRIVACY_PATTERNS è una coppia  "nome": r"regex"
  - Per AGGIUNGERE un nuovo tipo di dato sensibile, aggiungere una riga
    al dizionario con un nome univoco e la regex corrispondente.
  - Per RIMUOVERE un pattern, basta cancellare o commentare la riga.
  - Per MODIFICARE un pattern, aggiornare la regex.

COME MODIFICARE I SUGGERIMENTI:
  - REMEDIATION_SUGGESTIONS contiene i consigli mostrati nel report per
    ogni tipo di dato trovato. Le chiavi devono corrispondere a quelle
    di PRIVACY_PATTERNS.
  - GENERAL_HIGH_RISK_SUGGESTIONS sono suggerimenti aggiunti quando il
    rischio complessivo è alto.

ESEMPIO — aggiungere un pattern per il numero di Partita IVA:

    PRIVACY_PATTERNS["partita_iva"] = r"\\bIT\\d{11}\\b"

    REMEDIATION_SUGGESTIONS["partita_iva"] = [
        "Valutare se la P.IVA è strettamente necessaria",
    ]

=============================================================================
"""

from typing import Dict, List


# =============================================================================
# PATTERN PER DATI SENSIBILI (ITALIANO)
# =============================================================================

PRIVACY_PATTERNS: Dict[str, str] = {
    # Codice Fiscale italiano (16 caratteri alfanumerici)
    "codice_fiscale": r"\b[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]\b",

    # IBAN italiano (27 caratteri: IT + 2 cifre controllo + 1 lettera CIN
    # + 5 cifre ABI + 5 cifre CAB + 12 cifre conto)
    "iban": r"\bIT\d{2}[A-Z]\d{10}[A-Z0-9]{12}\b",

    # Email (pattern generico)
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",

    # Telefono italiano (fisso e mobile, con prefisso +39)
    "telefono": r"\b(?:\+39\s?)?(?:0\d{1,4}[\s.-]?\d{5,8}|\d{3}[\s.-]?\d{6,7})\b",

    # Indirizzo (via, piazza, corso, viale, largo + nome + numero civico)
    "indirizzo": r"\b(?:via|piazza|corso|viale|largo|vicolo|piazzale)\s+[A-Za-z\s']+,?\s*\d{1,5}(?:\s*[a-zA-Z])?\b",
}


# Pattern aggiuntivi per rilevare tabelle con dati personali
TABLE_HEADER_PATTERNS: List[str] = [
    r"nome\s*(?:e\s*)?cognome",
    r"cognome\s*(?:e\s*)?nome",
    r"nominativo",
    r"codice\s*fiscale",
    r"c\.?f\.?",
    r"data\s*(?:di\s*)?nascita",
]


# =============================================================================
# SUGGERIMENTI DI REMEDIATION PER TIPO DI DATO
# =============================================================================

REMEDIATION_SUGGESTIONS: Dict[str, List[str]] = {
    "codice_fiscale": [
        "Rimuovere codici fiscali da documenti pubblici",
        "Utilizzare riferimenti anonimi (es. numero pratica)",
    ],
    "iban": [
        "Non pubblicare IBAN completi online",
        "Se necessario, mascherare le ultime 12 cifre",
    ],
    "email": [
        "Centralizzare i contatti in una pagina dedicata",
        "Usare form di contatto invece di email in chiaro",
    ],
    "telefono": [
        "Ridurre l'esposizione di numeri diretti",
        "Preferire un numero di centralino unico",
    ],
    "indirizzo": [
        "Limitare gli indirizzi alle sole pagine di contatto/sedi",
    ],
}

# Suggerimenti generali per rischio alto
GENERAL_HIGH_RISK_SUGGESTIONS: List[str] = [
    "Verificare la necessita di pubblicazione dei dati personali",
    "Richiedere revisione privacy al DPO",
]

# Link a risorse esterne
PRIVACY_RESOURCES: Dict[str, str] = {
    "Linee guida AGID": "https://www.agid.gov.it/it/agenzia/stampa-e-comunicazione/notizie/2024/09/09/pubblicazione-linee-guida-accessibilita",
    "Garante Privacy - Trasparenza PA": "https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9556625",
    "FAQ Trasparenza e Privacy": "https://www.garanteprivacy.it/faq/trasparenza-e-privacy",
}
