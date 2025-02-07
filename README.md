# WebHarvest Pro 🌐

Solution professionnelle et éthique de web scraping avec interface graphique, développée en Python. Cet outil offre une extraction intelligente des données, une gestion optimisée des connexions et une interface utilisateur conviviale.

## ✨ Fonctionnalités

- 🖥️ **Interface Graphique Avancée**
  - Suivi en temps réel de la progression
  - Paramètres de scraping configurables
  - Gestion de l'historique des URLs
  - Tableau de bord statistique en direct
  - Filtrage des niveaux de logs

- 🔄 **Gestion Intelligente des Connexions**
  - Pool de connexions avec mise à l'échelle automatique
  - Mécanisme de réessai intelligent
  - Délais configurables entre les requêtes
  - Gestion automatique des sessions

- 🧠 **Détection Intelligente des Données**
  - Détection automatique de la structure
  - Extraction des emails et numéros de téléphone
  - Détection des liens de réseaux sociaux
  - Identification des données sensibles

- 🛡️ **Protection Intégrée**
  - Respect du fichier robots.txt
  - Mesures anti-détection de bot
  - Limitation du taux de requêtes
  - Rotation des User-Agents

- 💾 **Gestion des Données**
  - Export au format JSON
  - Sortie de données structurée
  - Sauvegarde de la progression
  - Persistance de la configuration

## 🚀 Pour Commencer

### Prérequis

- Python 3.8+
- Navigateur Chrome installé
- Windows/Linux/MacOS

### Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/votre-nom/webharvest-pro.git
cd webharvest-pro
```

2. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sous Windows : venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

### Utilisation

1. Lancez l'application graphique :
```bash
python gui.py
```

2. Entrez l'URL cible et configurez les paramètres :
   - Pages Max : Limite du nombre de pages à scraper
   - Profondeur Max : Définit la profondeur de suivi des liens
   - Workers : Nombre de connexions parallèles (recommandé : 3-5)

3. Options avancées :
   - Liens Externes : Activer/désactiver le suivi des liens externes
   - Robots.txt : Activer/désactiver le respect du robots.txt
   - Délai Requêtes : Définir le délai entre les requêtes

4. Cliquez sur "Démarrer" pour commencer le scraping

## 🛠️ Configuration

### Paramètres de Base
- **URL d'Entrée** : Saisissez l'URL du site cible
- **Pages Max** : Limitez le nombre total de pages
- **Profondeur Max** : Contrôlez la profondeur d'exploration
- **Workers** : Définissez les connexions parallèles

### Paramètres Avancés
- **Liens Externes** : Basculez le suivi des liens externes
- **Robots.txt** : Activez/désactivez la conformité
- **Délai Requêtes** : Configurez le délai inter-requêtes
- **Pool de Connexions** : Configurez la taille du pool

## 📊 Format des Données

Le scraper sauvegarde les données au format JSON avec la structure suivante :
```json
{
    "metadata": {
        "base_url": "https://exemple.com",
        "total_pages": 100,
        "timestamp": "2024-02-07T12:00:00"
    },
    "pages": {
        "page_id": {
            "url": "https://exemple.com/page",
            "titre": "Titre de la Page",
            "donnees": {...}
        }
    }
}
```

## 🔧 Optimisation des Performances

Pour des performances optimales :
- Réglez les workers entre 3 et 5 pour la plupart des sites
- Activez les délais entre requêtes (2-3 secondes recommandées)
- Utilisez le pool de connexions
- Activez le respect du robots.txt
- Surveillez les ressources système

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une Pull Request. Pour les changements majeurs, ouvrez d'abord une issue pour discuter des modifications souhaitées.

1. Forkez le Projet
2. Créez votre Branche de Fonctionnalité (`git checkout -b feature/NouvelleFonctionnalite`)
3. Committez vos Changements (`git commit -m 'Ajout de NouvelleFonctionnalite'`)
4. Poussez vers la Branche (`git push origin feature/NouvelleFonctionnalite`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## ⚠️ Avertissement

Cet outil est destiné uniquement à des fins éducatives. Veillez à toujours :
- Respecter le fichier robots.txt des sites
- Suivre les conditions d'utilisation des sites
- Implémenter des délais appropriés
- Utiliser de manière responsable et éthique

## 🙏 Remerciements

- Selenium WebDriver
- BeautifulSoup4
- Python Tkinter
- Et tous les autres contributeurs open source

## 📧 Contact

[@Okymi-X](https://github.com/Okymi-X)

[https://github.com/Okymi-X/webharvest-pro](https://github.com/Okymi-X/webharvest-pro)