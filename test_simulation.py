#!/usr/bin/env python3
"""
Script de simulation pour tester la création de tâches Google Sheets
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv

from google_sheets_client import GoogleSheetsClient

load_dotenv()

def create_simulation_data() -> List[Dict]:
    """Crée des données de simulation pour tester"""
    
    # Données de simulation
    simulation_invoices = [
        {
            'id': 'sim_001',
            'invoice_number': 'FACT-2025-001',
            'date': '2025-01-15',
            'currency_amount': '1250.00',
            'paid': True,
            'status': 'paid',
            'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'customer': {
                'id': '12345',
                'name': 'Entreprise Test 1'
            }
        },
        {
            'id': 'sim_002', 
            'invoice_number': 'FACT-2025-002',
            'date': '2025-01-20',
            'currency_amount': '850.50',
            'paid': True,
            'status': 'paid',
            'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'customer': {
                'id': '67890',
                'name': 'Entreprise Test 2'
            }
        },
        {
            'id': 'sim_003',
            'invoice_number': 'FACT-2025-003', 
            'date': '2025-01-25',
            'currency_amount': '2100.75',
            'paid': False,
            'status': 'partially_cancelled',
            'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'customer': {
                'id': '11111',
                'name': 'Entreprise Test 3'
            }
        },
        {
            'id': 'sim_004',
            'invoice_number': 'FACT-2025-004',
            'date': '2025-01-30', 
            'currency_amount': '750.25',
            'paid': True,
            'status': 'paid',
            'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'customer': {
                'id': '22222',
                'name': 'Entreprise Test 4'
            }
        },
        {
            'id': 'sim_005',
            'invoice_number': 'FACT-2025-005',
            'date': '2025-02-01',
            'currency_amount': '3200.00', 
            'paid': False,
            'status': 'partially_cancelled',
            'updated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'customer': {
                'id': '33333',
                'name': 'Entreprise Test 5'
            }
        }
    ]
    
    return simulation_invoices

def format_date(date_str: str) -> str:
    """Formate une date pour l'affichage"""
    if not date_str:
        return ""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_str

def format_amount(amount: str) -> str:
    """Formate un montant pour l'affichage"""
    if not amount:
        return ""
    try:
        amount_float = float(amount)
        return f"{amount_float:.2f} €"
    except:
        return amount

def create_task_from_simulation_invoice(invoice_data: Dict) -> Dict:
    """Crée une tâche à partir des données de simulation"""
    
    customer_data = invoice_data.get('customer', {})
    
    task_data = {
        'invoice_number': invoice_data.get('invoice_number', ''),
        'invoice_date': format_date(invoice_data.get('date')),
        'payment_amount': format_amount(invoice_data.get('currency_amount')),
        'client_name': customer_data.get('name', f"Client {customer_data.get('id', '')}"),
        'status': 'Payée' if invoice_data.get('paid') else 'Partiellement payée'
    }
    
    return task_data

def run_simulation():
    """Exécute la simulation complète"""
    
    print("=== SIMULATION - Test de création de tâches Google Sheets ===\n")
    
    try:
        # Initialiser le client Google Sheets
        print("1. Initialisation du client Google Sheets...")
        sheets_client = GoogleSheetsClient()
        sheets_client.setup_spreadsheet()
        print("✓ Client Google Sheets initialisé\n")
        
        # Créer les données de simulation
        print("2. Création des données de simulation...")
        simulation_invoices = create_simulation_data()
        print(f"✓ {len(simulation_invoices)} factures de simulation créées\n")
        
        # Afficher les données de simulation
        print("3. Données de simulation:")
        for i, invoice in enumerate(simulation_invoices, 1):
            print(f"   {i}. {invoice['invoice_number']} - {invoice['currency_amount']}€ - {invoice['status']}")
        print()
        
        # Traiter chaque facture de simulation
        print("4. Création des tâches dans Google Sheets...")
        processed_count = 0
        
        for invoice in simulation_invoices:
            # Créer la tâche
            task_data = create_task_from_simulation_invoice(invoice)
            
            # Ajouter au Google Sheet
            if sheets_client.create_task(task_data):
                processed_count += 1
                print(f"  ✓ Tâche créée pour {task_data['invoice_number']} ({task_data['payment_amount']})")
            else:
                print(f"  ✗ Erreur lors de la création de la tâche pour {invoice['invoice_number']}")
        
        print(f"\n✓ Simulation terminée: {processed_count} tâches créées avec succès")
        
        # Afficher l'URL du spreadsheet
        if sheets_client.spreadsheet_id:
            print(f"\n📊 Google Sheet: https://docs.google.com/spreadsheets/d/{sheets_client.spreadsheet_id}")
            print("   Vous pouvez vérifier les tâches créées dans le fichier.")
        
    except Exception as e:
        print(f"✗ Erreur lors de la simulation: {e}")
        print("Vérifiez votre configuration dans le fichier .env")

def test_single_task():
    """Test d'une seule tâche"""
    
    print("=== TEST - Création d'une seule tâche ===\n")
    
    try:
        # Initialiser le client
        sheets_client = GoogleSheetsClient()
        sheets_client.setup_spreadsheet()
        
        # Créer une tâche de test
        test_task = {
            'invoice_number': 'TEST-001',
            'invoice_date': '15/01/2025',
            'payment_amount': '1000.00 €',
            'status': 'Payée'
        }
        
        print("Création d'une tâche de test...")
        if sheets_client.create_task(test_task):
            print("✓ Tâche de test créée avec succès")
            if sheets_client.spreadsheet_id:
                print(f"📊 Vérifiez dans: https://docs.google.com/spreadsheets/d/{sheets_client.spreadsheet_id}")
        else:
            print("✗ Erreur lors de la création de la tâche de test")
            
    except Exception as e:
        print(f"✗ Erreur: {e}")

if __name__ == "__main__":
    print("Choisissez le mode de test:")
    print("1. Simulation complète (5 tâches)")
    print("2. Test d'une seule tâche")
    
    choice = input("\nVotre choix (1 ou 2): ").strip()
    
    if choice == "1":
        run_simulation()
    elif choice == "2":
        test_single_task()
    else:
        print("Choix invalide. Exécution de la simulation complète...")
        run_simulation() 