from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import time
import json
import logging
import os
from datetime import datetime

class WebScraper:
    def __init__(self, headless=True):
        self.setup_logging()
        self.setup_driver(headless)
        
    def setup_logging(self):
        """Configure le système de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self, headless):
        """Configure le driver Selenium"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        
        # Configuration des options pour éviter la détection
        chrome_options.add_argument(f'user-agent={UserAgent().random}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("Driver Chrome initialisé avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation du driver: {str(e)}")
            raise

    def navigate_to(self, url):
        """Navigate vers une URL avec gestion des erreurs"""
        try:
            self.driver.get(url)
            self.logger.info(f"Navigation réussie vers {url}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la navigation vers {url}: {str(e)}")
            return False

    def wait_for_element(self, by, value, timeout=10):
        """Attend qu'un élément soit présent sur la page"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            self.logger.error(f"Timeout en attendant l'élément {value}: {str(e)}")
            return None

    def extract_data(self, selector, multiple=False, attribute=None, as_elements=False):
        """Extrait les données selon un sélecteur CSS
        
        Args:
            selector (str): Sélecteur CSS
            multiple (bool): Si True, retourne une liste de résultats
            attribute (str): Si spécifié, extrait la valeur de cet attribut au lieu du texte
            as_elements (bool): Si True, retourne les éléments BeautifulSoup au lieu du texte
        """
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            if multiple:
                elements = soup.select(selector)
                if as_elements:
                    return elements
                if attribute:
                    return [elem.get(attribute, '') for elem in elements]
                return [elem.text.strip() for elem in elements]
            else:
                element = soup.select_one(selector)
                if as_elements:
                    return [element] if element else []
                if element:
                    if attribute:
                        return element.get(attribute, '')
                    return element.text.strip()
                return None
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des données: {str(e)}")
            return [] if multiple or as_elements else None

    def extract_data_from_element(self, container, selector, attribute=None):
        """Extrait les données d'un élément spécifique"""
        try:
            if isinstance(container, str):
                container = BeautifulSoup(container, 'html.parser')
            
            element = container.select_one(selector)
            if element:
                if attribute:
                    return element.get(attribute, '')
                return element.text.strip()
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des données de l'élément: {str(e)}")
            return None

    def get_page_source(self):
        """Retourne le code source de la page actuelle"""
        return self.driver.page_source

    def execute_js(self, script):
        """Exécute du code JavaScript sur la page"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution du JavaScript: {str(e)}")
            return None

    def scroll_to_bottom(self):
        """Fait défiler jusqu'au bas de la page pour charger le contenu dynamique"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            self.logger.error(f"Erreur lors du défilement: {str(e)}")

    def click_show_more(self, selector):
        """Clique sur les boutons 'Voir plus' pour charger plus de contenu"""
        try:
            while True:
                show_more = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if not show_more:
                    break
                show_more[0].click()
                time.sleep(2)
        except Exception as e:
            self.logger.error(f"Erreur lors du clic sur 'Voir plus': {str(e)}")

    def expand_all_elements(self):
        """Tente d'expandre tous les éléments pliables de la page"""
        expand_selectors = [
            '.show-more',
            '.load-more',
            '.expand',
            '[aria-expanded="false"]',
            '.collapsed',
            '.toggle'
        ]
        
        for selector in expand_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        element.click()
                        time.sleep(0.5)
                    except:
                        continue
            except:
                continue

    def wait_for_dynamic_content(self, timeout=10):
        """Attend que le contenu dynamique soit chargé"""
        try:
            # Attendre que les requêtes AJAX soient terminées
            self.driver.execute_script("""
                window.ajaxComplete = false;
                var oldXHR = window.XMLHttpRequest;
                function newXHR() {
                    var realXHR = new oldXHR();
                    realXHR.addEventListener("readystatechange", function() {
                        if(realXHR.readyState == 4){
                            window.ajaxComplete = true;
                        }
                    }, false);
                    return realXHR;
                }
                window.XMLHttpRequest = newXHR;
            """)
            
            # Attendre jusqu'à ce que les requêtes soient terminées
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.driver.execute_script("return window.ajaxComplete;"):
                    break
                time.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'attente du contenu dynamique: {str(e)}")

    def get_hidden_elements(self):
        """Récupère les éléments cachés de la page"""
        try:
            hidden_elements = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.display === 'none' || 
                           style.visibility === 'hidden' || 
                           style.opacity === '0' ||
                           el.hasAttribute('hidden');
                });
            """)
            return hidden_elements
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des éléments cachés: {str(e)}")
            return []

    def reveal_hidden_elements(self):
        """Rend visible les éléments cachés"""
        try:
            self.driver.execute_script("""
                Array.from(document.querySelectorAll('*')).forEach(el => {
                    if (window.getComputedStyle(el).display === 'none') {
                        el.style.display = 'block';
                    }
                    if (window.getComputedStyle(el).visibility === 'hidden') {
                        el.style.visibility = 'visible';
                    }
                    if (window.getComputedStyle(el).opacity === '0') {
                        el.style.opacity = '1';
                    }
                    if (el.hasAttribute('hidden')) {
                        el.removeAttribute('hidden');
                    }
                });
            """)
        except Exception as e:
            self.logger.error(f"Erreur lors de la révélation des éléments cachés: {str(e)}")

    def save_to_json(self, data, filename):
        """Sauvegarde les données au format JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Données sauvegardées dans {filename}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des données: {str(e)}")

    def close(self):
        """Ferme le navigateur"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Session de navigation fermée") 