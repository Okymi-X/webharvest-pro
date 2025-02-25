from scraper import WebScraper
from selenium.webdriver.common.by import By
import time
from tqdm import tqdm
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup, Comment
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import numpy as np
from json_parser import JsonParser

class DataDetector:
    """Classe pour la détection intelligente des données"""
    
    EMAIL_PATTERNS = [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r'mailto:[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r'email[:\s]+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r'e-mail[:\s]+[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    ]
    
    PHONE_PATTERNS = [
        r'\+?[\d\s.-]{10,}',
        r'(?:tel|phone|mobile)[:\s]+[\d\s.-]{10,}',
        r'\(\d{2,4}\)\s*\d{6,10}',
        r'\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}'
    ]
    
    SOCIAL_PATTERNS = {
        'facebook': r'(?:facebook\.com|fb\.com)/[\w.]+',
        'twitter': r'(?:twitter\.com|x\.com)/[\w]+',
        'linkedin': r'linkedin\.com/(?:in|company)/[\w-]+',
        'instagram': r'instagram\.com/[\w.]+',
    }
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = RandomForestClassifier(n_estimators=100)
        self.trained = False
    
    def extract_all_data(self, text, html):
        """Extrait toutes les données sensibles du texte et du HTML"""
        data = {
            'emails': self.extract_emails(text),
            'phones': self.extract_phones(text),
            'social_media': self.extract_social_media(text),
            'potential_sensitive': self.detect_potential_sensitive(html)
        }
        return data
    
    def extract_emails(self, text):
        """Extrait tous les emails avec contexte"""
        emails = []
        for pattern in self.EMAIL_PATTERNS:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                email = match.group()
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                emails.append({
                    'email': email.strip(),
                    'context': context.strip(),
                    'confidence': self.validate_email(email)
                })
        return emails
    
    def extract_phones(self, text):
        """Extrait tous les numéros de téléphone avec contexte"""
        phones = []
        for pattern in self.PHONE_PATTERNS:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                phone = match.group()
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                phones.append({
                    'phone': self.normalize_phone(phone),
                    'context': context.strip(),
                    'confidence': self.validate_phone(phone)
                })
        return phones
    
    def extract_social_media(self, text):
        """Extrait les liens des réseaux sociaux"""
        social = {}
        for platform, pattern in self.SOCIAL_PATTERNS.items():
            matches = re.finditer(pattern, text, re.I)
            social[platform] = [match.group() for match in matches]
        return social
    
    def normalize_phone(self, phone):
        """Normalise un numéro de téléphone"""
        return re.sub(r'[^\d+]', '', phone)
    
    def validate_email(self, email):
        """Valide un email et retourne un score de confiance"""
        if '@' not in email:
            return 0.0
        parts = email.split('@')
        if len(parts) != 2:
            return 0.0
        local, domain = parts
        if not domain.count('.'):
            return 0.0
        return min(1.0, (len(local) + len(domain)) / 50)
    
    def validate_phone(self, phone):
        """Valide un numéro de téléphone et retourne un score de confiance"""
        digits = re.sub(r'\D', '', phone)
        return min(1.0, len(digits) / 15)
    
    def detect_potential_sensitive(self, html):
        """Détecte les données potentiellement sensibles dans le HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        sensitive_data = []
        
        # Chercher dans les attributs sensibles
        sensitive_attrs = ['data-email', 'data-phone', 'data-user', 'data-id']
        for attr in sensitive_attrs:
            elements = soup.find_all(attrs={attr: True})
            for elem in elements:
                sensitive_data.append({
                    'type': attr,
                    'value': elem[attr],
                    'context': elem.get_text().strip()
                })
        
        # Chercher dans les classes et IDs sensibles
        sensitive_patterns = ['email', 'phone', 'contact', 'user', 'profile']
        for pattern in sensitive_patterns:
            elements = soup.find_all(class_=re.compile(pattern, re.I))
            elements.extend(soup.find_all(id=re.compile(pattern, re.I)))
            for elem in elements:
                sensitive_data.append({
                    'type': 'potential_' + pattern,
                    'value': elem.get_text().strip(),
                    'context': elem.parent.get_text().strip()
                })
        
        return sensitive_data
    
    def train_on_data(self, data_file):
        """Entraîne le modèle sur des données étiquetées"""
        try:
            df = pd.read_json(data_file)
            X = self.vectorizer.fit_transform(df['text'])
            y = df['is_sensitive']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
            self.classifier.fit(X_train, y_train)
            self.trained = True
            
            score = self.classifier.score(X_test, y_test)
            print(f"Modèle entraîné avec un score de: {score}")
            
        except Exception as e:
            print(f"Erreur lors de l'entraînement: {str(e)}")
    
    def save_model(self, filename):
        """Sauvegarde le modèle entraîné"""
        if not self.trained:
            return
        
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier
        }
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filename):
        """Charge un modèle entraîné"""
        try:
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
            self.vectorizer = model_data['vectorizer']
            self.classifier = model_data['classifier']
            self.trained = True
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {str(e)}")

def is_valid_url(url, allow_external=False, base_domain=None):
    """Vérifie si l'URL est valide et utilisable"""
    try:
        parsed = urlparse(url)
        # Ignorer les ancres et les liens javascript
        if not parsed.scheme or not parsed.netloc or parsed.scheme not in ['http', 'https']:
            return False
        if url.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            return False
        if not allow_external and base_domain and parsed.netloc != base_domain:
            return False
        return True
    except:
        return False

class SiteMapper:
    def __init__(self, base_url, explore_external=True):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.found_urls = set()
        self.external_urls = set()
        self.data_by_page = {}
        self.explore_external = explore_external
        self.scraper = WebScraper(headless=True)
        self.data_detector = DataDetector()
        self.json_parser = JsonParser()
        self.log_callback = print  # Par défaut, utilise print
        self.stats_callback = lambda x: None  # Par défaut, ne fait rien
        self.should_stop = False
        self.pause = False
        self.connection_pool = []
        self.max_pool_size = 5
        self.delay = 2  # Délai entre les requêtes en secondes
        self.respect_robots = True
        
        # Statistiques
        self.stats = {
            'pages_visited': 0,
            'internal_links': 0,
            'external_links': 0,
            'emails_found': 0,
            'phones_found': 0,
            'errors': 0,
            'progress': 0
        }
        
        # Initialiser le pool de connexions
        self.init_connection_pool()
    
    def init_connection_pool(self):
        """Initialise le pool de connexions"""
        for _ in range(self.max_pool_size):
            try:
                scraper = WebScraper(headless=True)
                self.connection_pool.append(scraper)
            except Exception as e:
                self.log(f"Erreur lors de l'initialisation d'une connexion: {str(e)}")
    
    def get_connection(self):
        """Obtient une connexion du pool"""
        while True:
            for scraper in self.connection_pool:
                if not hasattr(scraper, 'in_use') or not scraper.in_use:
                    scraper.in_use = True
                    return scraper
            time.sleep(0.1)
    
    def release_connection(self, scraper):
        """Libère une connexion"""
        scraper.in_use = False
    
    def update_stats(self, **kwargs):
        """Met à jour les statistiques et notifie l'interface"""
        self.stats.update(kwargs)
        self.stats_callback(self.stats)
    
    def log(self, message):
        """Envoie un message de log à l'interface"""
        self.log_callback(message)

    def extract_all_links(self, soup, current_url):
        """Extrait tous les liens de la page"""
        internal_links = set()
        external_links = set()
        
        # Liens standards
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Convertir les URLs relatives en absolues
            full_url = urljoin(current_url, href)
            
            if is_valid_url(full_url, True, self.domain):
                if urlparse(full_url).netloc == self.domain:
                    internal_links.add(full_url)
                else:
                    external_links.add(full_url)
        
        # Nettoyer les URLs
        internal_links = {self.clean_url(url) for url in internal_links}
        external_links = {self.clean_url(url) for url in external_links}
        
        return internal_links, external_links
    
    def clean_url(self, url):
        """Nettoie une URL en retirant les paramètres de tracking et les ancres"""
        try:
            parsed = urlparse(url)
            # Retirer les paramètres de tracking courants
            query = re.sub(r'utm_[^&]*&?', '', parsed.query)
            query = re.sub(r'fbclid=[^&]*&?', '', query)
            # Reconstruire l'URL sans l'ancre
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + query if query else ''}"
        except:
            return url

    def explore_page(self, url, depth=0, max_depth=2):
        """Explore une page et extrait ses données"""
        if url in self.visited_urls or depth > max_depth or self.should_stop:
            return
        
        while self.pause:
            time.sleep(1)
            if self.should_stop:
                return
        
        self.visited_urls.add(url)
        self.log(f"\nExploration de: {url} (profondeur: {depth})")
        
        scraper = self.get_connection()
        try:
            if not scraper.navigate_to(url):
                self.stats['errors'] += 1
                return
            
            # Respecter le délai entre les requêtes
            time.sleep(self.delay)
            
            # Extraire le contenu de la page
            page_source = scraper.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Révéler le contenu caché
            scraper.reveal_hidden_elements()
            scraper.expand_all_elements()
            scraper.scroll_to_bottom()
            
            # Attendre le chargement du contenu dynamique
            scraper.wait_for_dynamic_content()
            
            # Extraire à nouveau après les modifications
            page_source = scraper.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            text_content = soup.get_text()
            
            # Détecter la structure et les données sensibles
            structure = detect_data_structure(scraper)
            items = scrape_with_structure(scraper, url, structure)
            sensitive_data = self.data_detector.extract_all_data(text_content, page_source)
            
            # Mettre à jour les statistiques
            self.stats['pages_visited'] += 1
            self.stats['emails_found'] += len(sensitive_data.get('emails', []))
            self.stats['phones_found'] += len(sensitive_data.get('phones', []))
            
            # Extraire les liens
            internal_links, external_links = self.extract_all_links(soup, url)
            
            self.stats['internal_links'] = len(self.found_urls) + len(internal_links)
            self.stats['external_links'] = len(self.external_urls) + len(external_links)
            
            # Sauvegarder les données de cette page
            page_data = {
                'url': url,
                'structure': structure,
                'items': items,
                'sensitive_data': sensitive_data,
                'internal_links': list(internal_links),
                'external_links': list(external_links),
                'timestamp': datetime.now().isoformat(),
                'depth': depth
            }
            
            page_id = hashlib.md5(url.encode()).hexdigest()
            self.data_by_page[page_id] = page_data
            
            # Ajouter les nouveaux liens à explorer
            for link in internal_links:
                if link not in self.visited_urls:
                    self.found_urls.add((link, depth + 1))
            
            # Gérer les liens externes
            if self.explore_external:
                for link in external_links:
                    if link not in self.visited_urls:
                        self.external_urls.add((link, depth + 1))
            
            # Mettre à jour la progression
            if len(self.visited_urls) > 0:
                total_links = len(self.found_urls) + len(self.external_urls) + len(self.visited_urls)
                self.stats['progress'] = (len(self.visited_urls) / total_links) * 100
            
            self.update_stats(**self.stats)
            
        except Exception as e:
            self.log(f"Erreur lors de l'exploration de {url}: {str(e)}")
            self.stats['errors'] += 1
        
        finally:
            self.release_connection(scraper)

    def explore_site(self, max_pages=None, max_depth=2, max_workers=3):
        """Explore le site entier de manière récursive"""
        self.should_stop = False
        self.pause = False
        self.found_urls.add((self.base_url, 0))
        futures = set()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while (self.found_urls or futures or (self.explore_external and self.external_urls)) and \
                  (max_pages is None or len(self.visited_urls) < max_pages) and \
                  not self.should_stop:
                
                while self.pause:
                    time.sleep(1)
                    if self.should_stop:
                        break
                
                # Soumettre de nouvelles tâches
                while self.found_urls and len(futures) < max_workers and \
                      (max_pages is None or len(self.visited_urls) < max_pages) and \
                      not self.should_stop:
                    current_url, depth = self.found_urls.pop()
                    if depth <= max_depth and current_url not in self.visited_urls:
                        future = executor.submit(self.explore_page, current_url, depth, max_depth)
                        futures.add(future)
                        self.log(f"Ajout de {current_url} à la file d'exploration")
                
                # Explorer les liens externes si activé
                if self.explore_external and not self.found_urls and self.external_urls and not self.should_stop:
                    while self.external_urls and len(futures) < max_workers and \
                          (max_pages is None or len(self.visited_urls) < max_pages):
                        current_url, depth = self.external_urls.pop()
                        if depth <= max_depth and current_url not in self.visited_urls:
                            future = executor.submit(self.explore_page, current_url, depth, max_depth)
                            futures.add(future)
                            self.log(f"Ajout du lien externe {current_url} à la file d'exploration")
                
                # Attendre qu'au moins une tâche soit terminée
                if futures:
                    done, futures = wait(futures, return_when=FIRST_COMPLETED)
                    for future in done:
                        try:
                            future.result()
                        except Exception as e:
                            self.log(f"Erreur lors de l'exploration: {str(e)}")
                            self.stats['errors'] += 1
                else:
                    time.sleep(1)
                
                self.log(f"Progression: {len(self.visited_urls)} pages explorées, "
                        f"{len(self.found_urls)} liens internes en attente, "
                        f"{len(self.external_urls)} liens externes en attente")
        
        # Fermer toutes les connexions
        for scraper in self.connection_pool:
            try:
                scraper.close()
            except:
                pass
        
        return self.data_by_page

def detect_data_structure(scraper):
    """Détecte automatiquement la structure des données sur la page"""
    page_source = scraper.driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Détection des éléments répétitifs
    potential_containers = {}
    for tag in soup.find_all():
        # Chercher des éléments qui se répètent avec des classes similaires
        if tag.get('class'):
            class_key = ' '.join(tag.get('class'))
            if class_key in potential_containers:
                potential_containers[class_key] += 1
            else:
                potential_containers[class_key] = 1
    
    # Trouver les conteneurs principaux (ceux qui se répètent le plus)
    sorted_containers = sorted(potential_containers.items(), key=lambda x: x[1], reverse=True)
    main_containers = [container for container, count in sorted_containers[:3] if count > 1]
    
    data_structures = []
    for container in main_containers:
        structure = analyze_container(soup, container)
        if structure['fields']:  # Ne garder que les structures avec des champs détectés
            data_structures.append(structure)
    
    return data_structures

def analyze_container(soup, container_class):
    """Analyse détaillée d'un conteneur"""
    structure = {
        'container': f".{container_class.replace(' ', '.')}",
        'fields': {}
    }
    
    first_item = soup.find(class_=container_class.split())
    if not first_item:
        return structure
    
    # Détection améliorée des champs
    field_detectors = [
        ('title', detect_title_field),
        ('price', detect_price_field),
        ('image', detect_image_field),
        ('link', detect_link_field),
        ('description', detect_description_field),
        ('date', detect_date_field),
        ('email', detect_email_field),
        ('phone', detect_phone_field),
        ('address', detect_address_field)
    ]
    
    for field_name, detector in field_detectors:
        field_data = detector(first_item)
        if field_data:
            structure['fields'][field_name] = field_data
    
    return structure

def detect_title_field(element):
    """Détecte les champs de titre"""
    title_tags = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
    for tag in title_tags:
        if tag.text.strip():
            return {'selector': get_unique_selector(tag)}
    return None

def detect_price_field(element):
    """Détecte les champs de prix"""
    price_pattern = re.compile(r'\d+[,\.]\d{2}|\d+\s*[€$£¥]|\$\s*\d+')
    price_candidates = element.find_all(string=price_pattern)
    for candidate in price_candidates:
        return {'selector': get_unique_selector(candidate.parent)}
    return None

def detect_image_field(element):
    """Détecte les champs d'image"""
    images = element.find_all('img')
    for img in images:
        if img.get('src'):
            return {
                'selector': get_unique_selector(img),
                'attribute': 'src'
            }
    return None

def detect_link_field(element):
    """Détecte les champs de lien"""
    links = element.find_all('a')
    for link in links:
        if link.get('href'):
            return {
                'selector': get_unique_selector(link),
                'attribute': 'href'
            }
    return None

def detect_description_field(element):
    """Détecte les champs de description"""
    desc_pattern = re.compile(r'desc|description|details|info|content|text', re.I)
    candidates = element.find_all(['p', 'div'], class_=desc_pattern)
    for candidate in candidates:
        if len(candidate.text.strip()) > 50:  # Description minimale
            return {'selector': get_unique_selector(candidate)}
    return None

def detect_date_field(element):
    """Détecte les champs de date"""
    date_pattern = re.compile(r'\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}')
    date_candidates = element.find_all(string=date_pattern)
    for candidate in date_candidates:
        return {'selector': get_unique_selector(candidate.parent)}
    return None

def detect_email_field(element):
    """Détecte les champs d'email"""
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    email_candidates = element.find_all(string=email_pattern)
    for candidate in email_candidates:
        return {'selector': get_unique_selector(candidate.parent)}
    return None

def detect_phone_field(element):
    """Détecte les champs de téléphone"""
    phone_pattern = re.compile(r'\+?\d{2,}[\s.-]?\d{2,}[\s.-]?\d{2,}')
    phone_candidates = element.find_all(string=phone_pattern)
    for candidate in phone_candidates:
        return {'selector': get_unique_selector(candidate.parent)}
    return None

def detect_address_field(element):
    """Détecte les champs d'adresse"""
    address_pattern = re.compile(r'\d+\s+rue|\d+\s+avenue|\d+\s+boulevard|BP\s+\d+', re.I)
    address_candidates = element.find_all(string=address_pattern)
    for candidate in address_candidates:
        return {'selector': get_unique_selector(candidate.parent)}
    return None

def get_unique_selector(element):
    """Génère un sélecteur CSS unique pour un élément"""
    if element.get('id'):
        return f"#{element.get('id')}"
    elif element.get('class'):
        return f".{'.'.join(element.get('class'))}"
    else:
        return element.name

def scrape_with_structure(scraper, url, structures):
    """Scrape les données selon les structures détectées"""
    if not isinstance(structures, list):
        structures = [structures]
    
    all_items = []
    
    for structure in structures:
        if scraper.navigate_to(url):
            time.sleep(3)  # Attendre le chargement
            
            try:
                containers = scraper.extract_data(structure['container'], multiple=True, as_elements=True)
                print(f"Détection de {len(containers)} éléments pour la structure {structure['container']}")
                
                for container in containers:
                    item = {
                        'source_url': url,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    for field, config in structure['fields'].items():
                        if 'attribute' in config:
                            value = scraper.extract_data_from_element(
                                container,
                                config['selector'],
                                attribute=config['attribute']
                            )
                        else:
                            value = scraper.extract_data_from_element(
                                container,
                                config['selector']
                            )
                        item[field] = value
                    
                    all_items.append(item)
            except Exception as e:
                print(f"Erreur lors de l'extraction avec la structure {structure['container']}: {str(e)}")
                continue
    
    return all_items

def main():
    # URL à scraper
    url = "https://exemple.com/"
    
    # Créer le mapper de site avec exploration externe activée
    mapper = SiteMapper(url, explore_external=True)
    
    try:
        print("Démarrage de l'exploration du site...")
        data = mapper.explore_site(
            max_pages=50,     # Limite raisonnable pour commencer
            max_depth=2,      # Profondeur de 2 niveaux
            max_workers=5     # 5 workers parallèles
        )
        
        # Sauvegarder les résultats
        output_file = f"data_{urlparse(url).netloc.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'base_url': url,
                    'total_pages': len(data),
                    'total_internal_pages': len([p for p in data.values() if urlparse(p['url']).netloc == urlparse(url).netloc]),
                    'total_external_pages': len([p for p in data.values() if urlparse(p['url']).netloc != urlparse(url).netloc]),
                    'timestamp': datetime.now().isoformat()
                },
                'pages': data
            }, f, ensure_ascii=False, indent=4)
        
        print(f"\nExploration terminée. Données sauvegardées dans {output_file}")
        print(f"Nombre total de pages explorées: {len(mapper.visited_urls)}")
        print(f"Pages internes: {len([p for p in data.values() if urlparse(p['url']).netloc == urlparse(url).netloc])}")
        print(f"Pages externes: {len([p for p in data.values() if urlparse(p['url']).netloc != urlparse(url).netloc])}")
        
    except Exception as e:
        print(f"Une erreur est survenue: {str(e)}")
    
    finally:
        mapper.scraper.close()

if __name__ == "__main__":
    main()