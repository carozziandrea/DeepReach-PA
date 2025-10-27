import networkx as nx
from pyvis.network import Network
import json
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional

@dataclass
class NodeStyle:
    color: str
    shape: str
    emoji: str
    title_prefix: str
    border_width: int = 1
    
    def format_label(self, base_label: str) -> str:
        return f"{self.emoji} {base_label}"
    
    def format_title(self, **kwargs) -> str:
        raise NotImplementedError("Deve essere implementato nelle sottoclassi")


class NodeStyler:
    
    # Palette colori
    COLORS = {
        'blue': '#4A90E2',
        'orange': '#F5A623',
        'red': '#D0021B',
        'green': '#7ED321',
        'purple': '#9D65C9'
    }
    
    # Configurazioni per tipo di nodo
    STYLES = {
        'start': {
            'color': COLORS['red'],
            'shape': 'star',
            'emoji': '🏠',
            'border_width': 3
        },
        'dynamic': {
            'color': COLORS['purple'],
            'shape': 'diamond',
            'emoji': '🔄',
            'border_width': 1
        },
        'file': {
            'color': COLORS['green'],
            'shape': 'dot',
            'emoji': '📄',
            'border_width': 1
        },
        'broken': {
            'color': COLORS['red'],
            'shape': 'triangle',
            'emoji': '❌',
            'border_width': 3
        },
        'pending': {
            'color': COLORS['orange'],
            'shape': 'dot',
            'emoji': '⏳',
            'border_width': 1
        },
        'ok': {
            'color': COLORS['blue'],
            'shape': 'dot',
            'emoji': '✓',
            'border_width': 1
        }
    }
    
    @classmethod
    def get_node_type(cls, node_data: dict) -> str:
        if node_data.get('is_start', False):
            return 'start'
        elif node_data.get('is_dynamic', False):
            return 'dynamic'
        elif node_data.get('status') == 'file':
            return 'file'
        elif node_data.get('status') == 'broken':
            return 'broken'
        elif node_data.get('status') == 'pending':
            return 'pending'
        else:
            return 'ok'
    
    @classmethod
    def get_style(cls, node_type: str) -> dict:
        return cls.STYLES.get(node_type, cls.STYLES['ok'])
    
    @classmethod
    def format_tooltip(cls, node: str, node_data: dict, node_type: str, degree: int) -> str:
        status_code = node_data.get('status_code', 'N/A')
        
        if node_type == 'start':
            return f"🏠 PAGINA INIZIALE\nURL: {node}\nConnessioni: {degree}"
        
        elif node_type == 'dynamic':
            dynamic_label = node_data.get('dynamic_label', 'N/A')
            return f"🔄 CONTENUTO DINAMICO\nSezione: {dynamic_label}\nURL: {node}\nConnessioni: {degree}"
        
        elif node_type == 'file':
            file_type = node_data.get('file_type', 'unknown')
            return f"📄 FILE SCARICABILE\nTipo: {file_type}\nURL: {node}"
        
        elif node_type == 'broken':
            error_msg = node_data.get('error', 'Errore sconosciuto')
            return f"❌ LINK ROTTO\nURL: {node}\nStatus: {status_code}\nErrore: {error_msg}"
        
        else:
            title = node_data.get('title', 'N/A')
            return f"✓ URL: {node}\nStatus: {status_code}\nTitolo: {title}\nConnessioni: {degree}"


def create_force_directed_graph(json_file='./output/site_tree.json'):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tree = data['tree']
    G = nx.DiGraph()
    
    # Trova il nodo root
    start_url = None
    for url, info in tree.items():
        if info.get('depth', 999) == 0:
            start_url = url
            break
    
    if not start_url:
        raise ValueError("Nessun nodo root trovato (depth=0)")
    
    # Aggiungi nodi
    for url, info in tree.items():
        G.add_node(url,
                   depth=info.get('depth', 0),
                   display_name=info.get('display_name', 'unknown'),
                   title=info.get('title', ''),
                   is_start=url == start_url,
                   status=info.get('status', 'pending'),
                   status_code=info.get('status_code', 'N/A'),
                   error=info.get('error', ''),
                   file_type=info.get('file_type', None),
                   is_dynamic=info.get('is_dynamic', False),
                   dynamic_label=info.get('dynamic_label', 'N/A'))
    
    # Aggiungi archi
    for url, info in tree.items():
        if 'parents' in info and info['parents']:
            first_parent = info['parents'][0]
            if first_parent in tree:
                G.add_edge(first_parent, url)
    
    # Converti in Shortest Path Tree
    spt_edges = list(nx.bfs_edges(G, start_url))
    G_spt = nx.DiGraph()
    
    for node in G.nodes():
        G_spt.add_node(node, **G.nodes[node])
    
    for edge in spt_edges:
        G_spt.add_edge(edge[0], edge[1])
    
    return G_spt


def visualize_force_directed(G, output_file='./output/force_directed_graph.html'):
    net = Network(
        height='900px',
        width='100%',
        bgcolor='#ffffff',
        font_color='black',
        directed=True,
        notebook=False
    )
    
    # Configura le opzioni
    options = {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -100,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 1
            },
            "minVelocity": 2.00,
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": True,
                "onlyDynamicEdges": False,
                "iterations": 1000,
                "updateInterval": 100,
                "fit": True
            }
        },
        "layout": {
            "randomSeed": 42,
            "improvedLayout": True
        },
        "edges": {
            "smooth": {
                "type": "continuous",
                "forceDirection": "none"
            },
            "arrows": {
                "to": {
                    "enabled": True,
                    "scaleFactor": 0.5
                }
            }
        },
        "nodes": {
            "shape": "dot",
            "scaling": {
                "min": 10,
                "max": 30,
                "label": {
                    "enabled": True,
                    "min": 8,
                    "max": 20,
                    "drawThreshold": 12,
                    "maxVisible": 30
                }
            }
        },
        "font": {
            "size": 12,
            "strokeWidth": 2,
            "strokeColor": "#ffffff"
        },
        "interaction": {
            "navigationButtons": True,
            "keyboard": True,
            "hover": True,
            "zoomView": True,
            "hideEdgesOnZoom": True
        }
    }
    
    net.set_options(json.dumps(options))
    
    # Calcola centralità
    centrality = nx.degree_centrality(G)
    
    # Aggiungi nodi con stile
    for node in G.nodes():
        node_data = G.nodes[node]
        node_type = NodeStyler.get_node_type(node_data)
        style = NodeStyler.get_style(node_type)
        
        # Calcola dimensione
        base_size = 20 + (centrality[node] * 30)
        size = base_size + (20 if node_type == 'start' else 0)
        
        # Label e tooltip
        base_label = node_data.get('display_name', 'unknown')
        label = f"{style['emoji']} {base_label}"
        tooltip = NodeStyler.format_tooltip(node, node_data, node_type, G.degree(node))
        
        # Aggiungi nodo
        net.add_node(
            node,
            label=label,
            title=tooltip,
            size=size,
            color=style['color'],
            shape=style['shape'],
            borderWidth=style['border_width'],
            borderWidthSelected=5,
            hidden=False,
            physics=True,
            labelHighlightBold=True
        )
    
    # Aggiungi archi
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Salva
    try:
        net.save_graph(output_file)
        print(f"Visualizzazione salvata in: {output_file}")
    except Exception as e:
        print(f"Errore nel salvare il grafo: {e}")
        import traceback
        traceback.print_exc()


def main():
    try:
        G = create_force_directed_graph()
        
        # Statistiche
        print("\n  Statistiche del grafo:")
        print(f"   Nodi totali: {G.number_of_nodes()}")
        print(f"   Archi totali: {G.number_of_edges()}")
        
        # Conta nodi per status
        status_counts = {}
        for node in G.nodes():
            node_type = NodeStyler.get_node_type(G.nodes[node])
            status_counts[node_type] = status_counts.get(node_type, 0) + 1
        
        print(f"\nTipologia nodi:")
        print(f"   Pagina iniziale: {status_counts.get('start', 0)}")
        print(f"   Funzionanti: {status_counts.get('ok', 0)}")
        print(f"   Rotti: {status_counts.get('broken', 0)}")
        print(f"   File: {status_counts.get('file', 0)}")
        print(f"   Dinamici: {status_counts.get('dynamic', 0)}")
        print(f"   In attesa: {status_counts.get('pending', 0)}")
        
        # Nodo più centrale
        if G.number_of_nodes() > 0:
            centrality = nx.degree_centrality(G)
            central_node = max(centrality.items(), key=lambda x: x[1])
            print(f"\n⭐ Nodo più centrale: {urlparse(central_node[0]).path}")
        
        visualize_force_directed(G)
        
    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
