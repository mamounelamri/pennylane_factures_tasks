#!/usr/bin/env python3
"""
Script de configuration automatique pour l'intégration Pennylane - Google Sheets
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Crée le fichier .env avec les variables nécessaires"""
    
    print("=== Configuration du fichier .env ===\n")
    
    # Vérifier si le fichier existe déjà
    if os.path.exists('.env'):
        response = input("Le fichier .env existe déjà. Voulez-vous le remplacer ? (o/n): ")
        if response.lower() != 'o':
            print("Configuration annulée.")
            return
    
    # Demander les informations
    print("Veuillez fournir les informations suivantes :\n")
    
    pennylane_key = input("Clé API Pennylane: ").strip()
    if not pennylane_key:
        print("❌ Clé API Pennylane requise")
        return
    
    credentials_file = input("Fichier credentials Google (credentials.json): ").strip()
    if not credentials_file:
        credentials_file = "credentials.json"
    
    spreadsheet_name = input("Nom du Google Sheet: ").strip()
    if not spreadsheet_name:
        print("❌ Nom du Google Sheet requis")
        return
    
    # Créer le fichier .env
    env_content = f"""# Configuration Pennylane
PENNYLANE_API_KEY={pennylane_key}

# Configuration Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE={credentials_file}
SPREADSHEET_NAME={spreadsheet_name}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Fichier .env créé avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env: {e}")
        return

def check_dependencies():
    """Vérifie et installe les dépendances"""
    
    print("\n=== Vérification des dépendances ===\n")
    
    try:
        import requests
        import google.auth
        import schedule
        import dotenv
        print("✅ Toutes les dépendances sont installées")
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("Installation des dépendances...")
        
        try:
            os.system(f"{sys.executable} -m pip install -r requirements.txt")
            print("✅ Dépendances installées")
        except Exception as e:
            print(f"❌ Erreur lors de l'installation: {e}")
            return False
    
    return True

def check_files():
    """Vérifie la présence des fichiers nécessaires"""
    
    print("\n=== Vérification des fichiers ===\n")
    
    # Vérifier le fichier .env
    if not os.path.exists('.env'):
        print("❌ Fichier .env manquant")
        return False
    else:
        print("✅ Fichier .env présent")
    
    # Vérifier le fichier credentials
    credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    if not os.path.exists(credentials_file):
        print(f"❌ Fichier {credentials_file} manquant")
        print("   Téléchargez le fichier credentials.json depuis Google Cloud Console")
        return False
    else:
        print(f"✅ Fichier {credentials_file} présent")
    
    return True

def run_tests():
    """Lance les tests de configuration"""
    
    print("\n=== Tests de configuration ===\n")
    
    # Test Pennylane
    print("Test de connexion Pennylane...")
    try:
        from pennylane_client import PennylaneClient
        client = PennylaneClient()
        invoices = client.get_invoices(limit=1)
        if invoices is not None:
            print("✅ Connexion Pennylane réussie")
        else:
            print("⚠️  Aucune facture trouvée (vérifiez votre clé API)")
    except Exception as e:
        print(f"❌ Erreur de connexion Pennylane: {e}")
        return False
    
    # Test Google Sheets
    print("Test de connexion Google Sheets...")
    try:
        from google_sheets_client import GoogleSheetsClient
        sheets_client = GoogleSheetsClient()
        sheets_client.get_spreadsheet_info()
        print("✅ Connexion Google Sheets réussie")
    except Exception as e:
        print(f"❌ Erreur de connexion Google Sheets: {e}")
        return False
    
    return True

def main():
    """Fonction principale"""
    
    print("=== Configuration de l'intégration Pennylane - Google Sheets ===\n")
    
    # Étape 1: Créer le fichier .env
    create_env_file()
    
    # Étape 2: Vérifier les dépendances
    if not check_dependencies():
        print("\n❌ Configuration échouée - Dépendances manquantes")
        return
    
    # Étape 3: Vérifier les fichiers
    if not check_files():
        print("\n❌ Configuration échouée - Fichiers manquants")
        return
    
    # Étape 4: Tests
    if not run_tests():
        print("\n❌ Configuration échouée - Tests échoués")
        return
    
    print("\n🎉 Configuration terminée avec succès !")
    print("\nVous pouvez maintenant utiliser l'intégration :")
    print("  python main.py          # Lancer l'intégration")
    print("  python test_pennylane.py # Tester les endpoints Pennylane")

if __name__ == "__main__":
    main() 