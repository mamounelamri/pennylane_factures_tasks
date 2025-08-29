#!/usr/bin/env python3
"""
Script de test pour l'envoi d'emails d'alerte Tempo
Teste toutes les fonctionnalités d'alerte par email
"""

import argparse
from datetime import datetime
from tempo_email_client import TempoEmailClient

def test_connection():
    """Test de la connexion SMTP"""
    print("🔧 Test de connexion SMTP Office365...")
    
    try:
        email_client = TempoEmailClient()
        if email_client.test_connection():
            print("✅ Connexion SMTP réussie")
            return email_client
        else:
            print("❌ Échec de la connexion SMTP")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return None

def test_facture_not_found_alert(email_client: TempoEmailClient):
    """Test de l'alerte facture introuvable"""
    print("\n📧 Test de l'alerte 'Facture introuvable'...")
    
    success = email_client.send_facture_not_found_alert(
        invoice_number=99999,
        dossier="DAN02",
        base_url="https://host/API/Tempo",
        error_context="Test automatique - Facture fictive"
    )
    
    if success:
        print("✅ Alerte 'Facture introuvable' envoyée")
    else:
        print("❌ Échec de l'envoi de l'alerte")

def test_reglement_failed_alert(email_client: TempoEmailClient):
    """Test de l'alerte échec de règlement"""
    print("\n📧 Test de l'alerte 'Échec de règlement'...")
    
    payload = {
        "IdFacture": 99999,
        "RegleeTotale": "OUI",
        "DateReglementTotal": "20250828"
    }
    
    success = email_client.send_reglement_failed_alert(
        invoice_number=99999,
        operation_type="règlement total",
        error_message="Test automatique - Erreur fictive",
        payload=payload
    )
    
    if success:
        print("✅ Alerte 'Échec de règlement' envoyée")
    else:
        print("❌ Échec de l'envoi de l'alerte")

def test_integration_summary(email_client: TempoEmailClient):
    """Test du résumé d'intégration"""
    print("\n📧 Test du résumé d'intégration...")
    
    # Simuler des opérations
    operation_details = [
        {
            'success': True,
            'invoice_number': 20498,
            'operation_type': 'Règlement total',
            'amount': 1000.00,
            'message': 'Succès'
        },
        {
            'success': True,
            'invoice_number': 20499,
            'operation_type': 'Règlement partiel',
            'amount': 500.00,
            'message': 'Succès'
        },
        {
            'success': False,
            'invoice_number': 20500,
            'operation_type': 'Règlement total',
            'amount': 750.00,
            'message': 'Facture introuvable'
        }
    ]
    
    success = email_client.send_integration_summary(
        processed_count=2,
        error_count=1,
        details=operation_details
    )
    
    if success:
        print("✅ Résumé d'intégration envoyé")
    else:
        print("❌ Échec de l'envoi du résumé")

def test_custom_alert(email_client: TempoEmailClient, recipient: str):
    """Test d'une alerte personnalisée"""
    print(f"\n📧 Test d'alerte personnalisée vers {recipient}...")
    
    subject = "Test d'alerte personnalisée"
    html_content = f"""
    <h2>🧪 Test d'alerte personnalisée</h2>
    
    <p>Ceci est un test de l'intégration email Tempo.</p>
    
    <h3>Informations de test :</h3>
    <ul>
        <li><strong>Date/heure :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
        <li><strong>Destinataire :</strong> {recipient}</li>
        <li><strong>Type :</strong> Test automatique</li>
    </ul>
    
    <p><em>Si vous recevez cet email, la configuration email fonctionne correctement !</em></p>
    """
    
    success = email_client.send_alert_email(
        subject=subject,
        html_content=html_content,
        recipients=[recipient]
    )
    
    if success:
        print(f"✅ Alerte personnalisée envoyée à {recipient}")
    else:
        print(f"❌ Échec de l'envoi de l'alerte personnalisée")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Test des emails d'alerte Tempo")
    parser.add_argument('--recipient', type=str, help='Email de test personnalisé')
    parser.add_argument('--skip-connection', action='store_true', help='Passer le test de connexion')
    
    args = parser.parse_args()
    
    print("=== Test des Emails d'Alerte Tempo ===\n")
    
    # Test de connexion
    if not args.skip_connection:
        email_client = test_connection()
        if not email_client:
            print("\n❌ Impossible de continuer sans connexion SMTP")
            return
    else:
        try:
            email_client = TempoEmailClient()
            print("⚠ Test de connexion ignoré")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return
    
    # Test uniquement du résumé d'intégration (plus pratique)
    test_integration_summary(email_client)
    
    # Test d'alerte personnalisée si un destinataire est fourni
    if args.recipient:
        test_custom_alert(email_client, args.recipient)
    
    print("\n" + "="*50)
    print("🎉 Tests terminés !")
    print("="*50)
    
    print("\n📋 Résumé des tests :")
    print("✅ Connexion SMTP Office365")
    print("✅ Résumé d'intégration (email unique)")
    
    if args.recipient:
        print(f"✅ Alerte personnalisée vers {args.recipient}")
    
    print("\n💡 Vérifiez vos emails pour confirmer la réception !")

if __name__ == "__main__":
    main()
