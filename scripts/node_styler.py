"""
Node Styler - Definisce stili visivi per i nodi del grafo.

Gestisce colori, forme ed emoji per diversi tipi di nodi:
- Homepage, pagine dinamiche, file scaricabili
- Link rotti, sezioni trasparenza
- Indicatori visivi per rischio privacy
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class NodeStyle:
    color: str
    shape: str
    emoji: str
    title_prefix: str
    border_width: int = 1
    border_color: Optional[str] = None  # Per privacy risk

    def format_label(self, base_label: str) -> str:
        return f"{self.emoji} {base_label}"

    def format_title(self, **kwargs) -> str:
        raise NotImplementedError("Deve essere implementato nelle sottoclassi")


class NodeStyler:
    # Palette colori
    COLORS = {
        "blue": "#4A90E2",
        "orange": "#F5A623",
        "red": "#D0021B",
        "green": "#7ED321",
        "purple": "#9D65C9",
        "cyan": "#17A2B8",  # Per sezioni trasparenza obbligatorie
    }

    # Colori bordo per rischio privacy
    PRIVACY_BORDER_COLORS = {
        "high": "#FF0000",    # Rosso
        "medium": "#FFA500",  # Arancione
        "low": "#FFD700",     # Giallo/oro
        "none": None,         # Nessun bordo speciale
    }

    PRIVACY_BORDER_WIDTHS = {
        "high": 4,
        "medium": 3,
        "low": 2,
        "none": 1,
    }

    # Configurazioni per tipo di nodo
    STYLES = {
        "start": {
            "color": COLORS["red"],
            "shape": "star",
            "emoji": "🏠",
            "border_width": 3,
        },
        "dynamic": {
            "color": COLORS["purple"],
            "shape": "diamond",
            "emoji": "🔄",
            "border_width": 1,
        },
        "file": {
            "color": COLORS["green"],
            "shape": "dot",
            "emoji": "📄",
            "border_width": 1,
        },
        "broken": {
            "color": COLORS["red"],
            "shape": "triangle",
            "emoji": "❌",
            "border_width": 3,
        },
        "pending": {
            "color": COLORS["orange"],
            "shape": "dot",
            "emoji": "⏳",
            "border_width": 1,
        },
        "ok": {
            "color": COLORS["blue"],
            "shape": "dot",
            "emoji": "✓",
            "border_width": 1,
        },
        "transparency": {
            "color": COLORS["cyan"],
            "shape": "dot",
            "emoji": "📋",
            "border_width": 2,
        },
    }

    @classmethod
    def get_node_type(cls, node_data: dict) -> str:
        if node_data.get("is_start", False):
            return "start"
        elif node_data.get("is_dynamic", False):
            return "dynamic"
        elif node_data.get("status") == "file":
            return "file"
        elif node_data.get("status") == "broken":
            return "broken"
        elif node_data.get("status") == "pending":
            return "pending"
        elif node_data.get("is_transparency", False):
            return "transparency"
        else:
            return "ok"

    @classmethod
    def get_style(cls, node_type: str) -> dict:
        return cls.STYLES.get(node_type, cls.STYLES["ok"])

    @classmethod
    def get_privacy_style(cls, node_data: dict) -> dict:
        """
        Restituisce stile bordo basato sul rischio privacy.

        Il bordo si aggiunge allo stile base del nodo.
        Solo nodi con rischio medium o high ottengono un bordo colorato.
        """
        privacy_risk = node_data.get("privacy_risk", "none")

        # Solo rischio medium o high ottengono bordo colorato
        if privacy_risk not in ["high", "medium"]:
            return {}

        return {
            "border_color": cls.PRIVACY_BORDER_COLORS.get(privacy_risk),
            "border_width": cls.PRIVACY_BORDER_WIDTHS.get(privacy_risk, 1),
        }

    @classmethod
    def get_privacy_tooltip_section(cls, node_data: dict) -> str:
        """Genera la sezione privacy per il tooltip."""
        privacy_risk = node_data.get("privacy_risk", "none")

        if privacy_risk == "none" or privacy_risk is None:
            return ""

        # Etichette rischio
        risk_labels = {
            "high": "ALTO",
            "medium": "MEDIO",
            "low": "BASSO",
        }

        risk_emoji = {
            "high": "🔴",
            "medium": "🟠",
            "low": "🟡",
        }

        lines = [f"\n{risk_emoji.get(privacy_risk, '')} Privacy Risk: {risk_labels.get(privacy_risk, privacy_risk)}"]

        # Aggiungi dettagli findings
        findings = node_data.get("privacy_findings", [])
        if findings:
            finding_strs = []
            for f in findings:
                pattern_type = f.get("type", "unknown")
                count = f.get("count", 0)
                finding_strs.append(f"{pattern_type}: {count}")
            lines.append("Trovati: " + ", ".join(finding_strs))

        return "\n".join(lines)

    @classmethod
    def format_tooltip(
        cls, node: str, node_data: dict, node_type: str, degree: int
    ) -> str:
        status_code = node_data.get("status_code", "N/A")
        distance = node_data.get("distance", 0)

        # Sezione privacy (aggiunta in fondo al tooltip)
        privacy_section = cls.get_privacy_tooltip_section(node_data)

        if node_type == "start":
            base = f"🏠 PAGINA INIZIALE\nURL: {node}\nDistanza: {distance}\nConnessioni: {degree}"
            return base + privacy_section

        elif node_type == "dynamic":
            dynamic_label = node_data.get("dynamic_label", "N/A")
            base = f"🔄 CONTENUTO DINAMICO\nSezione: {dynamic_label}\nURL: {node}\nDistanza: {distance}\nConnessioni: {degree}"
            return base + privacy_section

        elif node_type == "file":
            file_type = node_data.get("file_type", "unknown")
            base = f"📄 FILE SCARICABILE\nTipo: {file_type}\nURL: {node}\nDistanza: {distance}"
            return base + privacy_section

        elif node_type == "broken":
            error_msg = node_data.get("error", "Errore sconosciuto")
            base = f"❌ LINK ROTTO\nURL: {node}\nStatus: {status_code}\nDistanza: {distance}\nErrore: {error_msg}"
            return base + privacy_section

        elif node_type == "transparency":
            section_name = node_data.get("transparency_section", "Sezione obbligatoria")
            title = node_data.get("title", "N/A")
            base = f"📋 SEZIONE TRASPARENZA\nSezione: {section_name}\nURL: {node}\nTitolo: {title}\nDistanza: {distance}\nConnessioni: {degree}"
            return base + privacy_section

        else:
            title = node_data.get("title", "N/A")
            base = f"✓ URL: {node}\nStatus: {status_code}\nTitolo: {title}\nDistanza: {distance}\nConnessioni: {degree}"
            return base + privacy_section