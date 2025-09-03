#!/usr/bin/env python3
"""
Script de test rapide pour l'intégration Armado
Ce script teste la connexion et les fonctions principales sans modifier de données réelles
"""

import os
import sys
from datetime import datetime

def test_imports():
    """Test des imports"""
    print("=== Test des imports ===")
    try:
        from armado_client import ArmadoClient
        from sync_payments import sync_armado_after_tempo, get_available_payment_modes, test_armado_connection
        print("✓ Tous les imports réussis")
        return True
    except ImportError as e:
        print(f"✗ Erreur d'import: {e}")
        return False

def test_environment():
    """Test des variables d'environnement"""
    print("\n=== Test des variables d'environnement ===")
    
    required_vars = ['ARMADO_API_KEY']
    optional_vars = ['ARMADO_BASE_URL', 'ARMADO_TIMEOUT']
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Variables manquantes: {missing_vars}")
        print("  Ajoutez-les à votre fichier .env")
        return False
    
    print("✓ Variables d'environnement requises présentes")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: (valeur par défaut)")
    
    return True

def test_client_initialization():
    """Test d'initialisation du client"""
    print("\n=== Test d'initialisation du client ===")
    try:
        from armado_client import ArmadoClient
        client = ArmadoClient()
        print(f"✓ Client initialisé")
        print(f"  Base URL: {client.base_url}")
        print(f"  Timeout: {client.timeout}")
        print(f"  Max retries: {client.max_retries}")
        return True
    except Exception as e:
        print(f"✗ Erreur d'initialisation: {e}")
        return False

def test_payment_modes():
    """Test des modes de paiement"""
    print("\n=== Test des modes de paiement ===")
    try:
        from sync_payments import get_available_payment_modes
        modes = get_available_payment_modes()
        print(f"✓ {len(modes)} modes de paiement disponibles:")
        for mode in sorted(modes):
            print(f"  - {mode}")
        return True
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

def test_connection():
    """Test de connexion à l'API Armado"""
    print("\n=== Test de connexion Armado ===")
    try:
        from sync_payments import test_armado_connection
        if test_armado_connection():
            print("✓ Connexion Armado réussie")
            return True
        else:
            print("✗ Problème de connexion Armado")
            print("  Vérifiez votre API key et la connectivité réseau")
            return False
    except Exception as e:
        print(f"✗ Erreur de connexion: {e}")
        return False

def test_sync_function():
    """Test de la fonction de synchronisation (avec données fictives)"""
    print("\n=== Test de la fonction de synchronisation ===")
    try:
        from sync_payments import sync_with_error_handling
        
        # Test avec des données fictives (va échouer mais on peut voir le comportement)
        result = sync_with_error_handling(
            invoice_reference="TEST_12345",
            payment_mode="virement",
            payment_date=datetime.now()
        )
        
        print(f"Résultat: success={result['success']}")
        if result['error']:
            print(f"Erreur (attendue): {result['error']}")
        
        # Vérifier que la structure de réponse est correcte
        required_keys = ['success', 'data', 'error']
        if all(key in result for key in required_keys):
            print("✓ Structure de réponse correcte")
            return True
        else:
            print("✗ Structure de réponse incorrecte")
            return False
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("=== Test rapide de l'intégration Armado ===\n")
    
    tests = [
        ("Imports", test_imports),
        ("Variables d'environnement", test_environment),
        ("Initialisation du client", test_client_initialization),
        ("Modes de paiement", test_payment_modes),
        ("Connexion Armado", test_connection),
        ("Fonction de synchronisation", test_sync_function)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "="*50)
    print("=== RÉSUMÉ DES TESTS ===")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'intégration est prête.")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
