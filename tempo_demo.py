#!/usr/bin/env python3
"""
Script de démonstration pour le client Tempo
Teste les différents cas d'usage des règlements de factures
"""

import argparse
from datetime import datetime
from tempo_client import TempoClient

def demo_reglement_total(tempo_client: TempoClient, id_facture: int, date_reglement: str):
    """Démonstration du règlement total (Cas d'usage A)"""
    print("\n" + "="*60)
    print("CAS D'USAGE A - RÈGLEMENT TOTAL")
    print("="*60)
    
    print(f"Enregistrement du règlement total pour la facture {id_facture}")
    print(f"Date de règlement: {date_reglement}")
    
    # Enregistrer le règlement total
    success = tempo_client.enregistrer_reglement_total(id_facture, date_reglement)
    
    if success:
        print("\n✓ Règlement total enregistré avec succès")
        # Vérifier l'état de la facture
        tempo_client.verifier_facture(id_facture)
    else:
        print("\n✗ Échec de l'enregistrement du règlement total")

def demo_reglement_partiel(tempo_client: TempoClient, id_facture: int, montant: float, date_reglement: str):
    """Démonstration du règlement partiel (Cas d'usage B)"""
    print("\n" + "="*60)
    print("CAS D'USAGE B - RÈGLEMENT PARTIEL")
    print("="*60)
    
    print(f"Enregistrement du règlement partiel pour la facture {id_facture}")
    print(f"Montant: {montant}€")
    print(f"Date de règlement: {date_reglement}")
    
    # Enregistrer le règlement partiel
    success = tempo_client.enregistrer_reglement_partiel(id_facture, montant, date_reglement)
    
    if success:
        print("\n✓ Règlement partiel enregistré avec succès")
        # Vérifier l'état de la facture
        tempo_client.verifier_facture(id_facture)
    else:
        print("\n✗ Échec de l'enregistrement du règlement partiel")

def demo_fixation_total_partiels(tempo_client: TempoClient, id_facture: int, montant_total: float, date_reglement: str):
    """Démonstration de la fixation du total des partiels (Cas d'usage C)"""
    print("\n" + "="*60)
    print("CAS D'USAGE C - FIXATION DU TOTAL DES PARTIELS")
    print("="*60)
    
    print(f"Fixation du total des partiels pour la facture {id_facture}")
    print(f"Montant total: {montant_total}€")
    print(f"Date de règlement: {date_reglement}")
    
    # Fixer le total des partiels
    success = tempo_client.fixer_total_partiels(id_facture, montant_total, date_reglement)
    
    if success:
        print("\n✓ Total des partiels fixé avec succès")
        # Vérifier l'état de la facture
        tempo_client.verifier_facture(id_facture)
    else:
        print("\n✗ Échec de la fixation du total des partiels")

def demo_partiel_plus_solde(tempo_client: TempoClient, id_facture: int, montant: float, date_reglement: str):
    """Démonstration du règlement partiel + solde (Cas d'usage D)"""
    print("\n" + "="*60)
    print("CAS D'USAGE D - PARTIEL + SOLDE")
    print("="*60)
    
    print(f"Enregistrement du règlement partiel + solde pour la facture {id_facture}")
    print(f"Montant: {montant}€")
    print(f"Date de règlement: {date_reglement}")
    
    # Enregistrer le règlement partiel + solde
    success = tempo_client.solder_avec_partiel(id_facture, montant, date_reglement)
    
    if success:
        print("\n✓ Règlement partiel + solde enregistré avec succès")
        # Vérifier l'état de la facture
        tempo_client.verifier_facture(id_facture)
    else:
        print("\n✗ Échec de l'enregistrement du règlement partiel + solde")

def demo_traitement_automatique(tempo_client: TempoClient, id_facture: int, montant: float, date_reglement: str, solder: bool):
    """Démonstration du traitement automatique"""
    print("\n" + "="*60)
    print("TRAITEMENT AUTOMATIQUE")
    print("="*60)
    
    print(f"Traitement automatique pour la facture {id_facture}")
    print(f"Montant: {montant}€")
    print(f"Date: {date_reglement}")
    print(f"Solder: {solder}")
    
    # Traitement automatique
    success = tempo_client.traiter_reglement_automatique(id_facture, montant, date_reglement, solder)
    
    if success:
        print("\n✓ Traitement automatique réussi")
    else:
        print("\n✗ Échec du traitement automatique")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Démonstration du client Tempo')
    parser.add_argument('--id-facture', type=int, required=True, help='Identifiant de la facture')
    parser.add_argument('--montant', type=float, help='Montant du règlement (pour les cas B, C, D)')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y%m%d'), 
                       help='Date de règlement au format AAAAMMJJ (défaut: aujourd\'hui)')
    parser.add_argument('--cas', choices=['A', 'B', 'C', 'D', 'auto'], required=True,
                       help='Cas d\'usage à tester')
    parser.add_argument('--solder', action='store_true', 
                       help='Solder la facture (pour le cas auto)')
    
    args = parser.parse_args()
    
    try:
        # Initialiser le client Tempo
        print("Initialisation du client Tempo...")
        tempo_client = TempoClient()
        print("✓ Client Tempo initialisé")
        
        # Tester la connexion
        print(f"\nTest de connexion avec la facture {args.id_facture}...")
        facture_test = tempo_client.get_facture(args.id_facture)
        if not facture_test:
            print("✗ Impossible de récupérer la facture de test")
            print("Vérifiez l'ID de la facture et votre configuration")
            return
        
        print("✓ Connexion Tempo réussie")
        
        # Exécuter le cas d'usage demandé
        if args.cas == 'A':
            # Cas A: Règlement total
            demo_reglement_total(tempo_client, args.id_facture, args.date)
            
        elif args.cas == 'B':
            # Cas B: Règlement partiel
            if not args.montant:
                print("✗ Le montant est requis pour le cas B")
                return
            demo_reglement_partiel(tempo_client, args.id_facture, args.montant, args.date)
            
        elif args.cas == 'C':
            # Cas C: Fixation du total des partiels
            if not args.montant:
                print("✗ Le montant est requis pour le cas C")
                return
            demo_fixation_total_partiels(tempo_client, args.id_facture, args.montant, args.date)
            
        elif args.cas == 'D':
            # Cas D: Partiel + solde
            if not args.montant:
                print("✗ Le montant est requis pour le cas D")
                return
            demo_partiel_plus_solde(tempo_client, args.id_facture, args.montant, args.date)
            
        elif args.cas == 'auto':
            # Traitement automatique
            if not args.montant:
                print("✗ Le montant est requis pour le traitement automatique")
                return
            demo_traitement_automatique(tempo_client, args.id_facture, args.montant, args.date, args.solder)
        
        print("\n" + "="*60)
        print("DÉMONSTRATION TERMINÉE")
        print("="*60)
        
    except ValueError as e:
        print(f"✗ Erreur de configuration: {e}")
        print("Vérifiez votre fichier .env")
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()
