"""
Exemple d'intégration Tempo -> Armado
Ce fichier montre comment intégrer la synchronisation Armado après une mise à jour de paiement Tempo
"""

import requests
from datetime import datetime
from typing import Dict, Optional
from sync_payments import sync_armado_after_tempo, sync_with_error_handling

class TempoArmadoIntegration:
    """Exemple d'intégration entre Tempo et Armado"""
    
    def __init__(self):
        # Configuration Tempo (à adapter selon votre setup)
        self.tempo_api_key = "your_tempo_api_key"
        self.tempo_base_url = "https://your_tempo_api_url"
        self.tempo_headers = {
            'Authorization': f'Bearer {self.tempo_api_key}',
            'Content-Type': 'application/json'
        }
    
    def process_tempo_payment_update(self, invoice_number: str, payment_data: Dict) -> Dict:
        """
        Traite une mise à jour de paiement Tempo et synchronise avec Armado
        
        Args:
            invoice_number: Numéro de facture Tempo
            payment_data: Données de paiement (montant, mode, date, etc.)
            
        Returns:
            Résultat de la synchronisation
        """
        print(f"[Tempo-Armado] Traitement du paiement pour la facture {invoice_number}")
        
        # 1. Mise à jour du paiement sur Tempo (FACTUREREGLEMENT)
        tempo_result = self._update_tempo_payment(invoice_number, payment_data)
        
        if tempo_result['success']:
            print(f"[Tempo-Armado] ✓ Paiement Tempo mis à jour avec succès")
            
            # 2. Synchronisation vers Armado
            armado_result = self._sync_to_armado(invoice_number, payment_data)
            
            return {
                'tempo_success': True,
                'armado_success': armado_result['success'],
                'armado_data': armado_result.get('data'),
                'armado_error': armado_result.get('error')
            }
        else:
            print(f"[Tempo-Armado] ✗ Erreur Tempo: {tempo_result['error']}")
            return {
                'tempo_success': False,
                'armado_success': False,
                'armado_data': None,
                'armado_error': f"Tempo error: {tempo_result['error']}"
            }
    
    def _update_tempo_payment(self, invoice_number: str, payment_data: Dict) -> Dict:
        """
        Met à jour le paiement sur Tempo (FACTUREREGLEMENT)
        
        Args:
            invoice_number: Numéro de facture
            payment_data: Données de paiement
            
        Returns:
            Résultat de la mise à jour Tempo
        """
        try:
            # URL de l'endpoint FACTUREREGLEMENT (à adapter selon votre API Tempo)
            url = f"{self.tempo_base_url}/FACTUREREGLEMENT"
            
            # Payload pour Tempo (à adapter selon votre structure)
            payload = {
                'invoice_number': invoice_number,
                'payment_amount': payment_data.get('amount'),
                'payment_date': payment_data.get('date'),
                'payment_mode': payment_data.get('mode')
            }
            
            print(f"[Tempo] Mise à jour du paiement: {payload}")
            
            response = requests.put(
                url,
                headers=self.tempo_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'data': None,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def _sync_to_armado(self, invoice_number: str, payment_data: Dict) -> Dict:
        """
        Synchronise le paiement vers Armado
        
        Args:
            invoice_number: Numéro de facture Tempo (utilisé comme référence Armado)
            payment_data: Données de paiement
            
        Returns:
            Résultat de la synchronisation Armado
        """
        try:
            # Extraire les données nécessaires
            payment_mode = payment_data.get('mode', 'virement')
            payment_date_str = payment_data.get('date')
            
            # Convertir la date si nécessaire
            if isinstance(payment_date_str, str):
                payment_date = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00'))
            else:
                payment_date = payment_date_str or datetime.now()
            
            print(f"[Armado] Synchronisation: ref={invoice_number}, mode={payment_mode}, date={payment_date}")
            
            # Utiliser la fonction de synchronisation avec gestion d'erreur
            return sync_with_error_handling(
                invoice_reference=invoice_number,
                payment_mode=payment_mode,
                payment_date=payment_date
            )
            
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': f"Erreur de synchronisation: {e}"
            }

def example_usage():
    """Exemple d'utilisation de l'intégration"""
    
    # Initialiser l'intégration
    integration = TempoArmadoIntegration()
    
    # Données de paiement exemple
    payment_data = {
        'amount': 1500.00,
        'mode': 'virement',
        'date': datetime.now().isoformat(),
        'reference': 'PAY_2024_001'
    }
    
    # Numéro de facture Tempo
    invoice_number = "20664"
    
    print("=== Exemple d'intégration Tempo -> Armado ===")
    print(f"Facture: {invoice_number}")
    print(f"Paiement: {payment_data}")
    
    # Traiter le paiement
    result = integration.process_tempo_payment_update(invoice_number, payment_data)
    
    # Afficher le résultat
    print("\n=== Résultat ===")
    print(f"Tempo: {'✓' if result['tempo_success'] else '✗'}")
    print(f"Armado: {'✓' if result['armado_success'] else '✗'}")
    
    if result['armado_error']:
        print(f"Erreur Armado: {result['armado_error']}")
    
    if result['armado_data']:
        print(f"Données Armado: {result['armado_data']}")

def example_batch_processing():
    """Exemple de traitement par lot"""
    
    integration = TempoArmadoIntegration()
    
    # Liste de paiements à traiter
    payments = [
        {
            'invoice_number': '20664',
            'payment_data': {
                'amount': 1500.00,
                'mode': 'virement',
                'date': datetime.now().isoformat()
            }
        },
        {
            'invoice_number': '20665',
            'payment_data': {
                'amount': 750.00,
                'mode': 'cb',
                'date': datetime.now().isoformat()
            }
        }
    ]
    
    print("=== Traitement par lot ===")
    
    results = []
    for payment in payments:
        print(f"\nTraitement de la facture {payment['invoice_number']}...")
        
        result = integration.process_tempo_payment_update(
            payment['invoice_number'],
            payment['payment_data']
        )
        
        results.append({
            'invoice_number': payment['invoice_number'],
            'result': result
        })
        
        # Délai entre les traitements pour éviter les quotas
        import time
        time.sleep(1)
    
    # Résumé
    print("\n=== Résumé du traitement par lot ===")
    tempo_success = sum(1 for r in results if r['result']['tempo_success'])
    armado_success = sum(1 for r in results if r['result']['armado_success'])
    
    print(f"Tempo: {tempo_success}/{len(results)} succès")
    print(f"Armado: {armado_success}/{len(results)} succès")
    
    # Afficher les erreurs
    for result in results:
        if not result['result']['armado_success'] and result['result']['armado_error']:
            print(f"Erreur {result['invoice_number']}: {result['result']['armado_error']}")

if __name__ == "__main__":
    # Exécuter les exemples
    example_usage()
    print("\n" + "="*50 + "\n")
    example_batch_processing()
