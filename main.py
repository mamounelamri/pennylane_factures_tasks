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
from sync_payments import sync_with_error_handling

load_dotenv()

class PennylaneSheetsIntegration:
    """Intégration entre Pennylane v2, Google Sheets et Armado"""
    
    def __init__(self, test_mode=False):
        self.pennylane_client = PennylaneClient()
        self.sheets_client = GoogleSheetsClient()
        self.processed_items_file = 'processed_items.json'
        self.processed_items = self.load_processed_items()
        self.test_mode = test_mode
    
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
        try:
            return f"{float(amount):.2f}€"
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
    
    def extract_client_name(self, label: str) -> str:
        """Extrait le nom du client du label de facture"""
        if not label:
            return 'N/A'
        
        try:
            # Format: "Facture EURO DISNEY ASSOCIES SAS - 20498 (label généré)"
            if label.startswith('Facture '):
                # Enlever "Facture " au début
                without_prefix = label[8:]  # "EURO DISNEY ASSOCIES SAS - 20498 (label généré)"
                
                # Trouver le premier "-" et prendre ce qui est avant
                if ' - ' in without_prefix:
                    client_name = without_prefix.split(' - ')[0]
                    return client_name.strip()
            
            # Format: "Avoir PROJET X AQUAPARK - 20572 (label généré)"
            if label.startswith('Avoir '):
                # Enlever "Avoir " au début
                without_prefix = label[6:]  # "PROJET X AQUAPARK - 20572 (label généré)"
                
                # Trouver le premier "-" et prendre ce qui est avant
                if ' - ' in without_prefix:
                    client_name = without_prefix.split(' - ')[0]
                    return client_name.strip()
            
            # Format: "PROJET X AQUAPARK - 20572 (label généré)" (sans préfixe)
            if ' - ' in label:
                client_name = label.split(' - ')[0]
                return client_name.strip()
            
            # Si le format n'est pas reconnu, retourner le label complet
            return label
        except:
            return label
    
    def sync_to_armado(self, invoice_number: str, payment_status: str, payment_date: datetime) -> Dict:
        """
        Synchronise le paiement vers Armado
        
        Args:
            invoice_number: Numéro de facture Tempo
            payment_status: Statut de paiement (Payée, Partiellement payée)
            payment_date: Date de paiement
            
        Returns:
            Résultat de la synchronisation
        """
        if self.test_mode:
            print(f"[Armado] Mode test - synchronisation désactivée pour {invoice_number}")
            return {'success': True, 'data': None, 'error': None}
        
        try:
            # Déterminer le mode de paiement par défaut (à adapter selon vos besoins)
            payment_mode = "virement"  # Mode par défaut, à personnaliser
            
            print(f"[Armado] Synchronisation: {invoice_number} ({payment_status})")
            
            result = sync_with_error_handling(
                invoice_reference=invoice_number,
                payment_mode=payment_mode,
                payment_date=payment_date
            )
            
            if result['success']:
                print(f"[Armado] ✓ Synchronisé: {invoice_number}")
            else:
                print(f"[Armado] ✗ Erreur: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Erreur inattendue Armado: {e}"
            print(f"[Armado] ✗ {error_msg}")
            return {'success': False, 'data': None, 'error': error_msg}
    
    def create_task_from_invoice(self, invoice: Dict) -> Dict:
        """Crée les données de tâche à partir d'une facture Pennylane"""
        try:
            # Calculs des montants avec gestion des valeurs None
            total_amount = float(invoice.get('amount', 0) or 0)
            remaining_amount = float(invoice.get('remaining_amount_with_tax', 0) or 0)
            paid_amount = total_amount - remaining_amount
            payment_percentage = (paid_amount / total_amount * 100) if total_amount > 0 else 0
            
            # Déterminer le statut de paiement
            if paid_amount >= total_amount or remaining_amount <= 0:
                payment_status = "Payée"
                task_name = "Règlement de facture"
            elif paid_amount > 0:
                payment_status = "Partiellement payée"
                task_name = "Règlement partiel de facture"
            else:
                payment_status = "Non payée"
                task_name = "Règlement de facture"
            
            # Formater les montants pour l'affichage
            total_formatted = f"{total_amount:.2f}€"
            paid_formatted = f"{paid_amount:.2f}€"
            remaining_formatted = f"{remaining_amount:.2f}€"
            
            # Informations de base
            invoice_number = invoice.get('invoice_number', 'N/A')
            invoice_date = self.format_date(invoice.get('date'))
            client_name = self.extract_client_name(invoice.get('label', 'N/A'))
            
            # Construire les champs modifiés avec plus de détails
            champs_modifies = f"Montant total : {total_formatted} / Montant payé : {paid_formatted} / Reste : {remaining_formatted}"
            
            # Commentaire interne avec statut de paiement
            commentaire_interne = f"Date facture : {invoice_date} / Statut : {payment_status} ({payment_percentage:.0f}%)"
            
            return {
                'invoice_number': invoice_number,
                'invoice_date': invoice_date,
                'payment_amount': paid_formatted,
                'client_name': client_name,
                'total_amount': total_formatted,
                'remaining_amount': remaining_formatted,
                'payment_status': payment_status,
                'payment_percentage': payment_percentage,
                'task_name': task_name,
                'champs_modifies': champs_modifies,
                'commentaire_interne': commentaire_interne
            }
            
        except Exception as e:
            print(f"Erreur lors de la création des données de tâche: {e}")
            return {}
    
    def process_paid_invoices_today(self):
        """Traite les factures passées en statut payé aujourd'hui"""
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n=== Traitement des factures payées aujourd'hui ({today}) - {datetime.now().strftime('%d/%m/%Y %H:%M')} ===")

        # Récupérer TOUTES les factures
        all_invoices = self.pennylane_client.get_all_invoices()

        # Filtrer uniquement les factures (pas les avoirs)
        regular_invoices = [inv for inv in all_invoices if inv.get('status') != 'credit_note']

        # Filtrer les factures avec paiement ET mises à jour aujourd'hui
        paid_invoices_today = []
        partially_paid_invoices_today = []
        
        for invoice in regular_invoices:
            # Vérifier si la facture a été mise à jour aujourd'hui
            if not self.is_date_today(invoice.get('updated_at')):
                continue
                
            # Calculer les montants avec gestion des valeurs None
            total_amount = float(invoice.get('amount', 0) or 0)
            remaining_amount = float(invoice.get('remaining_amount_with_tax', 0) or 0)
            paid_amount = total_amount - remaining_amount
            
            # Classifier selon le montant payé
            if paid_amount >= total_amount or remaining_amount <= 0:
                paid_invoices_today.append(invoice)
            elif paid_amount > 0:
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

            # Créer la tâche avec les nouveaux calculs
            task_data = self.create_task_from_invoice(invoice)
            
            if not task_data:
                print(f"✗ Erreur lors de la création des données pour la facture {invoice.get('invoice_number', 'N/A')}")
                continue

            # Ajouter au Google Sheet
            if self.sheets_client.create_task(task_data):
                self.processed_items.add(invoice_id)
                processed_count += 1
                print(f"  ✓ Facture {task_data['invoice_number']} traitée ({task_data['payment_status']})")
                
                # Synchronisation Armado UNIQUEMENT pour les factures complètement payées
                if task_data['payment_status'] == "Payée":
                    armado_result = self.sync_to_armado(
                        invoice_number=task_data['invoice_number'],
                        payment_status=task_data['payment_status'],
                        payment_date=datetime.now()
                    )
                    
                    # Log du résultat Armado (ne fait pas échouer le traitement principal)
                    if not armado_result['success']:
                        print(f"  ⚠ Synchronisation Armado échouée: {armado_result['error']}")
                else:
                    print(f"  ℹ Facture partiellement payée - pas de synchronisation Armado")
                
            else:
                print(f"  ✗ Erreur lors du traitement de la facture {invoice.get('invoice_number', 'N/A')}")

            # Délai de 1 seconde entre chaque facture pour éviter les quotas
            time.sleep(1)

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
    parser = argparse.ArgumentParser(description='Intégration Pennylane v2 - Google Sheets - Armado')
    parser.add_argument('--auto', action='store_true', help='Mode automatique pour GitHub Actions')
    parser.add_argument('--test-mode', action='store_true', help='Mode test (désactive la synchronisation Armado)')
    args = parser.parse_args()
    
    print("=== Intégration Pennylane v2 - Google Sheets - Armado ===\n")
    
    # Déterminer le mode test
    test_mode = args.test_mode or os.getenv('TEST_MODE', 'false').lower() == 'true'
    if test_mode:
        print("🧪 Mode test activé - synchronisation Armado désactivée")
    
    try:
        integration = PennylaneSheetsIntegration(test_mode=test_mode)
        
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