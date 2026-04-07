import scrapy
import json
import threading
from urllib.parse import urlparse, urljoin
from pathlib import Path

# Import PageMethod per Playwright
try:
    from scrapy_playwright.page import PageMethod
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: scrapy-playwright non installato, usa: pip install scrapy-playwright")

class SiteMapSpider(scrapy.Spider):
    name = 'sitemap_spider'

    # JavaScript per espandere dropdown e contenuti dinamici
    EXPAND_DROPDOWNS_JS = """
    async () => {
        // Funzione helper per attendere
        const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

        // 1. Espandi dropdown Bootstrap/comuni
        const dropdownToggles = document.querySelectorAll(
            '.dropdown-toggle, [data-toggle="dropdown"], [data-bs-toggle="dropdown"], ' +
            '.nav-link.dropdown, .has-submenu > a, .menu-item-has-children > a'
        );
        for (const toggle of dropdownToggles) {
            try {
                toggle.click();
                await sleep(100);
            } catch (e) {}
        }

        // 2. Espandi accordion/collapse
        const accordionToggles = document.querySelectorAll(
            '[data-toggle="collapse"], [data-bs-toggle="collapse"], ' +
            '.accordion-button, .collapse-toggle, .panel-heading a, ' +
            '[aria-expanded="false"]'
        );
        for (const toggle of accordionToggles) {
            try {
                if (toggle.getAttribute('aria-expanded') === 'false') {
                    toggle.click();
                    await sleep(150);
                }
            } catch (e) {}
        }

        // 3. Hover su menu per triggerare sottomenu (siti PA italiani)
        const menuItems = document.querySelectorAll(
            'nav li, .navbar li, .main-menu li, #menu li, ' +
            '.navigation li, .primary-menu li'
        );
        for (const item of menuItems) {
            try {
                item.dispatchEvent(new MouseEvent('mouseenter', {bubbles: true}));
                await sleep(50);
            } catch (e) {}
        }

        // 4. Click su "Mostra tutti", "Vedi altro", etc.
        const showMoreButtons = document.querySelectorAll(
            'a[href*="mostra"], a[href*="tutti"], ' +
            '.show-more, .view-all, .load-more, [class*="expand"]'
        );
        for (const btn of showMoreButtons) {
            try {
                btn.click();
                await sleep(100);
            } catch (e) {}
        }

        // Click su bottoni con testo specifico
        const allButtons = document.querySelectorAll('button, a.btn');
        for (const btn of allButtons) {
            const text = btn.textContent.toLowerCase();
            if (text.includes('mostra') || text.includes('espandi') || text.includes('vedi tutto')) {
                try {
                    btn.click();
                    await sleep(100);
                } catch (e) {}
            }
        }

        // 5. Scroll per triggerare lazy loading
        window.scrollTo(0, document.body.scrollHeight / 2);
        await sleep(200);
        window.scrollTo(0, document.body.scrollHeight);
        await sleep(300);
        window.scrollTo(0, 0);

        // Attendi che il DOM si stabilizzi
        await sleep(500);
    }
    """

    @staticmethod
    def normalize_url(url):
        """Normalizza URL rimuovendo query string e fragment."""
        if not url:
            return url
        # Rimuovi fragment e query string
        url = url.split('#')[0].split('?')[0]
        # Rimuovi trailing slash (eccetto per root)
        if url.endswith('/') and url.count('/') > 3:
            url = url.rstrip('/')
        return url

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 60000,
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
        # Contesti persistenti - riutilizza il browser invece di riaprirlo
        'PLAYWRIGHT_CONTEXTS': {
            'default': {
                'ignore_https_errors': True,
            }
        },
        # Blocca risorse inutili per velocizzare il crawling
        'PLAYWRIGHT_ABORT_REQUEST': lambda req: req.resource_type in [
            'image', 'media', 'font', 'stylesheet'
        ],
        'ROBOTSTXT_OBEY': False,
        'DEPTH_LIMIT': 5,
        'CONCURRENT_REQUESTS': 8,  # Aumentato per parallelizzare
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,  # Max 4 per dominio
        'DOWNLOAD_DELAY': 0.5,  # Ridotto delay
        'HTTPCACHE_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'DOWNLOAD_TIMEOUT': 60,
        'RETRY_TIMES': 3,
        'LOG_LEVEL': 'INFO',
    }
    
    # Path al file lista_siti.txt (relativo alla root del progetto)
    LISTA_SITI_PATH = Path(__file__).parent.parent.parent / 'input' / 'lista_siti.txt'

    def __init__(self, start_url=None, mode='deep', max_depth=None, output_name=None, output_dir=None, *args, **kwargs):
        """
        Inizializza il crawler.

        Args:
            start_url: URL di partenza (se non fornito, legge da input/lista_siti.txt)
            mode: 'deep' (per AT, esclude nav) o 'shallow' (per homepage, include nav)
            max_depth: Profondità massima (default: 5 per deep, 2 per shallow)
            output_name: Nome file output senza .json (default: site_tree o site_tree_main)
            output_dir: Directory di output (default: output/ nella root del progetto)
        """
        super().__init__(*args, **kwargs)

        if start_url:
            self.start_urls = [start_url]
        else:
            # Leggi URL da lista_siti.txt
            self.start_urls = self._load_urls_from_file()
        start_netloc = urlparse(self.start_urls[0]).netloc
        self.allowed_domain = start_netloc
        # Calcola il dominio radice (es. "comune.torino.it" da "trasparenza.comune.torino.it")
        # per permettere il crawling di sottodomini dello stesso ente
        parts = start_netloc.split('.')
        self.allowed_root_domain = '.'.join(parts[-3:]) if len(parts) >= 3 else start_netloc
        self.visited_urls = set()
        self.site_tree = {}

        # Lock per thread-safety
        self._lock = threading.Lock()
        
        # ========== CONFIGURAZIONE MODE ==========
        self.mode = mode
        
        # Profondità: valore passato oppure default basato su mode
        if max_depth is not None:
            self.max_depth = int(max_depth)
        else:
            self.max_depth = 5 if mode == 'deep' else 2
        
        # Nome output: valore passato oppure default basato su mode
        if output_name:
            self.output_name = output_name
        else:
            self.output_name = 'site_tree' if mode == 'deep' else 'site_tree_main'

        # Directory output: valore passato oppure default (output/ nella root)
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = None  # Usa default in _get_output_path

        # ========== HOMEPAGE ==========
        parsed = urlparse(self.start_urls[0])
        self.homepage_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # In mode shallow non blocchiamo la homepage (è il punto di partenza)
        self.block_homepage = (mode == 'deep')
        
        self.logger.info(f'🎯 Start URL: {self.start_urls[0]}')
        self.logger.info(f'⚙️  Mode: {self.mode} | Depth: {self.max_depth} | Output: {self.output_name}.json')
        if self.block_homepage:
            self.logger.info(f'🚫 Homepage bloccata: {self.homepage_url}')
        else:
            self.logger.info(f'✅ Homepage consentita (mode shallow)')
        
        # Statistiche
        self.stats_duplicates_skipped = 0
        self.stats_self_loops_skipped = 0
        self.stats_blacklist_skipped = 0
        self.stats_homepage_skipped = 0

        # ========== SALVATAGGIO PERIODICO ==========
        self.save_interval = 50  # Salva ogni N pagine visitate
        self._last_save_count = 0

        # Crea subito il file vuoto per garantire che esista
        self._save_results(partial=True)

    def _load_urls_from_file(self):
        """
        Carica gli URL dal file lista_siti.txt.

        Returns:
            Lista di URL letti dal file

        Raises:
            FileNotFoundError: Se il file non esiste
            ValueError: Se il file è vuoto o non contiene URL validi
        """
        if not self.LISTA_SITI_PATH.exists():
            raise FileNotFoundError(
                f"File lista_siti.txt non trovato: {self.LISTA_SITI_PATH}\n"
                f"Crea il file con uno o più URL (uno per riga) oppure passa -a start_url=<URL>"
            )

        urls = []
        with open(self.LISTA_SITI_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                # Ignora righe vuote e commenti
                if url and not url.startswith('#'):
                    urls.append(url)

        if not urls:
            raise ValueError(
                f"Nessun URL trovato in {self.LISTA_SITI_PATH}\n"
                f"Aggiungi almeno un URL (uno per riga) oppure passa -a start_url=<URL>"
            )

        self.logger.info(f"📂 Caricati {len(urls)} URL da {self.LISTA_SITI_PATH}")
        return urls

    def _get_output_path(self):
        """Restituisce il path del file di output."""
        # Usa output_dir custom se specificata, altrimenti output/ nella root del progetto
        if self.output_dir:
            output_dir = self.output_dir
        else:
            output_dir = Path(__file__).parent.parent.parent / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f'{self.output_name}.json'

    def _save_results(self, partial=False):
        """
        Salva i risultati correnti su file.

        Args:
            partial: Se True, indica che è un salvataggio parziale (crawl in corso)
        """
        with self._lock:
            # Copia locale per evitare modifiche durante il salvataggio
            tree_copy = dict(self.site_tree)
            visited_count = len(self.visited_urls)

        # Stats
        broken = sum(1 for v in tree_copy.values() if v.get('status') == 'broken')
        files = sum(1 for v in tree_copy.values() if v.get('status') == 'file')

        output_path = self._get_output_path()

        data = {
            'tree': tree_copy,
            'stats': {
                'total_pages': visited_count,
                'root_url': self.start_urls[0],
                'mode': self.mode,
                'max_depth': self.max_depth,
                'broken_links': broken,
                'files': files,
                'duplicates_skipped': self.stats_duplicates_skipped,
                'self_loops_skipped': self.stats_self_loops_skipped,
                'blacklist_skipped': self.stats_blacklist_skipped,
                'partial': partial,  # Indica se il crawl era completo o meno
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if partial:
            self.logger.info(f'💾 Salvataggio parziale: {visited_count} pagine -> {output_path}')

        self._last_save_count = visited_count

    def start_requests(self):
        """Genera le request iniziali"""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error("scrapy-playwright non disponibile!")
            return

        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                dont_filter=True,
                errback=self.handle_error,
                meta={
                    'playwright': True,
                    'playwright_context': 'default',  # Riutilizza lo stesso contesto
                    'playwright_page_methods': [
                        # Aspetta che la rete sia inattiva (nessuna richiesta per 500ms)
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                }
            )

    async def parse(self, response):
        """Parse della pagina"""
        current_url = self.normalize_url(response.url)

        # Check duplicati (thread-safe)
        with self._lock:
            if current_url in self.visited_urls:
                self.stats_duplicates_skipped += 1
                return

            self.visited_urls.add(current_url)
            visited_count = len(self.visited_urls)

            # Estrai testo della pagina per analisi privacy
            # Prende tutto il testo visibile dal body, limitato a 5000 caratteri
            page_text_parts = response.css('body *::text').getall()
            page_text = ' '.join(t.strip() for t in page_text_parts if t.strip())
            content_text = page_text[:5000] if len(page_text) > 5000 else page_text

            # Crea o aggiorna nodo
            if current_url not in self.site_tree:
                # Nuovo nodo
                self.site_tree[current_url] = {
                    'parents': [],
                    'children': [],
                    'title': response.css('title::text').get(),
                    'depth': response.meta.get('depth', 0),
                    'display_name': urlparse(current_url).path.split('/')[-1] or 'home',
                    'status': 'ok',
                    'status_code': response.status,
                    'content_text': content_text,
                }
            else:
                # Aggiorna nodo esistente (era pending, ora è visitato)
                self.site_tree[current_url]['status'] = 'ok'
                self.site_tree[current_url]['status_code'] = response.status
                self.site_tree[current_url]['title'] = response.css('title::text').get()
                self.site_tree[current_url]['content_text'] = content_text

            # Gestisci parent
            parent_url = response.meta.get('parent_url')
            if parent_url:
                if parent_url not in self.site_tree[current_url]['parents']:
                    self.site_tree[current_url]['parents'].append(parent_url)
                if parent_url in self.site_tree:
                    if current_url not in self.site_tree[parent_url]['children']:
                        self.site_tree[parent_url]['children'].append(current_url)

        self.logger.info(f'🔍 [{visited_count}] {current_url}')

        # ========== SALVATAGGIO PERIODICO ==========
        if visited_count - self._last_save_count >= self.save_interval:
            self._save_results(partial=True)

        # ========== ESCLUSIONE SELETTORI IN BASE AL MODE ==========
        # Mode deep: esclude nav (per restare dentro una sezione)
        # Mode shallow: include nav (per scoprire le sezioni del sito)
        if self.mode == 'deep':
            excluded_selectors = [
                'header a', 'footer a', 'nav a', '.navbar a',
                '.breadcrumb a', '.sidebar a', '.widget a',
                '.pagination a', '.pager a',
            ]
        else:  # shallow
            excluded_selectors = [
                'footer a',  # Solo footer (link legali, privacy, etc.)
                '.pagination a', '.pager a',  # Evita infinite pagine di lista
            ]
        exclude_selector = ", ".join(excluded_selectors)
        excluded_hrefs = response.css(exclude_selector + '::attr(href)').getall()
        excluded_urls = set(urljoin(response.url, href) for href in excluded_hrefs)

        # Blacklist path
        blacklisted_paths = ['/login', '/logout', '/privacy-policy', '/cookie-policy',
                            '/wp-content', '/sites', '/uploads', '/autenticazione']
        blacklisted_urls = set(urljoin(response.url, path) for path in blacklisted_paths)
        
        # ========== HOMEPAGE: blocca solo in mode deep ==========
        if self.block_homepage:
            blacklisted_urls.add(self.homepage_url)
        
        excluded_urls = excluded_urls.union(blacklisted_urls)

        # Trova contenuto - combina link da tutti i selettori
        content_selectors = [
            'main', '[role="main"]', '#content', '.main-content', 'article',
            '.page-content', '#main-content', '.entry-content', '#corpo', '.contenuto'
        ]
        all_links = set()
        matched_selectors = []

        for selector in content_selectors:
            links = response.css(f'{selector} a::attr(href)').getall()
            if links:
                all_links.update(links)
                matched_selectors.append(f'{selector}({len(links)})')

        # Fallback a body se nessun selettore ha matchato
        if not all_links:
            all_links = set(response.css('body a::attr(href)').getall())
            if all_links:
                matched_selectors.append(f'body({len(all_links)})')

        if matched_selectors:
            self.logger.info(f'✅ Contenuto: {", ".join(matched_selectors)} - Tot: {len(all_links)} link')
        else:
            self.logger.warning(f'⚠️ Nessun link trovato in {current_url}')
            # Non fare return silenzioso - la pagina è già nel tree con status ok

        all_links = list(all_links)

        # Filtra e normalizza link
        processed = set()
        clean_links = []
        
        for href in all_links:
            if not href or href.startswith('#') or href.startswith('mailto:'):
                continue
            
            if href in processed:
                continue
            processed.add(href)
            
            abs_url = self.normalize_url(urljoin(response.url, href))
            
            # ========== FILTRO HOMEPAGE: solo in mode deep ==========
            if self.block_homepage and abs_url == self.homepage_url:
                self.stats_homepage_skipped += 1
                continue
            
            if abs_url not in excluded_urls:
                clean_links.append(abs_url)

        self.logger.info(f'📋 {len(clean_links)} link da processare')

        # Estensioni file
        doc_ext = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip',
                   '.jpg', '.jpeg', '.png', '.gif', '.p7m', '.xml.p7m']
        media_ext = ['.mp3', '.mp4', '.avi']

        # Pattern URL che indicano download di file (senza estensione)
        download_patterns = ['/download/', '/downloads/', '/scarica/', '/allegato/', '/allegati/']

        links_generated = 0

        for abs_url in clean_links:
            try:
                parsed = urlparse(abs_url)
                url_lower = abs_url.lower()

                # Skip blacklist
                if any(bl in parsed.path for bl in ['/wp-content', '/sites', '/uploads']):
                    self.stats_blacklist_skipped += 1
                    continue

                # Check file by extension (endswith OR present anywhere in URL path)
                is_doc = any(url_lower.endswith(ext) or (ext + '/') in url_lower or (ext + '?') in url_lower for ext in doc_ext)
                is_media = any(url_lower.endswith(ext) or (ext + '/') in url_lower for ext in media_ext)

                # Check file by URL pattern (download links without extension)
                is_download_url = any(pattern in url_lower for pattern in download_patterns)
                
                if is_media:
                    continue

                # Treat as file: documents with extensions OR download URL patterns
                if is_doc or is_download_url:
                    # Determina il tipo di file
                    file_type = None
                    for ext in doc_ext:
                        if url_lower.endswith(ext):
                            file_type = ext
                            break
                    if not file_type and is_download_url:
                        file_type = ".pdf"  # Assume PDF per download link generici

                    with self._lock:
                        if abs_url not in self.site_tree:
                            self.site_tree[abs_url] = {
                                'parents': [current_url],
                                'children': [],
                                'title': None,
                                'depth': response.meta.get('depth', 0) + 1,
                                'display_name': parsed.path.split('/')[-1],
                                'status': 'file',
                                'status_code': None,
                                'file_type': file_type,  # Per analisi privacy
                            }
                        if abs_url not in self.site_tree[current_url]['children']:
                            self.site_tree[current_url]['children'].append(abs_url)
                    continue
                
                # Link normale — accetta stesso dominio o qualsiasi sottodominio
                if parsed.netloc == self.allowed_domain or parsed.netloc.endswith('.' + self.allowed_root_domain):
                    # ========== FILTRO HOMEPAGE: solo in mode deep ==========
                    if self.block_homepage and abs_url == self.homepage_url:
                        self.stats_homepage_skipped += 1
                        self.logger.debug(f'⏩ SKIP homepage: {abs_url}')
                        continue
                    
                    # Self-loop check
                    if abs_url == current_url:
                        self.stats_self_loops_skipped += 1
                        continue

                    # Aggiorna tree (thread-safe)
                    with self._lock:
                        if abs_url not in self.site_tree[current_url]['children']:
                            self.site_tree[current_url]['children'].append(abs_url)

                        if abs_url not in self.site_tree:
                            self.site_tree[abs_url] = {
                                'parents': [current_url],
                                'children': [],
                                'title': None,
                                'depth': response.meta.get('depth', 0) + 1,
                                'display_name': parsed.path.split('/')[-1] or 'home',
                                'status': 'pending',
                            }
                        else:
                            if current_url not in self.site_tree[abs_url]['parents']:
                                self.site_tree[abs_url]['parents'].append(current_url)

                        should_crawl = abs_url not in self.visited_urls
                        
                        # ========== CONTROLLO PROFONDITÀ ==========
                        next_depth = response.meta.get('depth', 0) + 1
                        if next_depth > self.max_depth:
                            should_crawl = False

                    if should_crawl:
                        links_generated += 1
                        yield scrapy.Request(
                            url=abs_url,
                            callback=self.parse,
                            errback=self.handle_error,
                            dont_filter=True,
                            meta={
                                'playwright': True,
                                'playwright_context': 'default',  # Riutilizza lo stesso contesto
                                'playwright_page_methods': [
                                    # Aspetta che la rete sia inattiva (nessuna richiesta per 500ms)
                                    PageMethod('wait_for_load_state', 'domcontentloaded'),
                                ],
                                'parent_url': current_url,
                                'depth': next_depth
                            }
                        )
            
            except Exception as e:
                self.logger.error(f'Errore: {e}')

        self.logger.info(f'🚀 Generati {links_generated} request | Tot: {len(self.visited_urls)}')

    def handle_error(self, failure):
        """Gestione errori con informazioni dettagliate"""
        url = failure.request.url

        # Estrai informazioni dall'errore
        error_type = failure.type.__name__ if failure.type else 'Unknown'
        error_msg = str(failure.value) if failure.value else 'Errore sconosciuto'

        # Ottieni meta dalla request
        meta = failure.request.meta
        parent_url = meta.get('parent_url')
        depth = meta.get('depth', 0)

        self.logger.error(f'❌ {error_type} su {url}: {error_msg}')

        with self._lock:
            if url not in self.site_tree:
                self.site_tree[url] = {
                    'parents': [parent_url] if parent_url else [],
                    'children': [],
                    'title': None,
                    'depth': depth,
                    'display_name': urlparse(url).path.split('/')[-1] or 'broken',
                    'status': 'broken',
                    'status_code': None,
                    'error': f'{error_type}: {error_msg}',
                }
            else:
                # Aggiorna lo status se già esisteva
                self.site_tree[url]['status'] = 'broken'
                self.site_tree[url]['error'] = f'{error_type}: {error_msg}'

    def closed(self, reason):
        """Salvataggio risultati finale"""
        self.logger.info(f'\n✅ Crawl completato ({reason}): {len(self.visited_urls)} pagine')

        # ========== PULIZIA: Marca nodi pending come non visitati ==========
        with self._lock:
            for info in self.site_tree.values():
                # Se è ancora pending dopo il crawl, non è stato visitato
                if info.get('status') == 'pending':
                    info['status'] = 'not_visited'

        # Salvataggio finale (partial=False indica crawl completato)
        self._save_results(partial=False)

        # Stats per log
        broken = sum(1 for v in self.site_tree.values() if v.get('status') == 'broken')
        files = sum(1 for v in self.site_tree.values() if v.get('status') == 'file')
        not_visited = sum(1 for v in self.site_tree.values() if v.get('status') == 'not_visited')

        self.logger.info(f'📊 Link rotti: {broken}')
        self.logger.info(f'📊 File: {files}')
        self.logger.info(f'📊 Non visitati: {not_visited}')
        self.logger.info(f'📊 Duplicati evitati: {self.stats_duplicates_skipped}')
        self.logger.info(f'📊 Self-loops evitati: {self.stats_self_loops_skipped}')
        self.logger.info(f'💾 Salvato in: {self._get_output_path()}')