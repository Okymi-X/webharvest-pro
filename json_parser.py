import json
from datetime import datetime
from urllib.parse import urlparse
import re

class JsonParser:
    """Classe pour parser et valider les données JSON en différents types"""
    
    def __init__(self):
        self.type_converters = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'date': self._parse_date,
            'email': self._validate_email,
            'url': self._validate_url,
            'list': list,
            'dict': dict
        }

    def parse_json(self, json_data, schema=None):
        """
        Parse les données JSON selon un schéma optionnel
        :param json_data: Données JSON à parser (str ou dict)
        :param schema: Schéma de validation (optionnel)
        :return: Données parsées et validées
        """
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON invalide: {str(e)}")
        else:
            data = json_data

        if schema:
            return self._validate_and_convert(data, schema)
        return data

    def _validate_and_convert(self, data, schema):
        """
        Valide et convertit les données selon le schéma
        :param data: Données à valider
        :param schema: Schéma de validation
        :return: Données validées et converties
        """
        if isinstance(schema, dict):
            if 'type' not in schema:
                return {k: self._validate_and_convert(v, schema.get(k, {})) for k, v in data.items()}
            
            required_type = schema['type']
            converter = self.type_converters.get(required_type)
            
            if not converter:
                raise ValueError(f"Type non supporté: {required_type}")
            
            try:
                return converter(data)
            except Exception as e:
                raise ValueError(f"Erreur de conversion en {required_type}: {str(e)}")
        
        return data

    def _parse_date(self, value):
        """Parse une chaîne en date"""
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Format de date invalide: {value}")

    def _validate_email(self, value):
        """Valide et retourne une adresse email"""
        if not isinstance(value, str):
            raise ValueError("L'email doit être une chaîne de caractères")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError(f"Email invalide: {value}")
        return value

    def _validate_url(self, value):
        """Valide et retourne une URL"""
        if not isinstance(value, str):
            raise ValueError("L'URL doit être une chaîne de caractères")
        
        try:
            result = urlparse(value)
            if all([result.scheme, result.netloc]):
                return value
            raise ValueError()
        except ValueError:
            raise ValueError(f"URL invalide: {value}")

# Exemple d'utilisation
if __name__ == "__main__":
    # Création d'un parseur
    parser = JsonParser()
    
    # Exemple 1: JSON simple
    json_simple = '{"nom": "Jean", "age": 30}'
    resultat1 = parser.parse_json(json_simple)
    print("Exemple 1 - JSON simple:", resultat1)
    
    # Exemple 2: JSON avec schéma de validation
    schema = {
        "nom": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "email"},
        "date_inscription": {"type": "date"},
        "site_web": {"type": "url"}
    }
    
    json_complet = '''
    {
        "nom": "Jean Dupont",
        "age": 30,
        "email": "jean@example.com",
        "date_inscription": "2025-02-25",
        "site_web": "https://example.com"
    }
    '''
    
    try:
        resultat2 = parser.parse_json(json_complet, schema)
        print("\nExemple 2 - JSON avec validation:")
        for key, value in resultat2.items():
            print(f"{key}: {value} ({type(value).__name__})")
    except ValueError as e:
        print(f"Erreur de validation: {e}")
