import json
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import numpy as np

def load_graph_data(filename='graph_data.json'):
    """Carica i dati del grafo dal file JSON"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['edges'], data['nodes']

def create_graph(edges):
    """Crea un grafo NetworkX dagli edges"""
    G = nx.DiGraph()
    G.add_edges_from(edges)
    return G

def visualize_basic(G, output_file='site_graph_basic.png'):
    """Visualizzazione base del grafo"""
    fig, ax = plt.subplots(figsize=(20, 20))
    
    pos = nx.spring_layout(G, k=0.3*1/np.sqrt(len(G.nodes())), iterations=50)
    
    nx.draw(G, pos,
            with_labels=False,
            node_size=50,
            node_color='lightblue',
            edge_color='gray',
            arrows=True,
            arrowsize=10,
            alpha=0.7,
            width=0.5,
            ax=ax)
    
    ax.set_title(f"Struttura del sito - {G.number_of_nodes()} pagine, {G.number_of_edges()} collegamenti")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Grafo base salvato in: {output_file}")
    plt.close()

def visualize_with_metrics(G, output_file='site_graph_metrics.png'):
    """Visualizzazione avanzata con metriche"""
    fig, ax = plt.subplots(figsize=(25, 25))
    
    pagerank = nx.pagerank(G)
    in_degree = dict(G.in_degree())
    
    node_sizes = [pagerank[node] * 10000 for node in G.nodes()]
    node_colors = [in_degree[node] for node in G.nodes()]
    
    pos = nx.spring_layout(G, k=0.5*1/np.sqrt(len(G.nodes())), iterations=50)
    
    nodes = nx.draw_networkx_nodes(G, pos,
                                     node_size=node_sizes,
                                     node_color=node_colors,
                                     cmap=plt.cm.Blues,
                                     alpha=0.7,
                                     ax=ax)
    
    nx.draw_networkx_edges(G, pos,
                           edge_color='gray',
                           arrows=True,
                           arrowsize=10,
                           alpha=0.3,
                           width=0.5,
                           ax=ax)
    
    top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
    labels = {node: urlparse(node).path or '/' for node, _ in top_nodes}
    
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color='red', ax=ax)
    
    # Colorbar con riferimento esplicito agli assi
    if nodes is not None:
        plt.colorbar(nodes, ax=ax, label='Link in entrata')
    
    ax.set_title(f"Struttura del sito con metriche\nDimensione nodi: PageRank | Colore: Link in entrata")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Grafo con metriche salvato in: {output_file}")
    plt.close()

def print_statistics(G):
    """Stampa statistiche del grafo"""
    print("\n=== STATISTICHE DEL GRAFO ===")
    print(f"Numero di pagine (nodi): {G.number_of_nodes()}")
    print(f"Numero di collegamenti (archi): {G.number_of_edges()}")
    
    if G.number_of_nodes() > 0:
        pagerank = nx.pagerank(G)
        top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n=== TOP 5 PAGINE PER PAGERANK ===")
        for url, score in top_pagerank:
            print(f"{score:.4f} - {url}")
        
        in_degree = dict(G.in_degree())
        top_in_degree = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n=== TOP 5 PAGINE PER LINK IN ENTRATA ===")
        for url, count in top_in_degree:
            print(f"{count} link - {url}")
        
        out_degree = dict(G.out_degree())
        top_out_degree = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print("\n=== TOP 5 PAGINE PER LINK IN USCITA ===")
        for url, count in top_out_degree:
            print(f"{count} link - {url}")

def main():
    print("Caricamento dati del grafo...")
    edges, nodes = load_graph_data()
    
    print(f"Caricati {len(nodes)} nodi e {len(edges)} archi")
    
    print("Creazione del grafo NetworkX...")
    G = create_graph(edges)
    
    print_statistics(G)
    
    print("\nGenerazione visualizzazioni...")
    visualize_basic(G)
    visualize_with_metrics(G)
    
    print("\nCompletato!")

if __name__ == "__main__":
    main()
