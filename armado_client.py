import requests
import os
import time
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

class ArmadoClient:
    """Client pour interagir avec l'API Armado"""
    
    def __init__(self):
        self.api_key = os.getenv('ARMADO_API_KEY')
        if not self.api_key:
            raise ValueError("ARMADO_API_KEY non définie dans les variables d'environnement")
        
        self.base_url = os.getenv('ARMADO_BASE_URL', 'https://api.myarmado.fr')
        self.timeout = int(os.getenv('ARMADO_TIMEOUT', '10'))
        self.max_retries = 3
        
        self.headers = {
            'ApiKey': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Effectue une requête HTTP avec retry automatique sur les erreurs 5xx
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Si c'est un succès ou une erreur client (4xx), on retourne directement
                if response.status_code < 500:
                    return response
                
                # Pour les erreurs 5xx, on retry avec backoff
                if attempt < self.max_retries - 1:
                    wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    print(f"[Armado] Erreur {response.status_code}, retry dans {wait_time}s (tentative {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[Armado] Erreur {response.status_code} après {self.max_retries} tentatives")
                    return response
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = 0.5 * (2 ** attempt)
                    print(f"[Armado] Erreur de connexion: {e}, retry dans {wait_time}s (tentative {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"[Armado] Erreur de connexion après {self.max_retries} tentatives: {e}")
                    raise
        
        return response
    
    def find_bill_id_by_reference(self, reference: str) -> Optional[int]:
        """
        Trouve l'ID d'une facture Armado par sa référence
        
        Args:
            reference: Numéro de facture Tempo (utilisé comme référence Armado)
            
        Returns:
            ID de la facture Armado si trouvée, None sinon
            
        Raises:
            ValueError: En cas d'erreur API (401, 422, etc.)
        """
        if not reference:
            raise ValueError("La référence ne peut pas être vide")
        
        url = f"{self.base_url}/v1/bill"
        params = {'reference': reference}
        
        try:
            print(f"[Armado] Recherche de la facture avec référence: {reference}")
            response = self._make_request_with_retry('GET', url, params=params)
            
            if response.status_code == 401:
                raise ValueError("API key invalide - vérifiez ARMADO_API_KEY")
            
            if response.status_code == 404:
                print(f"[Armado] Aucune facture trouvée avec la référence: {reference}")
                return None
            
            if response.status_code == 422:
                error_data = response.json()
                error_msg = error_data.get('message', 'Erreur de validation')
                raise ValueError(f"Erreur de validation Armado: {error_msg}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # L'API retourne une liste de factures
            if isinstance(data, list) and len(data) > 0:
                bill_id = data[0].get('id')
                if bill_id:
                    print(f"[Armado] Facture trouvée: ID={bill_id}, référence={reference}")
                    return bill_id
                else:
                    print(f"[Armado] Facture trouvée mais sans ID: {data[0]}")
                    return None
            else:
                print(f"[Armado] Aucune facture trouvée avec la référence: {reference}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[Armado] Erreur lors de la recherche de la facture: {e}")
            raise ValueError(f"Erreur de connexion Armado: {e}")
        except ValueError:
            # Re-raise les ValueError (erreurs métier)
            raise
        except Exception as e:
            print(f"[Armado] Erreur inattendue lors de la recherche: {e}")
            raise ValueError(f"Erreur inattendue Armado: {e}")
    
    def update_bill_payment(self, bill_id: int, payment_type: int, payment_date_iso: str) -> Dict:
        """
        Met à jour le paiement d'une facture Armado
        
        Args:
            bill_id: ID de la facture Armado
            payment_type: Type de paiement (1=chèque, 2=virement, 3=CB, 4=espèces)
            payment_date_iso: Date de paiement au format ISO (YYYY-MM-DDTHH:mm:ss.000000)
            
        Returns:
            Données de la facture mise à jour
            
        Raises:
            ValueError: En cas d'erreur API (401, 404, 422, etc.)
        """
        if not bill_id:
            raise ValueError("L'ID de la facture ne peut pas être vide")
        
        if payment_type is None:
            raise ValueError("Le type de paiement ne peut pas être None")
        
        if not payment_date_iso:
            raise ValueError("La date de paiement ne peut pas être vide")
        
        url = f"{self.base_url}/v1/bill/{bill_id}"
        payload = {
            "paymentType": payment_type,
            "paymentDate": payment_date_iso
        }
        
        try:
            print(f"[Armado] Mise à jour du paiement: ID={bill_id}, type={payment_type}, date={payment_date_iso}")
            response = self._make_request_with_retry('PUT', url, json=payload)
            
            if response.status_code == 401:
                raise ValueError("API key invalide - vérifiez ARMADO_API_KEY")
            
            if response.status_code == 404:
                raise ValueError(f"Facture avec ID {bill_id} introuvable")
            
            if response.status_code == 422:
                error_data = response.json()
                error_msg = error_data.get('message', 'Erreur de validation')
                raise ValueError(f"Erreur de validation Armado: {error_msg}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"[Armado] Paiement mis à jour avec succès: ID={bill_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"[Armado] Erreur lors de la mise à jour du paiement: {e}")
            raise ValueError(f"Erreur de connexion Armado: {e}")
        except ValueError:
            # Re-raise les ValueError (erreurs métier)
            raise
        except Exception as e:
            print(f"[Armado] Erreur inattendue lors de la mise à jour: {e}")
            raise ValueError(f"Erreur inattendue Armado: {e}")
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Armado
        
        Returns:
            True si la connexion est OK, False sinon
        """
        try:
            # Test simple avec une recherche qui ne devrait pas trouver de résultat
            url = f"{self.base_url}/v1/bill"
            params = {'reference': 'TEST_CONNECTION_12345'}
            
            response = self._make_request_with_retry('GET', url, params=params)
            
            if response.status_code == 401:
                print("[Armado] Test de connexion: API key invalide")
                return False
            
            if response.status_code in [200, 404]:  # 404 est OK pour un test
                print("[Armado] Test de connexion: OK")
                return True
            
            print(f"[Armado] Test de connexion: Erreur {response.status_code}")
            return False
            
        except Exception as e:
            print(f"[Armado] Test de connexion: Erreur {e}")
            return False

if __name__ == "__main__":
    # Test du client
    try:
        client = ArmadoClient()
        print("=== Test du client Armado ===")
        
        # Test de connexion
        if client.test_connection():
            print("✓ Connexion Armado réussie")
        else:
            print("✗ Problème de connexion Armado")
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation du client: {e}")
        print("Vérifiez que ARMADO_API_KEY est définie dans le fichier .env")
