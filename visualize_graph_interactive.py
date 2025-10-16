import networkx as nx
from pyvis.network import Network
import json
from urllib.parse import urlparse

def create_graph_from_json(json_file='site_tree.json'):
    # Carica i dati
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tree = data['tree']
    # Crea il grafo direzionato
    G = nx.DiGraph()
    
    # Aggiungi nodi con display_name
    for url, info in tree.items():
        G.add_node(url, 
                  depth=info['depth'],
                  display_name=info['display_name'],
                  title=info.get('title', ''))
        
        # Aggiungi archi per ogni parent
        for parent in info['parents']:
            G.add_edge(parent, url)
    
    return G

def visualize_interactive_graph(G, output_file='interactive_site_tree.html'):
    # Crea la rete Pyvis
    net = Network(
        height='900px',
        width='100%',
        bgcolor='#ffffff',
        font_color='black',
        directed=True,
        layout=True,
        notebook=False
    )
    
    options = {
        "physics": {
            "hierarchicalRepulsion": {
                "centralGravity": 0.0,
                "springLength": 100,
                "springConstant": 0.01,
                "nodeDistance": 120,
            },
            "minVelocity": 0.0,  # Ridotto a 0 per fermare il movimento
            "solver": "hierarchicalRepulsion",
            "stabilization": {
                "enabled": True,
                "iterations": 1000,  # Aumenta le iterazioni per una migliore stabilizzazione
                "updateInterval": 100,
                "fit": True
            },
            "enabled": False  # Disabilita la fisica dopo la stabilizzazione iniziale
        },
        "layout": {
            "hierarchical": {
                "enabled": True,
                "direction": "UD",  # Cambiato da "LR" a "UD" (Up-Down)
                "sortMethod": "directed",
                "nodeSpacing": 150,
                "levelSeparation": 200,
                "treeSpacing": 200  # Aggiunto per migliorare la spaziatura orizzontale
            }
        },
        "edges": {
            "smooth": {
                "type": "cubicBezier",
                "forceDirection": "vertical"  # Cambiato da "horizontal" a "vertical"
            },
            "color": {
                "inherit": False,
                "color": "#2B7CE9"
            }
        }
    }
    net.set_options(json.dumps(options))

    # Aggiungi nodi e archi dal grafo NetworkX
    for node in G.nodes():
        net.add_node(
            node,
            label=G.nodes[node]['display_name'],  # Usa display_name invece del path completo
            title=f"URL: {node}\nProfondità: {G.nodes[node]['depth']}",
            color="#97C2FC"
        )
    
    # Aggiungi tutti gli archi
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Salva il grafo
    try:
        net.save_graph(output_file)
        print(f"Visualizzazione interattiva salvata in: {output_file}")
    except Exception as e:
        print(f"Errore nel salvare il grafo: {e}")

def main():
    # Crea il grafo da JSON
    G = create_graph_from_json()
    
    # Stampa alcune statistiche
    print(f"Numero di nodi: {G.number_of_nodes()}")
    print(f"Numero di archi: {G.number_of_edges()}")
    print(f"Profondità massima: {max(nx.get_node_attributes(G, 'depth').values())}")
    
    # Visualizza il grafo
    visualize_interactive_graph(G)

if __name__ == '__main__':
    main()