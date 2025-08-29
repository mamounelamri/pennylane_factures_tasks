#!/usr/bin/env python3
"""
Intégration Pennylane - Tempo
Automatise l'enregistrement des règlements de factures dans Tempo
basé sur les données de Pennylane
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

from pennylane_client import PennylaneClient
from tempo_client import TempoClient

# Import optionnel pour éviter les erreurs si le client email n'est pas configuré
try:
    from tempo_email_client import TempoEmailClient
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    TempoEmailClient = None

load_dotenv()

class TempoIntegration:
    """Intégration entre Pennylane et Tempo pour l'automatisation des règlements"""
    
    def __init__(self):
        self.pennylane_client = PennylaneClient()
        self.tempo_client = TempoClient()
        self.processed_reglements_file = 'processed_reglements.json'
        self.processed_reglements = self.load_processed_reglements()
        
        # Initialiser le client email si disponible
        self.email_client = None
        if EMAIL_AVAILABLE:
            try:
                self.email_client = TempoEmailClient()
                print("✅ Client email Office365 initialisé")
            except Exception as e:
                print(f"⚠ Client email non disponible: {e}")
                self.email_client = None
    
    def load_processed_reglements(self) -> Dict[str, Dict]:
        """Charge la liste des règlements déjà traités"""
        try:
            if os.path.exists(self.processed_reglements_file):
                with open(self.processed_reglements_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Erreur lors du chargement des règlements traités: {e}")
            return {}
    
    def save_processed_reglements(self):
        """Sauvegarde la liste des règlements traités"""
        try:
            with open(self.processed_reglements_file, 'w') as f:
                json.dump(self.processed_reglements, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des règlements traités: {e}")
    
    def get_reglement_key(self, invoice_id: str, payment_date: str, amount: float) -> str:
        """Génère une clé unique pour identifier un règlement"""
        return f"{invoice_id}_{payment_date}_{amount}"
    
    def extract_invoice_number_from_label(self, label: str) -> Optional[int]:
        """Extrait le numéro de facture du label Pennylane"""
        if not label:
            return None
        
        try:
            # Format: "Facture EURO DISNEY ASSOCIES SAS - 20498 (label généré)"
            if ' - ' in label:
                parts = label.split(' - ')
                if len(parts) >= 2:
                    # Prendre la deuxième partie et extraire le numéro
                    second_part = parts[1]
                    # Chercher un nombre dans cette partie
                    import re
                    numbers = re.findall(r'\d+', second_part)
                    if numbers:
                        return int(numbers[0])
            return None
        except:
            return None
    
    def get_payment_amount(self, invoice: Dict) -> float:
        """Calcule le montant payé pour une facture"""
        try:
            total_amount = float(invoice.get('amount', 0) or 0)
            remaining_amount = float(invoice.get('remaining_amount_with_tax', 0) or 0)
            return total_amount - remaining_amount
        except:
            return 0.0
    
    def is_invoice_fully_paid(self, invoice: Dict) -> bool:
        """Vérifie si une facture est entièrement payée"""
        try:
            remaining_amount = float(invoice.get('remaining_amount_with_tax', 0) or 0)
            return remaining_amount <= 0
        except:
            return False
    
    def process_invoice_payment(self, invoice: Dict) -> bool:
        """Traite le paiement d'une facture en l'enregistrant dans Tempo"""
        try:
            invoice_id = invoice.get('id')
            invoice_number = self.extract_invoice_number_from_label(invoice.get('label', ''))
            
            if not invoice_number:
                print(f"⚠ Impossible d'extraire le numéro de facture pour {invoice_id}")
                return False
            
            # Calculer le montant payé
            payment_amount = self.get_payment_amount(invoice)
            if payment_amount <= 0:
                print(f"⚠ Aucun montant payé pour la facture {invoice_number}")
                return False
            
            # Vérifier si c'est un paiement total ou partiel
            is_fully_paid = self.is_invoice_fully_paid(invoice)
            
            # Date de règlement (aujourd'hui par défaut)
            payment_date = datetime.now()
            payment_date_str = payment_date.strftime('%Y%m%d')
            
            # Générer la clé unique du règlement
            reglement_key = self.get_reglement_key(invoice_id, payment_date_str, payment_amount)
            
            # Vérifier si déjà traité
            if reglement_key in self.processed_reglements:
                print(f"⚠ Règlement déjà traité pour la facture {invoice_number}")
                return True
            
            print(f"\n=== Traitement du règlement ===")
            print(f"Facture Pennylane ID: {invoice_id}")
            print(f"Numéro de facture Tempo: {invoice_number}")
            print(f"Montant payé: {payment_amount}€")
            print(f"Date de règlement: {payment_date_str}")
            print(f"Type: {'Total' if is_fully_paid else 'Partiel'}")
            
            # Enregistrer dans Tempo
            success = False
            if is_fully_paid:
                # Cas A: Règlement total
                success = self.tempo_client.enregistrer_reglement_total(
                    invoice_number, payment_date_str
                )
            else:
                # Cas B: Règlement partiel
                success = self.tempo_client.enregistrer_reglement_partiel(
                    invoice_number, payment_amount, payment_date_str
                )
            
            if success:
                # Marquer comme traité
                self.processed_reglements[reglement_key] = {
                    'invoice_id': invoice_id,
                    'invoice_number': invoice_number,
                    'payment_amount': payment_amount,
                    'payment_date': payment_date_str,
                    'is_fully_paid': is_fully_paid,
                    'processed_at': datetime.now().isoformat()
                }
                
                print(f"✓ Règlement enregistré avec succès dans Tempo")
                
                # Vérifier l'état dans Tempo
                print("\nVérification de l'état dans Tempo...")
                tempo_facture = self.tempo_client.get_facture(invoice_number)
                if tempo_facture:
                    print("✓ État récupéré depuis Tempo")
                else:
                    print("⚠ Impossible de récupérer l'état depuis Tempo")
                
                return True
            else:
                print(f"✗ Échec de l'enregistrement dans Tempo")
                return False
                
        except Exception as e:
            print(f"✗ Erreur lors du traitement du paiement: {e}")
            return False
    
    def process_paid_invoices_today(self):
        """Traite les factures passées en statut payé aujourd'hui"""
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n=== Traitement des factures payées aujourd'hui ({today}) ===")
        print(f"Début: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Récupérer toutes les factures Pennylane
        all_invoices = self.pennylane_client.get_all_invoices()
        
        # Filtrer uniquement les factures (pas les avoirs)
        regular_invoices = [inv for inv in all_invoices if inv.get('status') != 'credit_note']
        
        # Filtrer les factures avec paiement ET mises à jour aujourd'hui
        paid_invoices_today = []
        
        for invoice in regular_invoices:
            # Vérifier si la facture a été mise à jour aujourd'hui
            updated_at = invoice.get('updated_at')
            if not updated_at:
                continue
            
            try:
                # Parser la date ISO
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                if updated_date.date() == datetime.now().date():
                    # Vérifier s'il y a un paiement
                    payment_amount = self.get_payment_amount(invoice)
                    if payment_amount > 0:
                        paid_invoices_today.append(invoice)
            except:
                continue
        
        print(f"Nombre total de factures analysées: {len(regular_invoices)}")
        print(f"Factures payées aujourd'hui: {len(paid_invoices_today)}")
        
        if not paid_invoices_today:
            print("Aucune facture payée aujourd'hui")
            return
        
        # Traiter chaque facture avec suivi détaillé
        processed_count = 0
        error_count = 0
        operation_details = []
        
        for invoice in paid_invoices_today:
            try:
                if self.process_invoice_payment(invoice):
                    processed_count += 1
                    operation_details.append({
                        'success': True,
                        'invoice_number': self.extract_invoice_number_from_label(invoice.get('label', '')),
                        'operation_type': 'Règlement automatique',
                        'amount': self.get_payment_amount(invoice),
                        'message': 'Succès'
                    })
                else:
                    error_count += 1
                    operation_details.append({
                        'success': False,
                        'invoice_number': self.extract_invoice_number_from_label(invoice.get('label', '')),
                        'operation_type': 'Règlement automatique',
                        'amount': self.get_payment_amount(invoice),
                        'message': 'Échec du traitement'
                    })
                
                # Délai entre les traitements pour éviter les quotas
                time.sleep(1)
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                print(f"✗ Erreur lors du traitement de la facture {invoice.get('id')}: {error_msg}")
                
                operation_details.append({
                    'success': False,
                    'invoice_number': self.extract_invoice_number_from_label(invoice.get('label', '')),
                    'operation_type': 'Règlement automatique',
                    'amount': self.get_payment_amount(invoice),
                    'message': f'Exception: {error_msg}'
                })
        
        # Sauvegarder les règlements traités
        if processed_count > 0:
            self.save_processed_reglements()
            print(f"\n{processed_count} règlements traités avec succès")
        
        if error_count > 0:
            print(f"{error_count} erreurs rencontrées")
        
        # Envoyer le résumé par email si disponible
        if self.email_client and (processed_count > 0 or error_count > 0):
            print("\nEnvoi du résumé par email...")
            self.email_client.send_integration_summary(
                processed_count, error_count, operation_details
            )
        
        print(f"Fin: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    def run_initial_setup(self):
        """Configuration initiale et test de connexion"""
        print("=== Configuration initiale Tempo ===")
        
        # Test de connexion Tempo
        print("\nTest de connexion Tempo...")
        try:
            # Essayer de récupérer une facture de test (ID 1 par défaut)
            test_facture = self.tempo_client.get_facture(1)
            if test_facture:
                print("✓ Connexion Tempo réussie")
                print("Note: La facture de test peut ne pas exister, mais la connexion fonctionne")
            else:
                print("⚠ Connexion Tempo établie mais impossible de récupérer la facture de test")
                print("Cela peut être normal si la facture ID 1 n'existe pas")
        except Exception as e:
            print(f"✗ Erreur de connexion Tempo: {e}")
            print("Vérifiez votre configuration dans le fichier .env")
            return False
        
        # Test de connexion Pennylane
        print("\nTest de connexion Pennylane...")
        try:
            invoices = self.pennylane_client.get_invoices(limit=1)
            if invoices:
                print("✓ Connexion Pennylane réussie")
            else:
                print("⚠ Aucune facture trouvée dans Pennylane")
        except Exception as e:
            print(f"✗ Erreur de connexion Pennylane: {e}")
            return False
        
        print("\nConfiguration initiale terminée!")
        return True
    
    def run_once(self):
        """Exécute une fois le traitement complet"""
        try:
            self.process_paid_invoices_today()
        except Exception as e:
            print(f"Erreur lors du traitement: {e}")
            raise
    
    def run_scheduled(self):
        """Exécute le traitement de manière planifiée"""
        print("Démarrage du traitement planifié (tous les midis à 12h00)...")
        
        import schedule
        
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Intégration Pennylane - Tempo')
    parser.add_argument('--auto', action='store_true', help='Mode automatique pour GitHub Actions')
    parser.add_argument('--once', action='store_true', help='Exécution unique')
    parser.add_argument('--scheduled', action='store_true', help='Mode planifié')
    
    args = parser.parse_args()
    
    print("=== Intégration Pennylane - Tempo ===\n")
    
    try:
        integration = TempoIntegration()
        
        if args.auto:
            # Mode automatique pour GitHub Actions
            print("Mode automatique activé (GitHub Actions)")
            if integration.run_initial_setup():
                integration.run_once()
                print("✓ Traitement automatique terminé avec succès")
            else:
                print("✗ Échec de la configuration initiale")
                exit(1)
        elif args.once:
            # Mode exécution unique
            print("Mode exécution unique...")
            if integration.run_initial_setup():
                integration.run_once()
            else:
                print("✗ Échec de la configuration initiale")
                exit(1)
        elif args.scheduled:
            # Mode planifié
            print("Mode planifié...")
            if integration.run_initial_setup():
                integration.run_scheduled()
            else:
                print("✗ Échec de la configuration initiale")
                exit(1)
        else:
            # Mode interactif
            if not integration.run_initial_setup():
                print("✗ Échec de la configuration initiale")
                exit(1)
            
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
        exit(1)

if __name__ == "__main__":
    main()
