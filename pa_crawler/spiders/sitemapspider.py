import scrapy
from scrapy_playwright.page import PageMethod
import json
from urllib.parse import urlparse, urljoin

class SiteMapSpider(scrapy.Spider):
    name = 'sitemap_spider'
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'ROBOTSTXT_OBEY': False,
        'DEPTH_LIMIT': 3,
        'CONCURRENT_REQUESTS': 2,  # Ridotto con Playwright
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        },
        'HTTPCACHE_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_TIMEOUT': 30,
    }
    
    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://www.comune.piedimulera.vb.it/it-it/amministrazione/amministrazione-trasparente']
        self.allowed_domain = urlparse(self.start_urls[0]).netloc
        self.visited_urls = set()
        self.site_tree = {}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                    'depth': 0,
                    'parent_url': None
                },
                errback=self.errback_httpbin,
                dont_filter=True
            )

    def parse(self, response):
        current_url = response.url.split('?')[0].split('#')[0]
        
        #self.logger.info(f'✅ Parsing riuscito: {current_url} (status: {response.status})')
        
        # Marca come visitato
        self.visited_urls.add(current_url)
        
        # Crea/aggiorna nodo base
        if current_url not in self.site_tree:
            self.site_tree[current_url] = {
                'parents': [],
                'children': [],
                'title': response.css('title::text').get(),
                'depth': response.meta.get('depth', 0),
                'display_name': urlparse(current_url).path.split('/')[-1] or 'home',
                'status': 'ok',
                'status_code': response.status,
                'is_dynamic': False
            }
        else:
            self.site_tree[current_url]['status'] = 'ok'
            self.site_tree[current_url]['status_code'] = response.status
        
        # Gestisci parent
        parent_url = response.meta.get('parent_url')
        if parent_url and parent_url not in self.site_tree[current_url]['parents']:
            self.site_tree[current_url]['parents'].append(parent_url)
            if parent_url in self.site_tree and current_url not in self.site_tree[parent_url]['children']:
                self.site_tree[parent_url]['children'].append(current_url)

        # ============================================
        # SCRAPING NORMALE
        # ============================================
        excluded_sections = [
            'header', 'footer', '#header-nav', '#footer-main',
            '#header-top', '#header-main', '#side-nav', '.Megamenu', '.cookiebar'
        ]
        
        selector = ' '.join(f':not({section})' for section in excluded_sections)
        main_content_links = response.css(f'#content {selector} a::attr(href)').getall()
        
        #self.logger.info(f'   🔗 Trovati {len(main_content_links)} link in {current_url}')
        
        excluded_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv',
            '.xml', '.json', '.csv', '.txt'
        ]
        
        for link in main_content_links:
            try:
                absolute_url = urljoin(response.url, link).split('?')[0].split('#')[0]
                parsed_url = urlparse(absolute_url)
                
                url_lower = absolute_url.lower()
                
                # Lista estensioni
                excluded_extensions = [
                    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                    '.zip', '.rar', '.7z', '.tar', '.gz',
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
                    '.mp3', '.mp4', '.avi', '.mov', '.wmv',
                    '.xml', '.json', '.csv', '.txt'
                ]
                
                download_patterns = ['/download/', '/file/', '/attachment/', '/documento/']
                
                is_downloadable = (
                    any(url_lower.endswith(ext) for ext in excluded_extensions) or  # Estensione
                    any(pattern in url_lower for pattern in download_patterns) or   # Pattern URL
                    'pdf' in url_lower or 'doc' in url_lower  # Keyword nel nome
                )
                
                if is_downloadable:
                    self.logger.debug(f'      📄 Saltato file scaricabile: {absolute_url}')
                    
                    if absolute_url not in self.site_tree:
                        # Determina il tipo dal nome o dall'estensione
                        file_type = 'unknown'
                        for ext in excluded_extensions:
                            if ext in url_lower:
                                file_type = ext
                                break
                        
                        self.site_tree[absolute_url] = {
                            'parents': [current_url],
                            'children': [],
                            'title': None,
                            'depth': response.meta.get('depth', 0) + 1,
                            'display_name': urlparse(absolute_url).path.split('/')[-1] or 'file',
                            'status': 'file',
                            'status_code': None,
                            'file_type': file_type
                        }
                    
                    # Aggiungi come child del nodo corrente
                    if absolute_url not in self.site_tree[current_url]['children']:
                        self.site_tree[current_url]['children'].append(absolute_url)
                    
                    # Aggiungi parent al file
                    if current_url not in self.site_tree[absolute_url]['parents']:
                        self.site_tree[absolute_url]['parents'].append(current_url)
                    
                    continue 
                
                if (parsed_url.netloc == self.allowed_domain and
                    parsed_url.scheme in ['http', 'https']):
                    
                    if absolute_url not in self.site_tree[current_url]['children']:
                        self.site_tree[current_url]['children'].append(absolute_url)

                    if absolute_url not in self.site_tree:
                        self.site_tree[absolute_url] = {
                            'parents': [],
                            'children': [],
                            'title': None,
                            'depth': response.meta.get('depth', 0) + 1,
                            'display_name': urlparse(absolute_url).path.split('/')[-1] or 'home',
                            'status': 'pending',
                            'status_code': None
                        }
                    
                    if current_url not in self.site_tree[absolute_url]['parents']:
                        self.site_tree[absolute_url]['parents'].append(current_url)

                    # Segui solo se non visitato
                    if absolute_url not in self.visited_urls:
                        #self.logger.debug(f'      ➡️  Seguendo: {absolute_url}')
                        yield scrapy.Request(
                            absolute_url,
                            callback=self.parse,
                            errback=self.errback_httpbin,
                            meta={
                                'playwright': True,
                                'playwright_page_methods': [
                                    PageMethod('wait_for_load_state', 'domcontentloaded'),
                                ],
                                'parent_url': current_url,
                                'depth': response.meta.get('depth', 0) + 1
                            }
                        )
            except Exception as e:
                self.logger.error(f'❌ Errore processando link {link}: {str(e)}')

    def errback_httpbin(self, failure):
        """Gestisce gli errori HTTP (link rotti)"""
        request = failure.request
        url = request.url
        parent_url = request.meta.get('parent_url')
        
        self.logger.error(f'❌ ERRORE su {url}: {type(failure.value).__name__}: {str(failure.value)}')
        
        if url not in self.site_tree:
            self.site_tree[url] = {
                'parents': [],
                'children': [],
                'title': None,
                'depth': request.meta.get('depth', 0),
                'display_name': urlparse(url).path.split('/')[-1] or 'broken-link'
            }
        
        self.site_tree[url]['status'] = 'broken'
        self.site_tree[url]['error'] = f"{type(failure.value).__name__}: {str(failure.value)}"
        
        if hasattr(failure.value, 'response') and failure.value.response:
            self.site_tree[url]['status_code'] = failure.value.response.status
        else:
            self.site_tree[url]['status_code'] = None
        
        if parent_url and parent_url not in self.site_tree[url]['parents']:
            self.site_tree[url]['parents'].append(parent_url)

    def closed(self, reason):
        cleaned_tree = {k: v for k, v in self.site_tree.items() 
                       if v.get('parents') or v.get('children') or v.get('depth', 0) == 0}
        
        broken_count = sum(1 for v in cleaned_tree.values() if v.get('status') == 'broken')
        pending_count = sum(1 for v in cleaned_tree.values() if v.get('status') == 'pending')
        dynamic_count = sum(1 for v in cleaned_tree.values() if v.get('is_dynamic'))
        file_count = sum(1 for v in cleaned_tree.values() if v.get('status') == 'file')  # ✅ NUOVO
        
        output_path = 'site_tree.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tree': cleaned_tree,
                'stats': {
                    'total_pages': len(self.visited_urls),
                    'root_url': self.start_urls[0],
                    'multi_parent_nodes': sum(1 for v in cleaned_tree.values() if len(v.get('parents', [])) > 1),
                    'broken_links_count': broken_count,
                    'pending_links_count': pending_count,
                    'dynamic_pages_count': dynamic_count,
                    'file_count': file_count
                }
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f'✓ Salvate {len(self.visited_urls)} pagine uniche')
        self.logger.info(f'✓ Link rotti: {broken_count}')
        self.logger.info(f'✓ File scaricabili: {file_count}')
        self.logger.info(f'✓ Pagine dinamiche: {dynamic_count}')