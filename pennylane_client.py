import requests
import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class PennylaneClient:
    """Client pour interagir avec l'API Pennylane v2"""
    
    def __init__(self):
        self.api_key = os.getenv('PENNYLANE_API_KEY')
        if not self.api_key:
            raise ValueError("PENNYLANE_API_KEY non définie dans les variables d'environnement")
        
        # URL correcte de l'API Pennylane selon la documentation
        self.base_url = "https://app.pennylane.com/api/external/v2"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_all_invoices(self) -> List[Dict]:
        """
        Récupère TOUTES les factures depuis Pennylane v2 avec pagination
        """
        all_invoices = []
        cursor = None
        page = 1
        
        print("Récupération de toutes les factures...")
        
        while True:
            url = f"{self.base_url}/customer_invoices"
            params = {'limit': 100}  # Maximum par page
            
            if cursor:
                params['cursor'] = cursor
            
            try:
                print(f"  Page {page}...")
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                invoices = data.get('items', [])
                has_more = data.get('has_more', False)
                next_cursor = data.get('next_cursor')
                
                all_invoices.extend(invoices)
                print(f"    {len(invoices)} factures récupérées (total: {len(all_invoices)})")
                
                if not has_more or not next_cursor:
                    break
                
                cursor = next_cursor
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors de la récupération de la page {page}: {e}")
                break
        
        print(f"✓ Récupération terminée: {len(all_invoices)} factures au total")
        return all_invoices
    
    def get_invoices(self, status: Optional[str] = None, limit: int = 100, updated_at: Optional[str] = None) -> List[Dict]:
        """
        Récupère les factures depuis Pennylane v2 (pour compatibilité)
        """
        # Si on demande toutes les factures, utiliser get_all_invoices
        if limit >= 1000:  # Seuil pour récupérer toutes les factures
            return self.get_all_invoices()
        
        url = f"{self.base_url}/customer_invoices"
        params = {'limit': limit}
        
        if status:
            # Construire le filtre selon la documentation
            if status == 'paid':
                # Utiliser le champ paid directement
                params['filter'] = 'paid:eq:true'
            elif status == 'unpaid':
                params['filter'] = 'paid:eq:false'
            elif status == 'partially_paid':
                # Pour les factures partiellement payées, on peut filtrer par status
                params['filter'] = 'status:eq:partially_cancelled'
        
        if updated_at:
            # Tenter de filtrer par updated_at
            if 'filter' in params:
                params['filter'] += f',updated_at:gteq:{updated_at}'
            else:
                params['filter'] = f'updated_at:gteq:{updated_at}'
        
        try:
            print(f"Tentative de connexion à: {url}")
            print(f"Paramètres: {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            # La réponse contient items, has_more, next_cursor selon la doc
            data = response.json()
            return data.get('items', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des factures: {e}")
            return []
    
    def get_customer_details(self, customer_url: str) -> Optional[Dict]:
        """
        Récupère les détails complets d'un client via l'URL fournie
        """
        try:
            response = requests.get(customer_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des détails du client: {e}")
            return None
    
    def get_payment_details(self, payment_url: str) -> Optional[Dict]:
        """
        Récupère les détails des paiements via l'URL fournie
        """
        try:
            response = requests.get(payment_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des paiements: {e}")
            return None
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """
        Récupère les informations d'un client via l'endpoint invoices avec filtre
        """
        url = f"{self.base_url}/customer_invoices"
        params = {
            'filter': f'customer_id:eq:{customer_id}',
            'limit': 1
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            invoices = data.get('items', [])
            
            if invoices:
                # Extraire les informations du client depuis la facture
                invoice = invoices[0]
                customer_info = invoice.get('customer', {})
                return customer_info
            
            return None
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération du client {customer_id}: {e}")
            return None
    
    def get_payment_info_from_invoice(self, invoice_data: Dict) -> Dict:
        """
        Extrait les informations de paiement directement depuis les données de la facture
        """
        payment_info = {
            'payment_date': '',
            'payment_amount': '',
            'status': ''
        }
        
        # Date de la facture
        payment_info['payment_date'] = invoice_data.get('date', '')
        
        # Montant de la facture
        payment_info['payment_amount'] = invoice_data.get('currency_amount', '0')
        
        # Statut selon la documentation
        if invoice_data.get('status') == 'partially_cancelled':
            payment_info['status'] = 'Partiellement payée'
        elif invoice_data.get('paid'):
            payment_info['status'] = 'Payée'
        else:
            payment_info['status'] = invoice_data.get('status', '')
        
        return payment_info
    
    def explore_endpoints(self):
        """
        Explore les endpoints disponibles pour comprendre la structure des données
        """
        print("=== Exploration des endpoints Pennylane v2 ===\n")
        
        # Test des factures - récupérer toutes les factures
        print("1. Test des factures (récupération complète):")
        all_invoices = self.get_all_invoices()
        
        if all_invoices:
            print(f"   - {len(all_invoices)} factures récupérées au total")
            
            # Analyser les types de factures
            credit_notes = [inv for inv in all_invoices if inv.get('status') == 'credit_note']
            regular_invoices = [inv for inv in all_invoices if inv.get('status') != 'credit_note']
            paid_invoices = [inv for inv in all_invoices if inv.get('paid')]
            
            print(f"   Répartition:")
            print(f"     - Avoirs: {len(credit_notes)}")
            print(f"     - Factures régulières: {len(regular_invoices)}")
            print(f"     - Factures payées: {len(paid_invoices)}")
            
            # Afficher la structure de la première facture
            if all_invoices:
                sample_invoice = all_invoices[0]
                print(f"   - Exemple de structure: {list(sample_invoice.keys())}")
                
                # Afficher les statuts disponibles
                statuses = set(inv.get('status') for inv in all_invoices)
                print(f"   - Statuts disponibles: {statuses}")
                
                # Vérifier si les informations client sont incluses
                if 'customer' in sample_invoice:
                    customer = sample_invoice['customer']
                    print(f"\n   Informations client incluses:")
                    for key, value in customer.items():
                        print(f"     {key}: {type(value).__name__} = {value}")
                
                # Vérifier si les paiements sont inclus
                if 'payments' in sample_invoice:
                    payments = sample_invoice['payments']
                    print(f"\n   Informations de paiement incluses:")
                    if isinstance(payments, dict) and 'url' in payments:
                        print(f"   Récupération des détails des paiements...")
                        payment_details = self.get_payment_details(payments['url'])
                        if payment_details:
                            print(f"   Détails des paiements:")
                            for key, value in payment_details.items():
                                print(f"     {key}: {type(value).__name__} = {value}")
        else:
            print("   - Aucune facture trouvée")
        
        # Test avec différents statuts
        print("\n2. Test avec différents statuts:")
        # Test simple sans filtre d'abord
        print("   - Test sans filtre:")
        paid_count = sum(1 for inv in all_invoices if inv.get('paid'))
        unpaid_count = sum(1 for inv in all_invoices if not inv.get('paid'))
        print(f"     Total: {len(all_invoices)}, Payées: {paid_count}, Non payées: {unpaid_count}")
        
        # Test avec filtre updated_at
        print("\n3. Test avec filtre updated_at:")
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"   - Test avec updated_at >= {today}:")
        invoices_today = [inv for inv in all_invoices if self.is_date_today(inv.get('updated_at'))]
        print(f"     Factures mises à jour aujourd'hui: {len(invoices_today)}")
        
        # Test avec filtre paid + updated_at
        print(f"   - Test avec paid=true ET updated_at >= {today}:")
        paid_today = [inv for inv in all_invoices if inv.get('paid') and self.is_date_today(inv.get('updated_at'))]
        print(f"     Factures payées aujourd'hui: {len(paid_today)}")
    
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

if __name__ == "__main__":
    # Test du client
    try:
        client = PennylaneClient()
        client.explore_endpoints()
    except Exception as e:
        print(f"Erreur lors de l'initialisation du client: {e}")
        print("Vérifiez que PENNYLANE_API_KEY est définie dans le fichier .env") 