import scrapy
import json
from urllib.parse import urlparse, urljoin

class SiteMapSpider(scrapy.Spider):
    name = 'sitemap_spider'
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DEPTH_LIMIT': 3,  # Limite di profondità
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,  # Aumentare questo valore
        'ROBOTSTXT_OBEY': False,  # Disabilitare se non necessario
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 0,
        'HTTPCACHE_DIR': 'httpcache',
        'HTTPCACHE_IGNORE_HTTP_CODES': [],
        'HTTPCACHE_STORAGE': 'scrapy.extensions.httpcache.FilesystemCacheStorage'
    }
    
    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://www.comune.piedimulera.vb.it/it-it/amministrazione/amministrazione-trasparente']
        self.allowed_domain = urlparse(self.start_urls[0]).netloc
        self.visited_urls = set()
        self.site_tree = {}

    def parse(self, response):
        current_url = response.url.split('?')[0].split('#')[0]
        
        # Inizializza la struttura per l'URL corrente se non esiste
        if current_url not in self.site_tree:
            self.site_tree[current_url] = {
                'parents': [],  # Lista invece di singolo parent
                'children': [],
                'title': response.css('title::text').get(),
                'depth': response.meta.get('depth', 0),
                'display_name': urlparse(current_url).path.split('/')[-1] or '/'  # Nome corto
            }
        
        # Aggiungi il parent alla lista se esiste e non è già presente
        parent_url = response.meta.get('parent_url')
        if parent_url and parent_url not in self.site_tree[current_url]['parents']:
            self.site_tree[current_url]['parents'].append(parent_url)

        main_content_links = response.css('body *:not(header) *:not(footer) a::attr(href)').getall()
        
        # Oppure più specifico usando le classi/id esistenti
        excluded_sections = [
            'header',
            'footer',
            '#header-nav',
            '#footer-main',
            '#header-top',
            '#header-main',
            '#side-nav',
            '.Megamenu',
            '.cookiebar'
        ]
        
        selector = ' '.join(f':not({section})' for section in excluded_sections)
        main_content_links = response.css(f'#content {selector} a::attr(href)').getall()
        
        self.logger.info(f'Trovati {len(main_content_links)} link nel contenuto principale')
        # Trova tutti i link nella pagina
        for link in main_content_links:
            try:
                absolute_url = urljoin(response.url, link).split('?')[0].split('#')[0]
                parsed_url = urlparse(absolute_url)
                
                # Verifica che il link sia valido e dello stesso dominio
                if (parsed_url.netloc == self.allowed_domain and 
                    absolute_url not in self.visited_urls and
                    parsed_url.scheme in ['http', 'https']):
                    
                    # Aggiunge il link come figlio dell'URL corrente
                    if absolute_url not in self.site_tree[current_url]['children']:
                        self.site_tree[current_url]['children'].append(absolute_url)
                    
                    # Segue il link
                    self.logger.debug(f'Seguendo link: {absolute_url}')
                    yield response.follow(
                        absolute_url,
                        callback=self.parse,
                        meta={
                            'parent_url': current_url,
                            'depth': response.meta.get('depth', 0) + 1
                        }
                    )
            except Exception as e:
                self.logger.error(f'Errore nel processare il link {link}: {str(e)}')

    def closed(self, reason):
        # Rimuovi solo i nodi completamente isolati
        cleaned_tree = {k: v for k, v in self.site_tree.items() 
                    if v['parents'] or v['children']}
        
        output_path = 'site_tree.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tree': cleaned_tree,
                'stats': {
                    'total_pages': len(self.visited_urls),
                    'root_url': self.start_urls[0],
                    'multi_parent_nodes': sum(1 for v in cleaned_tree.values() if len(v['parents']) > 1)
                }
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f'Salvate {len(self.visited_urls)} pagine uniche nella struttura ad albero')