<div align="center">
  <a href="#english-version"><strong>English Version</strong></a> &nbsp;&nbsp;|&nbsp;&nbsp; <a href="#versione-italiana"><strong>Versione Italiana</strong></a>
</div>

---

<h1 id="versione-italiana">Versione Italiana</h1>

# Costruzione Automatica di Sovrastrutture Logiche per la Trasparenza nei Siti della Pubblica Amministrazione

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
```text
DeepReach-PA
├── orchestrator/                   # Modulo principale di orchestrazione
│   ├── main.py                     # Entry point e gestione argomenti CLI
│   ├── config.py                   # Configurazione centralizzata
│   ├── homepage_checker.py         # Rilevamento sezione AT nella homepage
│   ├── crawler_runner.py           # Esecuzione dei crawl Scrapy
│   ├── analyzer.py                 # Analisi dei dati raccolti
│   ├── content_scanner.py          # Scansione contenuti e privacy
│   ├── privacy_analyzer.py         # Analisi rischi privacy (PDF, HTML)
│   ├── metrics.py                  # Calcolo metriche e indici
│   ├── models.py                   # Modelli dati (dataclass)
│   ├── visualizer.py               # Generazione grafi interattivi
│   ├── batch_runner.py             # Esecuzione batch su più siti
│   ├── batch_index_generator.py    # Generazione pagina index.html batch
│   ├── utils.py                    # Funzioni di utilità comuni
│   ├── __init__.py                 # Esportazioni del modulo
│   ├── lib/                        # Librerie JS embedded (vis.js, tom-select)
│   └── reporters/                  # Generazione report
│       ├── report_generator.py     # Report PDF/TXT di analisi
│       ├── privacy_reporter.py     # Report PDF/TXT privacy
│       ├── comparative_reporter.py # Report comparativo batch
│       ├── console_reporter.py     # Output su console
│       ├── json_reporter.py        # Export JSON
│       ├── chart_utils.py          # Generazione grafici per PDF
│       └── base_reporter.py        # Classe base reporter
│
├── pa_crawler/                     # Spider Scrapy per il crawling
│   ├── spiders/                    # Implementazione spider
│   ├── middlewares.py              # Gestione richieste e Playwright
│   └── settings.py                 # Configurazione Scrapy
│
└── scripts/                        # Modulo visualizzazione grafi
    ├── graph_visualizer.py         # Rendering grafo interattivo (PyVis)
    ├── graph_builder.py            # Costruzione grafo da dati crawl
    ├── graph_stats.py              # Statistiche sul grafo
    ├── node_styler.py              # Stile e colori dei nodi
    └── config.py                   # Configurazione visualizzazione
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

## Installazione

### Prerequisiti

* Python 3.13 o superiore
* [uv](https://docs.astral.sh/uv/) (gestore pacchetti Python)

### Procedura

1. Clonare il repository:
   ```bash
   git clone https://github.com/carozziandrea/DeepReach-PA.git
   cd tesi-triennale-trasparenza-nella-pa
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
| `--limit-pdf <N>` | Limita il numero di PDF da scansionare per sito (0 = nessun limite) |
| `--crawler-dir <DIR>` | Specifica la directory del crawler Scrapy |

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
| `index.html` | Pagina riassuntiva con panoramica di tutti i siti analizzati (solo modalità batch) |

## Struttura dei Report

### Report di Analisi

Il report principale contiene:

* **Metadata**: URL analizzati, timestamp, stato rilevamento AT
* **Statistiche Crawl**: Pagine trovate, durata, errori
* **Metriche di Raggiungibilità**: Profondità media/massima, distribuzione pagine per livello
* **Metriche di Qualità**: Link rotti, pagine orfane, file rilevati
* **Analisi Trasparenza**: Sezioni obbligatorie trovate, trasparenza sommersa, sezioni mancanti
* **Indice di Usabilità**: Punteggio finale (0-100) con breakdown delle penalità

### Report Privacy

Il report privacy include:

* **Distribuzione Rischi**: Conteggio nodi per livello di rischio (HIGH, MEDIUM, LOW)
* **Tipologie Dati**: Email, telefoni, indirizzi, codici fiscali rilevati
* **Dettaglio per URL**: Lista completa degli URL con dati sensibili
* **Suggerimenti**: Raccomandazioni per la remediation

---

<h1 id="english-version">English Version</h1>

# Automatic Construction of Logical Superstructures for Transparency in Public Administration Websites

## Project Objective

The project aims to develop software capable of analyzing Italian Public Administration (PA) websites.

The analysis focuses on the "Amministrazione Trasparente" (Transparent Administration) section to verify its compliance with standards, regulatory obligations, and current directives regarding administrative transparency.

The software implements the following features:

1. Automatic exploration of the internal structure of public websites starting from an initial URL
2. Generation of an interactive site map (site graph)
3. Classification of pages based on the presence of content relevant to transparency or potentially critical for privacy
4. Measurement of the reachability of mandatory content (depth, paths, broken links)
5. Calculation of a usability index and detection of "submerged transparency"

## System Architecture

```text
DeepReach-PA
├── orchestrator/                   # Main orchestration module
│   ├── main.py                     # Entry point and CLI arguments management
│   ├── config.py                   # Centralized configuration
│   ├── homepage_checker.py         # Detection of AT section on the homepage
│   ├── crawler_runner.py           # Execution of Scrapy crawls
│   ├── analyzer.py                 # Collected data analysis
│   ├── content_scanner.py          # Content and privacy scanning
│   ├── privacy_analyzer.py         # Privacy risks analysis (PDF, HTML)
│   ├── metrics.py                  # Metrics and indices calculation
│   ├── models.py                   # Data models (dataclasses)
│   ├── visualizer.py               # Interactive graphs generation
│   ├── batch_runner.py             # Batch execution on multiple sites
│   ├── batch_index_generator.py    # Generation of batch index.html page
│   ├── utils.py                    # Common utility functions
│   ├── __init__.py                 # Module exports
│   ├── lib/                        # Embedded JS libraries (vis.js, tom-select)
│   └── reporters/                  # Report generation
│       ├── report_generator.py     # Analysis PDF/TXT report
│       ├── privacy_reporter.py     # Privacy PDF/TXT report
│       ├── comparative_reporter.py # Comparative batch report
│       ├── console_reporter.py     # Console output
│       ├── json_reporter.py        # JSON export
│       ├── chart_utils.py          # PDF charts generation
│       └── base_reporter.py        # Base reporter class
│
├── pa_crawler/                     # Scrapy spiders for crawling
│   ├── spiders/                    # Spider implementation
│   ├── middlewares.py              # Requests and Playwright management
│   └── settings.py                 # Scrapy configuration
│
└── scripts/                        # Graph visualization module
    ├── graph_visualizer.py         # Interactive graph rendering (PyVis)
    ├── graph_builder.py            # Graph construction from crawl data
    ├── graph_stats.py              # Graph statistics
    ├── node_styler.py              # Node styling and colors
    └── config.py                   # Visualization configuration
```

### Execution Flow

1. **Homepage Checker**: Automatically identifies the link to the "Amministrazione Trasparente" section
2. **Crawler Runner**: Executes two parallel crawls (shallow on the homepage, deep on the AT section)
3. **Analyzer**: Processes the collected data by calculating reachability, quality, and transparency metrics
4. **Privacy Analyzer**: Analyzes HTML pages and PDF documents to detect personal data
5. **Metrics**: Calculates the final usability index with penalties and bonuses
6. **Reporters**: Generates reports in PDF, TXT, and JSON formats
7. **Visualizer**: Produces interactive graphs

## Technologies Used

### Language and Runtime

| Technology | Version | Usage |
|------------|----------|----------|
| Python | >= 3.13 | Primary programming language |

### Main Frameworks and Libraries

| Library | Usage |
|----------|----------|
| **Scrapy** | Framework for web scraping and HTTP request management |
| **Playwright** | Rendering of JavaScript-based pages via headless browser |
| **scrapy-playwright** | Integration between Scrapy and Playwright |
| **BeautifulSoup4** | Parsing and analysis of HTML code |
| **NetworkX** | Creation and manipulation of graphs to model site structure |
| **PyVis** | Interactive visualization of generated graphs |
| **Matplotlib** | Generation of static charts and visualizations |
| **ReportLab** | Report generation in PDF format |
| **pdfplumber** | Text extraction from PDF documents for privacy analysis |
| **Requests** | HTTP request management for document downloads |

## Installation

### Prerequisites

* Python 3.13 or higher
* [uv](https://docs.astral.sh/uv/) (Python package manager)

### Procedure

1. Clone the repository:
   ```bash
   git clone https://github.com/carozziandrea/DeepReach-PA.git
   cd tesi-triennale-trasparenza-nella-pa
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Install browsers for Playwright:
   ```bash
   uv run playwright install
   ```

## Usage Instructions

### Single Site Analysis

Run a complete analysis on a PA website:

```bash
cd orchestrator
uv run python main.py <HOMEPAGE_URL>
```

Example:
```bash
uv run python main.py https://www.interno.gov.it
```

### Available Options

| Option | Description |
|---------|-------------|
| `--shallow-only` | Executes only the homepage crawl (faster) |
| `--deep-only` | Executes only the AT section crawl (requires `--at-url`) |
| `--at-url <URL>` | Manually specifies the AT section URL |
| `--skip-crawl` | Skips crawls and analyzes existing JSONs |
| `--output-dir <DIR>` | Directory for output files (default: `./output`) |
| `--thorough` | In-depth analysis with greater crawl depth |
| `--limit-pdf <N>` | Limits the number of PDFs to scan per site (0 = no limit) |
| `--crawler-dir <DIR>` | Specifies the Scrapy crawler directory |

### Batch Mode

To analyze multiple sites sequentially:

```bash
uv run python main.py --batch --sites-file ./input/lista_siti.txt
```

The input file must contain one URL per line. Lines starting with `#` are ignored.

Additional options for batch mode:

| Option | Description |
|---------|-------------|
| `--stop-on-error` | Stops execution on the first error |
| `--resume` | Resumes execution by skipping already analyzed sites |

## Generated Outputs

Upon completion of the analysis, the following files are generated in the output directory:

| File | Description |
|------|-------------|
| `analysis_report.pdf` | Comprehensive analysis report with metrics and charts |
| `analysis_report.txt` | Textual version of the report |
| `analysis_report.json` | Structured data in JSON format |
| `privacy_report.pdf` | Detailed report on privacy risks |
| `privacy_report.txt` | Textual version of the privacy report |
| `graph_image.png` | Static visualization of the site graph |
| `*_graph.html` | Interactive graph visualization (PyVis) |
| `index.html` | Summary page with an overview of all analyzed sites (batch mode only) |

## Report Structure

### Analysis Report

The main report contains:

* **Metadata**: Analyzed URLs, timestamps, AT detection status
* **Crawl Statistics**: Pages found, duration, errors
* **Reachability Metrics**: Average/maximum depth, page distribution per level
* **Quality Metrics**: Broken links, orphan pages, detected files
* **Transparency Analysis**: Mandatory sections found, submerged transparency, missing sections
* **Usability Index**: Final score (0-100) with penalty breakdown

### Privacy Report

The privacy report includes:

* **Risk Distribution**: Node count by risk level (HIGH, MEDIUM, LOW)
* **Data Types**: Detected emails, phone numbers, addresses, fiscal codes
* **Detail by URL**: Complete list of URLs containing sensitive data
* **Suggestions**: Recommendations for remediation

<br><br>
