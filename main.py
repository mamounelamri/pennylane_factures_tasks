import os
import json
import schedule
import time
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dotenv import load_dotenv

from pennylane_client import PennylaneClient
from google_sheets_client import GoogleSheetsClient

load_dotenv()

class PennylaneSheetsIntegration:
    """Intégration entre Pennylane v2 et Google Sheets"""
    
    def __init__(self):
        self.pennylane_client = PennylaneClient()
        self.sheets_client = GoogleSheetsClient()
        self.processed_items_file = 'processed_items.json'
        self.processed_items = self.load_processed_items()
    
    def load_processed_items(self) -> Set[str]:
        """Charge la liste des éléments déjà traités"""
        try:
            if os.path.exists(self.processed_items_file):
                with open(self.processed_items_file, 'r') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            print(f"Erreur lors du chargement des éléments traités: {e}")
            return set()
    
    def save_processed_items(self):
        """Sauvegarde la liste des éléments traités"""
        try:
            with open(self.processed_items_file, 'w') as f:
                json.dump(list(self.processed_items), f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des éléments traités: {e}")
    
    def format_date(self, date_str: str) -> str:
        """Formate une date pour l'affichage"""
        if not date_str:
            return ""
        try:
            # Supposons que la date est au format ISO
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%Y')
        except:
            return date_str
    
    def format_amount(self, amount: str) -> str:
        """Formate un montant pour l'affichage"""
        if not amount:
            return ""
        try:
            amount_float = float(amount)
            return f"{amount_float:.2f} €"
        except:
            return amount
    
    def is_date_today(self, date_str: str) -> bool:
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
    
    def get_payment_info(self, invoice_data: Dict) -> Dict:
        """
        Récupère les informations de paiement d'une facture depuis l'API v2
        """
        payment_info = {
            'payment_date': '',
            'payment_amount': '',
            'status': ''
        }
        
        # Date de la facture
        payment_info['payment_date'] = self.format_date(invoice_data.get('date'))
        
        # Montant de la facture
        payment_info['payment_amount'] = self.format_amount(invoice_data.get('currency_amount'))
        
        # Statut selon la documentation
        if invoice_data.get('status') == 'partially_cancelled':
            payment_info['status'] = 'Partiellement payée'
        elif invoice_data.get('paid'):
            payment_info['status'] = 'Payée'
        else:
            payment_info['status'] = invoice_data.get('status', '')
        
        return payment_info
    
    def create_task_from_invoice(self, invoice_data: Dict) -> Dict:
        """
        Crée une tâche à partir des données d'une facture (API v2)
        """
        payment_info = self.get_payment_info(invoice_data)
        
        # Dans l'API v2, les informations client sont incluses dans la facture
        customer_data = invoice_data.get('customer', {})
        
        # Utiliser l'ID du client comme référence (puisqu'on ne peut pas récupérer les détails)
        customer_id = customer_data.get('id', '')
        
        task_data = {
            'client_number': str(customer_id),
            'client_name': f"Client {customer_id}",  # Nom générique du client
            'invoice_number': invoice_data.get('invoice_number', ''),
            'invoice_date': self.format_date(invoice_data.get('date')),
            'payment_date': payment_info['payment_date'],
            'payment_amount': payment_info['payment_amount'],
            'status': payment_info['status'],
            'created_at': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        return task_data
    
    def process_paid_invoices_today(self):
        """Traite les factures passées en statut payé aujourd'hui"""
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n=== Traitement des factures payées aujourd'hui ({today}) - {datetime.now().strftime('%d/%m/%Y %H:%M')} ===")
        
        # Récupérer TOUTES les factures
        all_invoices = self.pennylane_client.get_all_invoices()
        
        # Filtrer uniquement les factures (pas les avoirs)
        regular_invoices = [inv for inv in all_invoices if inv.get('status') != 'credit_note']
        
        # Filtrer les factures payées ET mises à jour aujourd'hui
        paid_invoices_today = []
        for invoice in regular_invoices:
            if invoice.get('paid') and self.is_date_today(invoice.get('updated_at')):
                paid_invoices_today.append(invoice)
        
        # Filtrer les factures partiellement payées ET mises à jour aujourd'hui
        partially_paid_invoices_today = []
        for invoice in regular_invoices:
            if (invoice.get('status') == 'partially_cancelled' and 
                self.is_date_today(invoice.get('updated_at'))):
                partially_paid_invoices_today.append(invoice)
        
        all_invoices_to_process = paid_invoices_today + partially_paid_invoices_today
        
        print(f"Nombre total de factures analysées: {len(regular_invoices)}")
        print(f"  - Factures payées aujourd'hui: {len(paid_invoices_today)}")
        print(f"  - Factures partiellement payées aujourd'hui: {len(partially_paid_invoices_today)}")
        print(f"  - Avoirs ignorés: {len([inv for inv in all_invoices if inv.get('status') == 'credit_note'])}")
        
        processed_count = 0
        
        for invoice in all_invoices_to_process:
            invoice_id = invoice.get('id')
            
            # Vérifier si déjà traité
            if invoice_id in self.processed_items:
                continue
            
            # Vérifier que les informations client sont présentes
            customer_data = invoice.get('customer', {})
            if not customer_data:
                print(f"Pas d'informations client pour la facture {invoice.get('invoice_number', 'N/A')}")
                continue
            
            # Créer la tâche
            task_data = self.create_task_from_invoice(invoice)
            
            # Ajouter au Google Sheet
            if self.sheets_client.create_task(task_data):
                self.processed_items.add(invoice_id)
                processed_count += 1
                print(f"  ✓ Facture {task_data['invoice_number']} traitée (payée le {self.format_date(invoice.get('updated_at'))})")
            else:
                print(f"  ✗ Erreur lors du traitement de la facture {invoice.get('invoice_number', 'N/A')}")
        
        # Sauvegarder les éléments traités
        if processed_count > 0:
            self.save_processed_items()
            print(f"\n{processed_count} nouvelles factures traitées aujourd'hui")
        else:
            print("\nAucune nouvelle facture payée aujourd'hui")
    
    def run_initial_setup(self):
        """Configuration initiale"""
        print("=== Configuration initiale ===")
        
        # Configuration du Google Sheet
        self.sheets_client.setup_spreadsheet()
        
        # Test de connexion Pennylane
        print("\nTest de connexion Pennylane v2...")
        try:
            # Test avec quelques factures d'abord
            invoices = self.pennylane_client.get_invoices(limit=1)
            if invoices:
                print("✓ Connexion Pennylane v2 réussie")
                print(f"  - {len(invoices)} facture(s) trouvée(s) (test)")
                
                # Afficher un aperçu de la structure
                sample_invoice = invoices[0]
                print(f"  - Structure: {list(sample_invoice.keys())}")
                
                if 'customer' in sample_invoice:
                    print("  - ✓ Informations client incluses")
                if 'payments' in sample_invoice:
                    print("  - ✓ Informations de paiement incluses")
            else:
                print("⚠ Aucune facture trouvée (vérifiez votre clé API)")
        except Exception as e:
            print(f"✗ Erreur de connexion Pennylane: {e}")
        
        print("\nConfiguration terminée!")
    
    def run_once(self):
        """Exécute une fois le traitement complet"""
        try:
            self.process_paid_invoices_today()
        except Exception as e:
            print(f"Erreur lors du traitement: {e}")
            sys.exit(1)  # Code d'erreur pour GitHub Actions
    
    def run_scheduled(self):
        """Exécute le traitement de manière planifiée (tous les midis)"""
        print("Démarrage du traitement planifié (tous les midis à 12h00)...")
        
        # Traitement tous les midis à 12h00
        schedule.every().day.at("12:00").do(self.run_once)
        
        # Traitement initial
        print("Exécution du traitement initial...")
        self.run_once()
        
        # Boucle de surveillance
        while True:
            schedule.run_pending()
            time.sleep(60)  # Vérifier toutes les minutes

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Intégration Pennylane v2 - Google Sheets')
    parser.add_argument('--auto', action='store_true', help='Mode automatique pour GitHub Actions')
    args = parser.parse_args()
    
    print("=== Intégration Pennylane v2 - Google Sheets ===\n")
    
    try:
        integration = PennylaneSheetsIntegration()
        
        if args.auto:
            # Mode automatique pour GitHub Actions
            print("Mode automatique activé (GitHub Actions)")
            integration.run_initial_setup()
            integration.run_once()
            print("✓ Traitement automatique terminé avec succès")
        else:
            # Mode interactif
            # Configuration initiale
            integration.run_initial_setup()
            
            # Demander le mode d'exécution
            print("\nChoisissez le mode d'exécution:")
            print("1. Exécution unique (traitement des factures payées aujourd'hui)")
            print("2. Surveillance continue (tous les midis à 12h00)")
            
            choice = input("\nVotre choix (1 ou 2): ").strip()
            
            if choice == "1":
                print("\nExécution unique...")
                integration.run_once()
            elif choice == "2":
                print("\nDémarrage de la surveillance continue...")
                integration.run_scheduled()
            else:
                print("Choix invalide. Exécution unique par défaut.")
                integration.run_once()
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation: {e}")
        print("Vérifiez votre configuration dans le fichier .env")
        sys.exit(1)  # Code d'erreur pour GitHub Actions

if __name__ == "__main__":
    main() 