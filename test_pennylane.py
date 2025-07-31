#!/usr/bin/env python3
"""
Script de test pour explorer les endpoints Pennylane v2
Permet de comprendre la structure des données retournées par l'API
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from pennylane_client import PennylaneClient

load_dotenv()

def is_date_today(date_str: str) -> bool:
    """Vérifie si une date correspond à aujourd'hui"""
    if not date_str:
        return False
    try:
        # Parser la date ISO
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        today = datetime.now().date()
        return date_obj.date() == today
    except:
        return False

def test_pennylane_endpoints():
    """Test et explore les endpoints Pennylane v2"""
    
    print("=== Test des endpoints Pennylane v2 ===\n")
    
    try:
        client = PennylaneClient()
        
        # Test 1: Récupération des factures
        print("1. Test des factures:")
        invoices = client.get_invoices(limit=10)
        
        if invoices:
            print(f"   ✓ {len(invoices)} factures récupérées")
            
            # Afficher la structure de la première facture
            sample_invoice = invoices[0]
            print(f"   Structure d'une facture:")
            for key, value in sample_invoice.items():
                if isinstance(value, dict):
                    print(f"     {key}: {type(value).__name__} = {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"     {key}: {type(value).__name__} = {len(value)} éléments")
                else:
                    print(f"     {key}: {type(value).__name__} = {value}")
            
            # Afficher les statuts disponibles
            statuses = set(inv.get('status') for inv in invoices)
            print(f"   Statuts trouvés: {statuses}")
            
            # Analyser les types de factures
            credit_notes = [inv for inv in invoices if inv.get('status') == 'credit_note']
            regular_invoices = [inv for inv in invoices if inv.get('status') != 'credit_note']
            paid_invoices = [inv for inv in invoices if inv.get('paid')]
            
            print(f"   Répartition:")
            print(f"     - Avoirs: {len(credit_notes)}")
            print(f"     - Factures régulières: {len(regular_invoices)}")
            print(f"     - Factures payées: {len(paid_invoices)}")
            
            # Test du filtrage par date
            print(f"\n2. Test du filtrage par date (updated_at = aujourd'hui):")
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"   Date aujourd'hui: {today}")
            
            paid_today = []
            partially_paid_today = []
            
            for invoice in regular_invoices:
                updated_at = invoice.get('updated_at')
                if updated_at:
                    if invoice.get('paid') and is_date_today(updated_at):
                        paid_today.append(invoice)
                    elif (invoice.get('status') == 'partially_cancelled' and 
                          is_date_today(updated_at)):
                        partially_paid_today.append(invoice)
            
            print(f"   - Factures payées aujourd'hui: {len(paid_today)}")
            print(f"   - Factures partiellement payées aujourd'hui: {len(partially_paid_today)}")
            
            # Afficher les détails des factures payées aujourd'hui
            if paid_today:
                print(f"\n   Détails des factures payées aujourd'hui:")
                for i, invoice in enumerate(paid_today, 1):
                    print(f"     {i}. Facture {invoice.get('invoice_number')}")
                    print(f"        - Montant: {invoice.get('currency_amount')} {invoice.get('currency')}")
                    print(f"        - Date facture: {invoice.get('date')}")
                    print(f"        - Date mise à jour: {invoice.get('updated_at')}")
                    print(f"        - Statut: {invoice.get('status')}")
                    print(f"        - Payée: {invoice.get('paid')}")
            
            # Vérifier les informations client incluses
            if 'customer' in sample_invoice:
                customer = sample_invoice['customer']
                print(f"\n   Informations client incluses:")
                for key, value in customer.items():
                    print(f"     {key}: {type(value).__name__} = {value}")
                
                # Tenter de récupérer les détails du client
                if 'url' in customer:
                    print(f"\n   Récupération des détails du client...")
                    customer_details = client.get_customer_details(customer['url'])
                    if customer_details:
                        print(f"   Détails du client:")
                        for key, value in customer_details.items():
                            print(f"     {key}: {type(value).__name__} = {value}")
                    else:
                        print("   ❌ Impossible de récupérer les détails du client")
                
                # Vérifier si les paiements sont inclus
                if 'payments' in sample_invoice:
                    payments = sample_invoice['payments']
                    print(f"\n   Informations de paiement incluses:")
                    if isinstance(payments, dict) and 'url' in payments:
                        print(f"   Récupération des détails des paiements...")
                        payment_details = client.get_payment_details(payments['url'])
                        if payment_details:
                            print(f"   Détails des paiements:")
                            for key, value in payment_details.items():
                                print(f"     {key}: {type(value).__name__} = {value}")
                        else:
                            print("   ❌ Impossible de récupérer les détails des paiements")
            
        else:
            print("   ✗ Aucune facture trouvée")
        
        # Test 3: Test avec différents statuts
        print("\n3. Test avec différents statuts:")
        # Test simple sans filtre d'abord
        print("   - Test sans filtre:")
        all_invoices = client.get_invoices(limit=10)
        paid_count = sum(1 for inv in all_invoices if inv.get('paid'))
        unpaid_count = sum(1 for inv in all_invoices if not inv.get('paid'))
        credit_note_count = sum(1 for inv in all_invoices if inv.get('status') == 'credit_note')
        print(f"     Total: {len(all_invoices)}, Payées: {paid_count}, Non payées: {unpaid_count}, Avoirs: {credit_note_count}")
        
        # Test 4: Sauvegarde d'exemples
        print("\n4. Sauvegarde d'exemples:")
        examples = {
            'invoices': invoices[:2] if invoices else [],
            'paid_invoices': [inv for inv in invoices if inv.get('paid')][:2],
            'credit_notes': [inv for inv in invoices if inv.get('status') == 'credit_note'][:2],
            'paid_today': paid_today[:2] if 'paid_today' in locals() else []
        }
        
        with open('pennylane_v2_examples.json', 'w', encoding='utf-8') as f:
            json.dump(examples, f, indent=2, ensure_ascii=False, default=str)
        
        print("   ✓ Exemples sauvegardés dans pennylane_v2_examples.json")
        
        print("\n=== Test terminé ===")
        
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        print("Vérifiez que PENNYLANE_API_KEY est définie dans le fichier .env")

if __name__ == "__main__":
    test_pennylane_endpoints() 