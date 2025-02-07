import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from main import SiteMapper
from urllib.parse import urlparse
import queue
import json
from datetime import datetime

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper")
        self.root.geometry("800x600")
        
        # Queue pour la communication entre threads
        self.log_queue = queue.Queue()
        self.data_queue = queue.Queue()
        
        self.setup_gui()
        self.update_logs()
        self.update_stats()
        
    def setup_gui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Sauvegarder la configuration", command=self.save_config)
        file_menu.add_command(label="Charger la configuration", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Nettoyer le cache", command=self.clear_cache)
        tools_menu.add_command(label="Voir les données extraites", command=self.show_data)
        
        # URL Input avec historique
        url_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        url_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=5)
        self.url_var = tk.StringVar(value="https://egycards.com/")
        self.url_combo = ttk.Combobox(url_frame, textvariable=self.url_var, width=50)
        self.url_combo['values'] = self.load_url_history()
        self.url_combo.grid(row=0, column=1, padx=5)
        
        # Options avancées
        options_frame = ttk.LabelFrame(main_frame, text="Options avancées", padding="5")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Page 1: Options de base
        self.options_notebook = ttk.Notebook(options_frame)
        self.options_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        basic_frame = ttk.Frame(self.options_notebook)
        self.options_notebook.add(basic_frame, text="Base")
        
        ttk.Label(basic_frame, text="Max Pages:").grid(row=0, column=0, padx=5)
        self.max_pages_var = tk.StringVar(value="50")
        ttk.Entry(basic_frame, textvariable=self.max_pages_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(basic_frame, text="Max Depth:").grid(row=0, column=2, padx=5)
        self.max_depth_var = tk.StringVar(value="2")
        ttk.Entry(basic_frame, textvariable=self.max_depth_var, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(basic_frame, text="Workers:").grid(row=0, column=4, padx=5)
        self.workers_var = tk.StringVar(value="3")  # Réduit à 3 workers
        ttk.Entry(basic_frame, textvariable=self.workers_var, width=10).grid(row=0, column=5, padx=5)
        
        # Page 2: Options avancées
        advanced_frame = ttk.Frame(self.options_notebook)
        self.options_notebook.add(advanced_frame, text="Avancé")
        
        self.explore_external_var = tk.BooleanVar(value=False)  # Désactivé par défaut
        ttk.Checkbutton(advanced_frame, text="Explorer liens externes", 
                       variable=self.explore_external_var).grid(row=0, column=0, padx=5)
        
        self.respect_robots_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Respecter robots.txt", 
                       variable=self.respect_robots_var).grid(row=0, column=1, padx=5)
        
        self.delay_var = tk.StringVar(value="2")
        ttk.Label(advanced_frame, text="Délai entre requêtes (s):").grid(row=0, column=2, padx=5)
        ttk.Entry(advanced_frame, textvariable=self.delay_var, width=5).grid(row=0, column=3, padx=5)
        
        # Boutons avec icônes
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        self.start_button = ttk.Button(buttons_frame, text="▶ Démarrer", command=self.start_scraping)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(buttons_frame, text="⏸ Pause", command=self.pause_scraping, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="⏹ Arrêter", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        # Statistiques avec graphique
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding="5")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.stats_text = {
            'pages_visited': tk.StringVar(value="Pages visitées: 0"),
            'internal_links': tk.StringVar(value="Liens internes: 0"),
            'external_links': tk.StringVar(value="Liens externes: 0"),
            'emails_found': tk.StringVar(value="Emails trouvés: 0"),
            'phones_found': tk.StringVar(value="Téléphones trouvés: 0"),
            'errors': tk.StringVar(value="Erreurs: 0")
        }
        
        for i, (key, var) in enumerate(self.stats_text.items()):
            ttk.Label(stats_frame, textvariable=var).grid(row=i//3, column=i%3, padx=10, pady=2)
        
        # Logs avec filtres
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="5")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.log_level_var = tk.StringVar(value="INFO")
        ttk.Label(log_toolbar, text="Niveau:").pack(side=tk.LEFT, padx=5)
        ttk.OptionMenu(log_toolbar, self.log_level_var, "INFO", "DEBUG", "INFO", "WARNING", "ERROR").pack(side=tk.LEFT)
        
        ttk.Button(log_toolbar, text="Effacer", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.RIGHT, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Progress Bar avec pourcentage
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=1, padx=5)
        
        # Configuration de la grille
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
    def save_config(self):
        """Sauvegarde la configuration actuelle"""
        config = {
            'url': self.url_var.get(),
            'max_pages': self.max_pages_var.get(),
            'max_depth': self.max_depth_var.get(),
            'workers': self.workers_var.get(),
            'explore_external': self.explore_external_var.get(),
            'respect_robots': self.respect_robots_var.get(),
            'delay': self.delay_var.get()
        }
        with open('scraper_config.json', 'w') as f:
            json.dump(config, f)
        self.log("Configuration sauvegardée")
    
    def load_config(self):
        """Charge une configuration sauvegardée"""
        try:
            with open('scraper_config.json', 'r') as f:
                config = json.load(f)
            self.url_var.set(config.get('url', ''))
            self.max_pages_var.set(config.get('max_pages', '50'))
            self.max_depth_var.set(config.get('max_depth', '2'))
            self.workers_var.set(config.get('workers', '3'))
            self.explore_external_var.set(config.get('explore_external', False))
            self.respect_robots_var.set(config.get('respect_robots', True))
            self.delay_var.set(config.get('delay', '2'))
            self.log("Configuration chargée")
        except:
            self.log("Erreur lors du chargement de la configuration")
    
    def load_url_history(self):
        """Charge l'historique des URLs"""
        try:
            with open('url_history.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_url_history(self):
        """Sauvegarde l'URL dans l'historique"""
        urls = self.load_url_history()
        current_url = self.url_var.get()
        if current_url not in urls:
            urls.insert(0, current_url)
            urls = urls[:10]  # Garder les 10 dernières URLs
            with open('url_history.json', 'w') as f:
                json.dump(urls, f)
            self.url_combo['values'] = urls
    
    def clear_cache(self):
        """Nettoie le cache du scraper"""
        if hasattr(self, 'mapper'):
            self.mapper.scraper.clear_cache()
        self.log("Cache nettoyé")
    
    def show_data(self):
        """Affiche les données extraites dans une nouvelle fenêtre"""
        if not hasattr(self, 'data_window'):
            self.data_window = tk.Toplevel(self.root)
            self.data_window.title("Données extraites")
            self.data_window.geometry("600x400")
            
            text = scrolledtext.ScrolledText(self.data_window)
            text.pack(fill=tk.BOTH, expand=True)
            
            if hasattr(self, 'mapper') and hasattr(self.mapper, 'data_by_page'):
                text.insert(tk.END, json.dumps(self.mapper.data_by_page, indent=2))
            else:
                text.insert(tk.END, "Aucune donnée disponible")
    
    def pause_scraping(self):
        """Met en pause le scraping"""
        if hasattr(self, 'mapper'):
            self.mapper.pause = not getattr(self.mapper, 'pause', False)
            self.pause_button.config(text="▶ Reprendre" if self.mapper.pause else "⏸ Pause")
            self.log("Scraping en pause" if self.mapper.pause else "Scraping repris")
    
    def log(self, message):
        self.log_queue.put(message)
    
    def update_logs(self):
        while True:
            try:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
            except queue.Empty:
                break
        self.root.after(100, self.update_logs)
    
    def update_stats(self):
        while True:
            try:
                stats = self.data_queue.get_nowait()
                for key, value in stats.items():
                    if key in self.stats_text:
                        self.stats_text[key].set(f"{key.replace('_', ' ').title()}: {value}")
                self.progress_var.set(min(100, stats.get('progress', 0)))
            except queue.Empty:
                break
        self.root.after(100, self.update_stats)
    
    def start_scraping(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.scraping_active = True
        
        # Démarrer le scraping dans un thread séparé
        threading.Thread(target=self.run_scraper, daemon=True).start()
    
    def stop_scraping(self):
        self.scraping_active = False
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
    
    def run_scraper(self):
        try:
            url = self.url_var.get()
            max_pages = int(self.max_pages_var.get())
            max_depth = int(self.max_depth_var.get())
            max_workers = int(self.workers_var.get())
            explore_external = self.explore_external_var.get()
            
            self.log(f"Démarrage du scraping de {url}")
            
            mapper = SiteMapper(url, explore_external=explore_external)
            mapper.log_callback = self.log
            mapper.stats_callback = lambda stats: self.data_queue.put(stats)
            
            data = mapper.explore_site(
                max_pages=max_pages,
                max_depth=max_depth,
                max_workers=max_workers
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
            
            self.log(f"\nScraping terminé. Données sauvegardées dans {output_file}")
            
        except Exception as e:
            self.log(f"Erreur: {str(e)}")
        
        finally:
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 