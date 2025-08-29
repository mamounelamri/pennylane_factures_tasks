import os
import base64
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Union
from dotenv import load_dotenv

# Import optionnel pour éviter les erreurs si le client email n'est pas configuré
try:
    from tempo_email_client import TempoEmailClient
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    TempoEmailClient = None

load_dotenv()

class TempoClient:
    """Client pour l'API Tempo - Gestion des règlements de factures"""
    
    def __init__(self):
        self.base_url = os.getenv('TEMPO_BASE_URL')
        self.dossier = os.getenv('TEMPO_DOSSIER')
        self.username = os.getenv('TEMPO_USERNAME')
        self.password = os.getenv('TEMPO_PASSWORD')
        
        if not all([self.base_url, self.dossier, self.username, self.password]):
            raise ValueError("Configuration Tempo manquante dans le fichier .env")
        
        # Supprimer le / final de l'URL si présent
        if self.base_url.endswith('/'):
            self.base_url = self.base_url.rstrip('/')
        
        # Initialiser le client email si disponible
        self.email_client = None
        if EMAIL_AVAILABLE:
            try:
                self.email_client = TempoEmailClient()
                print("✅ Client email Office365 initialisé")
            except Exception as e:
                print(f"⚠ Client email non disponible: {e}")
                self.email_client = None
    
    def _get_auth_header(self) -> str:
        """Génère l'en-tête d'authentification Basic Auth"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Retourne les en-têtes HTTP nécessaires"""
        return {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/json'
        }
    
    def _format_date_aaaammjj(self, date_obj: datetime) -> str:
        """Formate une date au format AAAAMMJJ requis par Tempo"""
        return date_obj.strftime('%Y%m%d')
    
    def _parse_date_aaaammjj(self, date_str: str) -> datetime:
        """Parse une date au format AAAAMMJJ"""
        return datetime.strptime(date_str, '%Y%m%d')
    
    def get_facture(self, id_facture: int) -> Optional[Dict]:
        """
        Récupère les informations d'une facture
        
        Args:
            id_facture: Identifiant de la facture
            
        Returns:
            Dict contenant les informations de la facture ou None en cas d'erreur
        """
        try:
            url = f"{self.base_url}/FACTURE?Dossier={self.dossier}&ID={id_facture}"
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur lors de la récupération de la facture {id_facture}: {response.status_code}")
                if response.text:
                    print(f"Réponse: {response.text}")
                
                # Pas d'alerte email immédiate - seulement le résumé quotidien
                # if self.email_client and response.status_code == 404:
                #     self.email_client.send_facture_not_found_alert(
                #         id_facture, self.dossier, self.base_url, 
                #         f"HTTP {response.status_code} - {response.text}"
                #     )
                
                return None
                
        except Exception as e:
            print(f"Erreur lors de la récupération de la facture {id_facture}: {e}")
            
            # Pas d'alerte email immédiate - seulement le résumé quotidien
            # if self.email_client:
            #     self.email_client.send_facture_not_found_alert(
            #         id_facture, self.dossier, self.base_url, 
            #         f"Exception: {str(e)}"
            #     )
            
            return None
    
    def enregistrer_reglement_total(self, id_facture: int, date_reglement: Union[str, datetime]) -> bool:
        """
        Enregistre un règlement total d'une facture (Cas d'usage A)
        
        Args:
            id_facture: Identifiant de la facture
            date_reglement: Date de règlement (format AAAAMMJJ ou datetime)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Formater la date si nécessaire
            if isinstance(date_reglement, datetime):
                date_reglement = self._format_date_aaaammjj(date_reglement)
            
            payload = {
                "IdFacture": id_facture,
                "RegleeTotale": "OUI",
                "DateReglementTotal": date_reglement
            }
            
            return self._post_reglement(payload, "règlement total")
            
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du règlement total: {e}")
            return False
    
    def enregistrer_reglement_partiel(self, id_facture: int, montant: float, 
                                    date_reglement: Optional[Union[str, datetime]] = None) -> bool:
        """
        Enregistre un règlement partiel d'une facture (Cas d'usage B)
        
        Args:
            id_facture: Identifiant de la facture
            montant: Montant du règlement partiel
            date_reglement: Date de règlement optionnelle (format AAAAMMJJ ou datetime)
            
        Returns:
            True si succès, False sinon
        """
        try:
            payload = {
                "IdFacture": id_facture,
                "MontantReglementPartiel": montant
            }
            
            # Ajouter la date si fournie
            if date_reglement:
                if isinstance(date_reglement, datetime):
                    date_reglement = self._format_date_aaaammjj(date_reglement)
                payload["DateReglementTotal"] = date_reglement
            
            return self._post_reglement(payload, "règlement partiel")
            
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du règlement partiel: {e}")
            return False
    
    def fixer_total_partiels(self, id_facture: int, montant_total: float,
                           date_reglement: Optional[Union[str, datetime]] = None) -> bool:
        """
        Fixe le total des règlements partiels (Cas d'usage C)
        
        Args:
            id_facture: Identifiant de la facture
            montant_total: Montant total des partiels à fixer
            date_reglement: Date de règlement optionnelle (format AAAAMMJJ ou datetime)
            
        Returns:
            True si succès, False sinon
        """
        try:
            payload = {
                "IdFacture": id_facture,
                "MontantReglementPartielTotal": montant_total
            }
            
            # Ajouter la date si fournie
            if date_reglement:
                if isinstance(date_reglement, datetime):
                    date_reglement = self._format_date_aaaammjj(date_reglement)
                payload["DateReglementTotal"] = date_reglement
            
            return self._post_reglement(payload, "fixation du total des partiels")
            
        except Exception as e:
            print(f"Erreur lors de la fixation du total des partiels: {e}")
            return False
    
    def solder_avec_partiel(self, id_facture: int, montant: float, 
                           date_reglement: Union[str, datetime]) -> bool:
        """
        Enregistre un règlement partiel et solde la facture (Cas d'usage D)
        
        Args:
            id_facture: Identifiant de la facture
            montant: Montant du règlement
            date_reglement: Date de règlement (format AAAAMMJJ ou datetime)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Formater la date si nécessaire
            if isinstance(date_reglement, datetime):
                date_reglement = self._format_date_aaaammjj(date_reglement)
            
            payload = {
                "IdFacture": id_facture,
                "MontantReglementPartielTotal": montant,
                "RegleeTotale": "OUI",
                "DateReglementTotal": date_reglement
            }
            
            return self._post_reglement(payload, "règlement partiel + solde")
            
        except Exception as e:
            print(f"Erreur lors du règlement partiel + solde: {e}")
            return False
    
    def _post_reglement(self, payload: Dict, operation_type: str) -> bool:
        """
        Effectue la requête POST pour enregistrer un règlement
        
        Args:
            payload: Données du règlement
            operation_type: Description de l'opération pour les logs
            
        Returns:
            True si succès, False sinon
        """
        try:
            url = f"{self.base_url}/FACTUREREGLEMENT?Dossier={self.dossier}"
            
            print(f"Envoi du {operation_type} pour la facture {payload['IdFacture']}...")
            print(f"URL: {url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            
            print(f"Réponse: {response.status_code}")
            if response.text:
                print(f"Contenu: {response.text}")
            
            if response.status_code == 200:
                print(f"✓ {operation_type} enregistré avec succès")
                return True
            else:
                print(f"✗ Erreur lors du {operation_type}: {response.status_code}")
                
                # Pas d'alerte email immédiate - seulement le résumé quotidien
                # if self.email_client:
                #     self.email_client.send_reglement_failed_alert(
                #         payload['IdFacture'], operation_type,
                #         f"HTTP {response.status_code} - {response.text}",
                #         payload
                #     )
                
                return False
                
        except Exception as e:
            print(f"Erreur lors de la requête POST: {e}")
            
            # Pas d'alerte email immédiate - seulement le résumé quotidien
            # if self.email_client:
            #     self.email_client.send_reglement_failed_alert(
            #         payload['IdFacture'], operation_type,
            #         f"Exception: {str(e)}",
            #         payload
            #     )
            
            return False
    
    def verifier_facture(self, id_facture: int) -> Optional[Dict]:
        """
        Vérifie l'état d'une facture après règlement
        
        Args:
            id_facture: Identifiant de la facture
            
        Returns:
            Dict contenant l'état de la facture ou None en cas d'erreur
        """
        print(f"\nVérification de la facture {id_facture}...")
        
        facture = self.get_facture(id_facture)
        if facture:
            print("✓ Facture récupérée avec succès")
            print(f"Contenu: {json.dumps(facture, indent=2)}")
            return facture
        else:
            print("✗ Impossible de récupérer la facture")
            return None
    
    def traiter_reglement_automatique(self, id_facture: int, montant: float, 
                                    date_reglement: Union[str, datetime],
                                    solder_facture: bool = False) -> bool:
        """
        Traite automatiquement un règlement selon les règles métier
        
        Args:
            id_facture: Identifiant de la facture
            montant: Montant du règlement
            date_reglement: Date de règlement
            solder_facture: Si True, solde la facture (RegleeTotale="OUI")
            
        Returns:
            True si succès, False sinon
        """
        try:
            print(f"\n=== Traitement automatique du règlement ===")
            print(f"Facture: {id_facture}")
            print(f"Montant: {montant}")
            print(f"Date: {date_reglement}")
            print(f"Solder: {solder_facture}")
            
            # Récupérer l'état actuel de la facture
            facture_avant = self.get_facture(id_facture)
            if not facture_avant:
                print("✗ Impossible de récupérer l'état initial de la facture")
                return False
            
            print(f"État initial de la facture récupéré")
            
            # Déterminer le type de règlement
            if solder_facture:
                # Cas D: Partiel + solder
                success = self.solder_avec_partiel(id_facture, montant, date_reglement)
            else:
                # Cas B: Règlement partiel simple
                success = self.enregistrer_reglement_partiel(id_facture, montant, date_reglement)
            
            if not success:
                print("✗ Échec de l'enregistrement du règlement")
                return False
            
            # Vérifier l'état après règlement
            print("\nVérification de l'état après règlement...")
            facture_apres = self.get_facture(id_facture)
            
            if facture_apres:
                print("✓ État après règlement récupéré")
                print("Comparaison des états:")
                print(f"  - Avant: {json.dumps(facture_avant, indent=2)}")
                print(f"  - Après: {json.dumps(facture_apres, indent=2)}")
            else:
                print("⚠ Impossible de récupérer l'état après règlement")
            
            return True
            
        except Exception as e:
            print(f"Erreur lors du traitement automatique: {e}")
            return False
