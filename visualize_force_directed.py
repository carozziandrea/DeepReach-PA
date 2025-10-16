import networkx as nx
from pyvis.network import Network
import json
from urllib.parse import urlparse

def create_force_directed_graph(json_file='site_tree.json'):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tree = data['tree']
    G = nx.DiGraph()
    
    start_url = None
    for url, info in tree.items():
        if info.get('depth', 999) == 0:
            start_url = url
            break
    
    if not start_url:
        raise ValueError("Nessun nodo root trovato (depth=0)")
    
    # Aggiungi nodi
    for url, info in tree.items():
        status = info.get('status', 'pending')
        status_code = info.get('status_code', 'N/A')
        
        G.add_node(url, 
                  depth=info.get('depth', 0),
                  display_name=info.get('display_name', 'unknown'),
                  title=info.get('title', ''),
                  is_start=url == start_url,
                  status=status,
                  status_code=status_code,
                  error=info.get('error', ''),
                  file_type=info.get('file_type', None),
                  is_dynamic=info.get('is_dynamic', False))
        
        if 'parents' in info and info['parents']:
            first_parent = info['parents'][0]  # Solo il primo
            if first_parent in tree:
                G.add_edge(first_parent, url)
    
    return G

def visualize_force_directed(G, output_file='force_directed_graph.html'):
    # Crea la rete Pyvis
    net = Network(
        height='900px',
        width='100%',
        bgcolor='#ffffff',
        font_color='black',
        directed=True,
        notebook=False
    )
    
    # Configura le opzioni per force-directed layout
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
                "fit": True              # Adatta la vista al grafo
            }
        },
        "layout": {
            "randomSeed": 42,  # Per risultati consistenti
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
                    "drawThreshold": 12,  # Soglia di zoom per mostrare le etichette
                    "maxVisible": 30      # Lunghezza massima etichetta visibile
                }
            },
            "font": {
                "size": 12,
                "strokeWidth": 2,        # Bordo del testo per migliore leggibilità
                "strokeColor": "#ffffff"  # Colore del bordo del testo
            }
        },
        "interaction": {
            "navigationButtons": True,
            "keyboard": True,
            "hover": True,
            "zoomView": True,            # Abilita zoom
            "hideEdgesOnZoom": True      # Nascondi archi quando zoomi out
        }
    }
    net.set_options(json.dumps(options))

    # Calcola la centralità dei nodi per dimensionarli
    centrality = nx.degree_centrality(G)
    
    # Mappa di colori per gli stati
    COLOR_MAP = {
        'ok': '#4A90E2',        # Blu - pagine OK
        'pending': '#F5A623',   # Arancione - pagine non ancora visitate
        'broken': '#D0021B',    # Rosso - link rotti
        'file': '#7ED321'       # Verde - file scaricabili
    }
    
    # Aggiungi nodi con colori differenti
    for node in G.nodes():
        node_data = G.nodes[node]
        size = 20 + (centrality[node] * 30)
        is_start = node_data.get('is_start', False)
        is_dynamic = node_data.get('is_dynamic', False)
        status = node_data.get('status', 'pending')
        status_code = node_data.get('status_code', 'N/A')
        
        # Determina colore e tooltip
        if is_start:
            color = COLOR_MAP['broken']
            title_text = f"🏠 PAGINA INIZIALE\nURL: {node}\nConnessioni: {G.degree(node)}"
            shape = 'star'
        elif is_dynamic:
            color = "#9D65C9"
            dynamic_label = node_data.get('dynamic_label', 'N/A')
            title_text = f"🔄 CONTENUTO DINAMICO\nSezione: {dynamic_label}\nURL: {node}\nConnessioni: {G.degree(node)}"
            shape = 'diamond'
        elif status == 'file':
            color = COLOR_MAP['file']
            file_type = node_data.get('file_type', 'unknown')
            title_text = f"📄 FILE SCARICABILE\nTipo: {file_type}\nURL: {node}"
            shape = 'dot'
        elif status == 'broken':
            color = COLOR_MAP['broken']
            error_msg = node_data.get('error', 'Errore sconosciuto')
            title_text = f"❌ LINK ROTTO\nURL: {node}\nStatus: {status_code}\nErrore: {error_msg}"
            shape = 'triangle'
        else:
            color = COLOR_MAP.get(status, COLOR_MAP['ok'])
            title_text = f"✓ URL: {node}\nStatus: {status_code}\nTitolo: {node_data.get('title', 'N/A')}\nConnessioni: {G.degree(node)}"
            shape = 'dot'
        
        # Label
        label = node_data.get('display_name', 'unknown')
        if is_dynamic:
            label = f"🔄 {label}"
        elif status == 'file':
            label = f"📄 {label}"
        elif status == 'broken':
            label = f"❌ {label}"
        elif is_start:
            label = f"🏠 {label}"
        elif status == 'pending':
            label = f"⏳ {label}"
        
        net.add_node(
            node,
            label=label,
            title=title_text,
            size=size + (20 if is_start else 0),
            color=color,
            borderWidth=3 if (is_start or status == 'broken') else 1,
            borderWidthSelected=5,
            hidden=False,
            physics=True,
            labelHighlightBold=True,
            shape=shape
        )
    
    # Aggiungi archi
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Salva il grafo
    try:
        net.save_graph(output_file)
        print(f"✓ Visualizzazione salvata in: {output_file}")
    except Exception as e:
        print(f"❌ Errore nel salvare il grafo: {e}")
        import traceback
        traceback.print_exc()

def main():
    try:
        # Crea il grafo
        G = create_force_directed_graph()
        
        # Statistiche
        print("\n📊 Statistiche del grafo:")
        print(f"   Nodi totali: {G.number_of_nodes()}")
        print(f"   Archi totali: {G.number_of_edges()}")
        
        # Conta nodi per status
        status_counts = {}
        for node in G.nodes():
            status = G.nodes[node].get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n🔗 Stati dei link:")
        print(f"   ✓ Funzionanti: {status_counts.get('ok', 0)}")
        print(f"   ❌ Rotti: {status_counts.get('broken', 0)}")
        print(f"   ⏳ In attesa: {status_counts.get('pending', 0)}")
        
        # Nodo più centrale
        if G.number_of_nodes() > 0:
            centrality = nx.degree_centrality(G)
            central_node = max(centrality.items(), key=lambda x: x[1])
            print(f"\n⭐ Nodo più centrale: {urlparse(central_node[0]).path}")
        
        # Visualizza il grafo
        visualize_force_directed(G)
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()