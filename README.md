# Costruzione Automatica di Sovrastrutture Logiche per la Trasparenza nei Siti della Pubblica Amministrazione

**Autore:** Andrea Carozzi (Matricola: 896142)

Progetto di tirocinio interno legato alla tesi di Laurea in Informatica presso l'Università degli Studi di Milano.


## Obiettivo del Progetto

Il progetto mira a sviluppare un software in grado di analizzare i siti web della Pubblica Amministrazione italiana (PA).

L'analisi si concentra sulla sezione "Amministrazione Trasparente" per verificarne la conformità agli standard, agli obblighi normativi e alle direttive vigenti in materia di trasparenza amministrativa.

Il software implementa le seguenti funzionalità:

1. Esplorazione automatica della struttura interna dei siti pubblici a partire da un URL iniziale
2. Generazione di una mappa interattiva delle pagine (site graph)
3. Classificazione delle pagine in base alla presenza di contenuti rilevanti per la trasparenza o potenzialmente critici per la privacy
4. Misurazione della raggiungibilità dei contenuti obbligatori (profondità, percorsi, link rotti)
5. Calcolo di un indice di usabilità e rilevamento della "trasparenza sommersa"


## Architettura del Sistema
```
DeepReach-PA
├── orchestrator/               # Modulo principale di orchestrazione
│   ├── main.py                 # Entry point e gestione argomenti CLI
│   ├── config.py               # Configurazione centralizzata
│   ├── homepage_checker.py     # Rilevamento sezione AT nella homepage
│   ├── crawler_runner.py       # Esecuzione dei crawl Scrapy
│   ├── analyzer.py             # Analisi dei dati raccolti
│   ├── content_scanner.py      # Scansione contenuti e privacy
│   ├── privacy_analyzer.py     # Analisi rischi privacy (PDF, HTML)
│   ├── metrics.py              # Calcolo metriche e indici
│   ├── models.py               # Modelli dati (dataclass)
│   ├── visualizer.py           # Generazione grafi interattivi
│   ├── batch_runner.py         # Esecuzione batch su più siti
│   └── reporters/              # Generazione report (PDF, TXT, JSON)
│
├── pa_crawler/                 # Spider Scrapy per il crawling
│   ├── spiders/                # Implementazione spider
│   ├── middlewares.py          # Gestione richieste e Playwright
│   └── settings.py             # Configurazione Scrapy
│
└── scripts/                    # Utility e visualizzazione grafi
```

### Flusso di Esecuzione

1. **Homepage Checker**: Identifica automaticamente il link alla sezione "Amministrazione Trasparente"
2. **Crawler Runner**: Esegue due crawl paralleli (shallow sulla homepage, deep sulla sezione AT)
3. **Analyzer**: Elabora i dati raccolti calcolando metriche di raggiungibilità, qualità e trasparenza
4. **Privacy Analyzer**: Analizza pagine HTML e documenti PDF per rilevare dati personali
5. **Metrics**: Calcola l'indice di usabilità finale con penalità e bonus
6. **Reporters**: Genera i report in formato PDF, TXT e JSON
7. **Visualizer**: Produce grafi interattivi

## Tecnologie Utilizzate

### Linguaggio e Runtime

| Tecnologia | Versione | Utilizzo |
|------------|----------|----------|
| Python | >= 3.13 | Linguaggio di programmazione principale |

### Framework e Librerie Principali

| Libreria | Utilizzo |
|----------|----------|
| **Scrapy** | Framework per web scraping e gestione delle richieste HTTP |
| **Playwright** | Rendering di pagine JavaScript-based tramite browser headless |
| **scrapy-playwright** | Integrazione tra Scrapy e Playwright |
| **BeautifulSoup4** | Parsing e analisi del codice HTML |
| **NetworkX** | Creazione e manipolazione di grafi per modellare la struttura del sito |
| **PyVis** | Visualizzazione interattiva dei grafi generati |
| **Matplotlib** | Generazione di grafici e visualizzazioni statiche |
| **ReportLab** | Generazione di report in formato PDF |
| **pdfplumber** | Estrazione di testo da documenti PDF per analisi privacy |
| **Requests** | Gestione richieste HTTP per download documenti |
| **NumPy / SciPy** | Calcoli numerici e analisi statistica |
| **python-louvain** | Algoritmi di community detection per analisi grafi |


## Installazione

### Prerequisiti

- Python 3.13 o superiore
- [uv](https://docs.astral.sh/uv/) (gestore pacchetti Python) - consigliato
- Connessione Internet

### Procedura

1. Clonare il repository:
   ```bash
   git clone <repository-url>
   cd Tesi
   ```

2. Installare le dipendenze con `uv`:
   ```bash
   uv sync
   ```

3. Installare i browser per Playwright:
   ```bash
   uv run playwright install
   ```


## Istruzioni d'Uso

### Analisi Singolo Sito

Eseguire l'analisi completa su un sito della PA:

```bash
cd orchestrator
uv run python main.py <URL_HOMEPAGE>
```

Esempio:
```bash
uv run python main.py https://www.interno.gov.it
```

### Opzioni Disponibili

| Opzione | Descrizione |
|---------|-------------|
| `--shallow-only` | Esegue solo il crawl della homepage (più veloce) |
| `--deep-only` | Esegue solo il crawl della sezione AT (richiede `--at-url`) |
| `--at-url <URL>` | Specifica manualmente l'URL della sezione AT |
| `--skip-crawl` | Salta i crawl e analizza i JSON esistenti |
| `--output-dir <DIR>` | Directory per i file di output (default: `./output`) |
| `--thorough` | Analisi approfondita con maggiore profondità di crawl |

### Modalità Batch

Per analizzare più siti in sequenza:

```bash
uv run python main.py --batch --sites-file ./input/lista_siti.txt
```

Il file di input deve contenere un URL per riga. Le righe che iniziano con `#` sono ignorate.

Opzioni aggiuntive per la modalità batch:

| Opzione | Descrizione |
|---------|-------------|
| `--stop-on-error` | Interrompe l'esecuzione al primo errore |
| `--resume` | Riprende l'esecuzione saltando i siti già analizzati |


## Output Generati

Al termine dell'analisi, vengono generati i seguenti file nella directory di output:

| File | Descrizione |
|------|-------------|
| `analysis_report.pdf` | Report completo dell'analisi con metriche e grafici |
| `analysis_report.txt` | Versione testuale del report |
| `analysis_report.json` | Dati strutturati in formato JSON |
| `privacy_report.pdf` | Report dettagliato sui rischi privacy |
| `privacy_report.txt` | Versione testuale del report privacy |
| `graph_image.png` | Visualizzazione statica del grafo del sito |
| `*_graph.html` | Visualizzazione interattiva del grafo (PyVis) |


## Struttura dei Report

### Report di Analisi

Il report principale contiene:

- **Metadata**: URL analizzati, timestamp, stato rilevamento AT
- **Statistiche Crawl**: Pagine trovate, durata, errori
- **Metriche di Raggiungibilità**: Profondità media/massima, distribuzione pagine per livello
- **Metriche di Qualità**: Link rotti, pagine orfane, file rilevati
- **Analisi Trasparenza**: Sezioni obbligatorie trovate, trasparenza sommersa, sezioni mancanti
- **Indice di Usabilità**: Punteggio finale (0-100) con breakdown delle penalità

### Report Privacy

Il report privacy include:

- **Distribuzione Rischi**: Conteggio nodi per livello di rischio (HIGH, MEDIUM, LOW)
- **Tipologie Dati**: Email, telefoni, indirizzi, codici fiscali rilevati
- **Dettaglio per URL**: Lista completa degli URL con dati sensibili
- **Suggerimenti**: Raccomandazioni per la remediation


## Stato del Progetto

* In corso.