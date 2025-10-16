import networkx as nx
from pyvis.network import Network
import json
from urllib.parse import urlparse

def create_force_directed_graph(json_file='site_tree.json'):
    # Carica i dati
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tree = data['tree']
    G = nx.DiGraph()
    
    # Identifica l'URL di partenza (quello con depth=0)
    start_url = next(url for url, info in tree.items() if info['depth'] == 0)
    
    # Aggiungi nodi con display_name e flag per il nodo iniziale
    for url, info in tree.items():
        G.add_node(url, 
                  depth=info['depth'],
                  display_name=info['display_name'],
                  title=info.get('title', ''),
                  is_start=url == start_url)
        
        # Aggiungi archi per ogni parent nella lista parents
        if 'parents' in info:
            for parent in info['parents']:
                G.add_edge(parent, url)  # Crea un arco da ogni parent al nodo
    
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
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": True,
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
    
    # Aggiungi nodi con colori differenti
    for node in G.nodes():
        size = 20 + (centrality[node] * 30)
        is_start = G.nodes[node]['is_start']
        
        net.add_node(
            node,
            label=G.nodes[node]['display_name'],
            title=f"URL: {node}\nConnessioni: {G.degree(node)}",
            size=size + (20 if is_start else 0),  # Nodo iniziale più grande
            color="#FF4444" if is_start else "#97C2FC",  # Rosso per il nodo iniziale
            borderWidth=3 if is_start else 1,  # Bordo più spesso per il nodo iniziale
            hidden=False,
            physics=True,
            labelHighlightBold=True     # Etichetta in grassetto al passaggio del mouse
        )
    
    # Aggiungi gli archi
    for edge in G.edges():
        net.add_edge(edge[0], edge[1])
    
    # Salva il grafo
    try:
        net.save_graph(output_file)
        print(f"Visualizzazione force-directed salvata in: {output_file}")
    except Exception as e:
        print(f"Errore nel salvare il grafo: {e}")

def main():
    # Crea il grafo
    G = create_force_directed_graph()
    
    # Stampa statistiche
    print("\nStatistiche del grafo:")
    print(f"Numero di nodi: {G.number_of_nodes()}")
    print(f"Numero di archi: {G.number_of_edges()}")
    
    # Trova il nodo più centrale
    centrality = nx.degree_centrality(G)
    central_node = max(centrality.items(), key=lambda x: x[1])
    print(f"\nNodo più centrale: {urlparse(central_node[0]).path}")
    
    # Visualizza il grafo
    visualize_force_directed(G)

if __name__ == '__main__':
    main()