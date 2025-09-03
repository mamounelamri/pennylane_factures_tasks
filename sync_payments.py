from datetime import datetime
from typing import Dict, Optional
from armado_client import ArmadoClient

# Table de correspondance des types de paiement
# À ajuster selon votre référentiel Armado
PAYMENT_TYPE_MAP = {
    "virement": 2,
    "cb": 3,
    "carte": 3,
    "carte bancaire": 3,
    "cheque": 1,
    "chèque": 1,
    "especes": 4,
    "espèces": 4,
    "liquide": 4,
    "cash": 4,
    "prelevement": 5,
    "prélèvement": 5,
    "sepa": 5,
    "paypal": 6,
    "stripe": 7,
    "autre": 8,
    "other": 8
}

def sync_armado_after_tempo(invoice_reference: str, payment_mode: str, payment_date: datetime) -> Dict:
    """
    Synchronise un paiement Tempo vers Armado après une mise à jour réussie
    
    Args:
        invoice_reference: Numéro de facture Tempo (ex: '20664'), utilisé comme Armado.reference
        payment_mode: Mode de paiement (ex: 'virement', 'cb', 'cheque', etc.)
        payment_date: Date/heure de paiement côté Tempo
        
    Returns:
        Données de la facture Armado mise à jour
        
    Raises:
        ValueError: En cas d'erreur de synchronisation (facture introuvable, type de paiement invalide, etc.)
    """
    if not invoice_reference:
        raise ValueError("La référence de facture ne peut pas être vide")
    
    if not payment_mode:
        raise ValueError("Le mode de paiement ne peut pas être vide")
    
    if not payment_date:
        raise ValueError("La date de paiement ne peut pas être vide")
    
    print(f"[Sync] Début de la synchronisation Armado pour la facture {invoice_reference}")
    print(f"[Sync] Mode de paiement: {payment_mode}, Date: {payment_date}")
    
    try:
        # Initialiser le client Armado
        client = ArmadoClient()
        
        # 1. Trouver la facture Armado par sa référence
        bill_id = client.find_bill_id_by_reference(invoice_reference)
        if not bill_id:
            raise ValueError(f"Armado: facture avec référence '{invoice_reference}' introuvable")
        
        # 2. Mapper le mode de paiement vers le type Armado
        payment_type = PAYMENT_TYPE_MAP.get(payment_mode.lower())
        if payment_type is None:
            available_modes = list(PAYMENT_TYPE_MAP.keys())
            raise ValueError(f"Armado: paymentType introuvable pour mode '{payment_mode}'. Modes disponibles: {available_modes}")
        
        # 3. Formater la date pour Armado (format ISO avec microsecondes)
        payment_date_iso = payment_date.strftime("%Y-%m-%dT%H:%M:%S.000000")
        
        # 4. Mettre à jour le paiement sur Armado
        result = client.update_bill_payment(bill_id, payment_type, payment_date_iso)
        
        print(f"[Sync] ✓ Synchronisation réussie: bill_id={bill_id}, paymentType={payment_type}, paymentDate={payment_date_iso}")
        return result
        
    except ValueError as e:
        # Re-raise les erreurs métier avec un message clair
        error_msg = f"Erreur de synchronisation Armado: {e}"
        print(f"[Sync] ✗ {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        # Capturer les autres erreurs inattendues
        error_msg = f"Erreur inattendue lors de la synchronisation Armado: {e}"
        print(f"[Sync] ✗ {error_msg}")
        raise ValueError(error_msg)

def get_available_payment_modes() -> list:
    """
    Retourne la liste des modes de paiement supportés
    
    Returns:
        Liste des modes de paiement disponibles
    """
    return list(PAYMENT_TYPE_MAP.keys())

def add_payment_mode_mapping(mode: str, payment_type: int) -> None:
    """
    Ajoute un nouveau mapping de mode de paiement
    
    Args:
        mode: Mode de paiement (ex: 'nouveau_mode')
        payment_type: Type de paiement Armado (ex: 9)
    """
    PAYMENT_TYPE_MAP[mode.lower()] = payment_type
    print(f"[Sync] Nouveau mapping ajouté: '{mode}' -> {payment_type}")

def test_armado_connection() -> bool:
    """
    Teste la connexion à l'API Armado
    
    Returns:
        True si la connexion est OK, False sinon
    """
    try:
        client = ArmadoClient()
        return client.test_connection()
    except Exception as e:
        print(f"[Sync] Erreur lors du test de connexion Armado: {e}")
        return False

def sync_with_error_handling(invoice_reference: str, payment_mode: str, payment_date: datetime) -> Dict:
    """
    Version de synchronisation avec gestion d'erreur non-bloquante
    
    Cette fonction ne lève pas d'exception mais retourne un résultat avec le statut
    
    Args:
        invoice_reference: Numéro de facture Tempo
        payment_mode: Mode de paiement
        payment_date: Date de paiement
        
    Returns:
        Dict avec 'success', 'data' et 'error' keys
    """
    try:
        result = sync_armado_after_tempo(invoice_reference, payment_mode, payment_date)
        return {
            'success': True,
            'data': result,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }

if __name__ == "__main__":
    # Test du module de synchronisation
    print("=== Test du module de synchronisation Armado ===")
    
    # Test de connexion
    if test_armado_connection():
        print("✓ Connexion Armado OK")
    else:
        print("✗ Problème de connexion Armado")
    
    # Afficher les modes de paiement disponibles
    print(f"\nModes de paiement disponibles: {get_available_payment_modes()}")
    
    # Test de synchronisation (avec des données fictives)
    print("\nTest de synchronisation (données fictives):")
    try:
        # Ce test va échouer car la facture n'existe pas, mais on peut voir le comportement
        test_result = sync_with_error_handling(
            invoice_reference="TEST_12345",
            payment_mode="virement",
            payment_date=datetime.now()
        )
        
        if test_result['success']:
            print("✓ Test de synchronisation réussi")
        else:
            print(f"✗ Test de synchronisation échoué (attendu): {test_result['error']}")
            
    except Exception as e:
        print(f"Erreur lors du test: {e}")
