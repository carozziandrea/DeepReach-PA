"""
Chart Utilities - Genera grafici per i report PDF.

Utilizza matplotlib per creare pie chart, bar chart e altre visualizzazioni
che vengono poi incorporate nei PDF tramite ReportLab.
"""

import matplotlib
matplotlib.use('Agg')  # Backend non-interattivo per server/CLI

import matplotlib.pyplot as plt
from io import BytesIO
from typing import Dict, Optional, Tuple
from pathlib import Path


# Palette colori DeepReach-PA
COLORS = {
    'primary': '#2563eb',      # Blu PA
    'success': '#16a34a',      # Verde
    'warning': '#d97706',      # Arancione
    'danger': '#dc2626',       # Rosso
    'gray': '#6b7280',         # Grigio
    'light': '#f3f4f6',        # Grigio chiaro
    'cyan': '#17A2B8',         # Cyan (trasparenza)
}

# Colori per rischio privacy
PRIVACY_COLORS = {
    'high': '#dc2626',     # Rosso
    'medium': '#f59e0b',   # Arancione
    'low': '#fbbf24',      # Giallo
    'none': '#22c55e',     # Verde
}

# Colori per trasparenza
TRANSPARENCY_COLORS = {
    'present': '#16a34a',   # Verde - sezioni presenti
    'hidden': '#f59e0b',    # Arancione - trasparenza sommersa
    'missing': '#dc2626',   # Rosso - mancanti
}


def create_pie_chart(
    data: Dict[str, int],
    title: str,
    colors: Optional[Dict[str, str]] = None,
    figsize: Tuple[float, float] = (4, 4)
) -> BytesIO:
    """
    Crea un pie chart e lo ritorna come BytesIO per ReportLab.

    Args:
        data: Dizionario {label: valore}
        title: Titolo del grafico
        colors: Dizionario opzionale {label: colore}
        figsize: Dimensione figura (width, height) in pollici

    Returns:
        BytesIO contenente l'immagine PNG
    """
    # Filtra valori zero
    data = {k: v for k, v in data.items() if v > 0}

    if not data:
        # Nessun dato, crea grafico vuoto
        return _create_empty_chart("Nessun dato disponibile", figsize)

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')

    labels = list(data.keys())
    values = list(data.values())

    # Usa colori custom se forniti
    if colors:
        chart_colors = [colors.get(label, COLORS['gray']) for label in labels]
    else:
        chart_colors = plt.cm.Blues(
            [0.3 + 0.5 * i / len(labels) for i in range(len(labels))]
        )

    # Crea pie chart
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct='%1.0f%%',
        colors=chart_colors,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1},
    )

    # Styling testo
    for text in texts:
        text.set_fontsize(9)
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color('white')
        autotext.set_fontweight('bold')

    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)

    plt.tight_layout()

    # Salva in buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    plt.close(fig)

    return buffer


def create_bar_chart(
    data: Dict[str, int],
    title: str,
    xlabel: str = "",
    ylabel: str = "",
    colors: Optional[Dict[str, str]] = None,
    figsize: Tuple[float, float] = (5, 3),
    horizontal: bool = False
) -> BytesIO:
    """
    Crea un bar chart e lo ritorna come BytesIO per ReportLab.

    Args:
        data: Dizionario {label: valore}
        title: Titolo del grafico
        xlabel: Etichetta asse X
        ylabel: Etichetta asse Y
        colors: Dizionario opzionale {label: colore}
        figsize: Dimensione figura (width, height) in pollici
        horizontal: Se True, crea barre orizzontali

    Returns:
        BytesIO contenente l'immagine PNG
    """
    if not data:
        return _create_empty_chart("Nessun dato disponibile", figsize)

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')

    labels = list(data.keys())
    values = list(data.values())

    # Usa colori custom se forniti
    if colors:
        chart_colors = [colors.get(label, COLORS['primary']) for label in labels]
    else:
        chart_colors = [COLORS['primary']] * len(labels)

    if horizontal:
        bars = ax.barh(labels, values, color=chart_colors, edgecolor='white')
        ax.set_xlabel(ylabel)  # Invertiti per orizzontale
        ax.set_ylabel(xlabel)
    else:
        bars = ax.bar(labels, values, color=chart_colors, edgecolor='white')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

    # Aggiungi valori sulle barre
    for bar, value in zip(bars, values):
        if horizontal:
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                    str(value), va='center', fontsize=9)
        else:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    str(value), ha='center', fontsize=9)

    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    plt.close(fig)

    return buffer


def create_privacy_pie_chart(
    high: int,
    medium: int,
    low: int,
    none: int = 0
) -> BytesIO:
    """
    Crea pie chart specifico per distribuzione rischio privacy.

    Args:
        high: Conteggio rischio alto
        medium: Conteggio rischio medio
        low: Conteggio rischio basso
        none: Conteggio nessun rischio

    Returns:
        BytesIO contenente l'immagine PNG
    """
    data = {
        'Alto': high,
        'Medio': medium,
        'Basso': low,
    }

    colors = {
        'Alto': PRIVACY_COLORS['high'],
        'Medio': PRIVACY_COLORS['medium'],
        'Basso': PRIVACY_COLORS['low'],
    }

    return create_pie_chart(
        data,
        title="Distribuzione Rischio Privacy",
        colors=colors,
        figsize=(3.5, 3.5)
    )


def create_transparency_bar_chart(
    in_at: int,
    hidden: int,
    missing: int
) -> BytesIO:
    """
    Crea bar chart per analisi sezioni trasparenza.

    Args:
        in_at: Sezioni presenti in AT
        hidden: Sezioni fuori da AT (trasparenza sommersa)
        missing: Sezioni mancanti

    Returns:
        BytesIO contenente l'immagine PNG
    """
    data = {
        'In AT': in_at,
        'Fuori AT': hidden,
        'Mancanti': missing,
    }

    colors = {
        'In AT': TRANSPARENCY_COLORS['present'],
        'Fuori AT': TRANSPARENCY_COLORS['hidden'],
        'Mancanti': TRANSPARENCY_COLORS['missing'],
    }

    return create_bar_chart(
        data,
        title="Sezioni Trasparenza Obbligatorie",
        ylabel="Numero sezioni",
        colors=colors,
        figsize=(4.5, 3)
    )


def create_node_type_bar_chart(
    ok: int,
    transparency: int,
    broken: int,
    files: int,
    dynamic: int = 0
) -> BytesIO:
    """
    Crea bar chart per tipologia nodi del grafo.

    Args:
        ok: Pagine funzionanti
        transparency: Sezioni trasparenza
        broken: Link rotti
        files: File (PDF, etc.)
        dynamic: Contenuti dinamici

    Returns:
        BytesIO contenente l'immagine PNG
    """
    data = {
        'OK': ok,
        'Trasparenza': transparency,
        'Rotti': broken,
        'File': files,
    }

    if dynamic > 0:
        data['Dinamici'] = dynamic

    colors = {
        'OK': COLORS['primary'],
        'Trasparenza': COLORS['cyan'],
        'Rotti': COLORS['danger'],
        'File': COLORS['success'],
        'Dinamici': '#9D65C9',
    }

    return create_bar_chart(
        data,
        title="Tipologia Nodi",
        ylabel="Conteggio",
        colors=colors,
        figsize=(5, 3),
        horizontal=True
    )


def _create_empty_chart(message: str, figsize: Tuple[float, float]) -> BytesIO:
    """Crea un grafico vuoto con messaggio."""
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    ax.text(0.5, 0.5, message, ha='center', va='center',
            fontsize=10, color=COLORS['gray'])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buffer.seek(0)
    plt.close(fig)

    return buffer


def export_graph_to_png(
    G,
    output_path: Path,
    figsize: Tuple[float, float] = (16, 12),
    node_size: int = 300
) -> Optional[str]:
    """
    Esporta un grafo NetworkX come immagine PNG.

    Args:
        G: Grafo NetworkX
        output_path: Path per salvare l'immagine
        figsize: Dimensione figura
        node_size: Dimensione nodi

    Returns:
        Path al file salvato, o None se errore
    """
    try:
        import networkx as nx

        fig, ax = plt.subplots(figsize=figsize, facecolor='white')

        # Colori nodi basati su tipo
        node_colors = []
        root_node = None
        for node in G.nodes():
            node_data = G.nodes[node]
            if node_data.get('is_start', False):
                node_colors.append(COLORS['danger'])
                root_node = node
            elif node_data.get('is_transparency', False):
                node_colors.append(COLORS['cyan'])
            elif node_data.get('status') == 'broken':
                node_colors.append(COLORS['danger'])
            elif node_data.get('status') == 'file':
                node_colors.append(COLORS['success'])
            else:
                node_colors.append(COLORS['primary'])

        # Layout - usa layout radiale simile a force-directed
        if root_node and G.number_of_nodes() < 200:
            # Crea layout a shell (radiale) con root al centro
            try:
                # Organizza nodi per profondità
                depths = {}
                for node in G.nodes():
                    depth = G.nodes[node].get('depth', 0)
                    if depth not in depths:
                        depths[depth] = []
                    depths[depth].append(node)
                
                # Crea liste ordinate per profondità
                shells = [depths.get(d, []) for d in sorted(depths.keys())]
                if shells:
                    # Scala maggiore e rotazione per evitare sovrapposizioni
                    pos = nx.shell_layout(G, nlist=shells, scale=3, rotate=0.5)
                else:
                    pos = nx.spring_layout(G, k=4, iterations=150, seed=42, scale=3)
            except Exception:
                pos = nx.spring_layout(G, k=4, iterations=150, seed=42, scale=3)
        else:
            # Fallback: spring layout con parametri più spaziosi per grafi grandi
            pos = nx.spring_layout(G, k=3, iterations=100, seed=42, scale=3)

        # Dimensione nodi proporzionale al numero totale (più nodi = nodi più piccoli)
        adjusted_node_size = max(50, min(node_size, 400 - G.number_of_nodes()))

        # Disegna grafo
        nx.draw(
            G, pos, ax=ax,
            node_color=node_colors,
            node_size=adjusted_node_size,
            with_labels=False,
            edge_color='#dddddd',
            arrows=True,
            arrowsize=8,
            alpha=0.85,
            width=0.5
        )

        ax.set_title("Mappa del Sito", fontsize=14, fontweight='bold')

        # Legenda colori nodi
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['danger'],
                   markersize=10, label='Homepage'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['cyan'],
                   markersize=10, label='Sezione AT'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['success'],
                   markersize=10, label='File'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['primary'],
                   markersize=10, label='Pagina'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', framealpha=0.9, fontsize=9)

        plt.tight_layout()
        plt.savefig(output_path, format='png', dpi=150,
                    bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return str(output_path)

    except Exception as e:
        print(f"[WARN] Impossibile esportare grafo come PNG: {e}")
        return None
