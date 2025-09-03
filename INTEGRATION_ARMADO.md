# Intégration Armado - Synchronisation des Paiements

Ce document explique comment intégrer la synchronisation Armado après les mises à jour de paiement Tempo.

## Vue d'ensemble

L'intégration permet de synchroniser automatiquement les paiements de Tempo vers Armado **uniquement** quand une facture est **complètement payée**.

### Flux de synchronisation

1. **Mise à jour Tempo** : `FACTUREREGLEMENT` → Code 200
2. **Vérification statut** : Facture complètement payée ? (pas de paiement partiel)
3. **Recherche Armado** : Trouver la facture par référence (numéro Tempo)
4. **Mise à jour Armado** : `PUT /v1/bill/:id` avec `paymentType` et `paymentDate`

### Comportement

- ✅ **Facture complètement payée** → Synchronisation Armado
- ❌ **Facture partiellement payée** → Pas de synchronisation Armado
- ✅ **Google Sheets** → Toujours mis à jour (payée ou partiellement payée)

## Fichiers créés

- `armado_client.py` : Client HTTP pour l'API Armado
- `sync_payments.py` : Module de synchronisation principal
- `test_armado_integration.py` : Tests unitaires
- `tempo_armado_integration_example.py` : Exemple d'intégration complète
- `env_example.txt` : Variables d'environnement nécessaires

## Configuration

### Variables d'environnement

Ajoutez ces variables à votre fichier `.env` :

```bash
# Configuration Armado
ARMADO_API_KEY=your_armado_api_key_here
ARMADO_BASE_URL=https://api.myarmado.fr
ARMADO_TIMEOUT=10
```

### Types de paiement supportés

```python
PAYMENT_TYPE_MAP = {
    "virement": 2,
    "cb": 3,
    "carte": 3,
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
```

## Utilisation

### Intégration simple

```python
from datetime import datetime
from sync_payments import sync_armado_after_tempo

# Après une mise à jour Tempo réussie
tempo_invoice_number = "20664"  # Numéro de facture Tempo
payment_mode = "virement"       # Mode de paiement
payment_date = datetime.now()   # Date de paiement

try:
    armado_result = sync_armado_after_tempo(
        tempo_invoice_number, 
        payment_mode, 
        payment_date
    )
    print(f"[Armado] OK: bill id={armado_result.get('id')}")
except Exception as e:
    print(f"[Armado] ERREUR: {e}")
```

### Intégration avec gestion d'erreur non-bloquante

```python
from sync_payments import sync_with_error_handling

result = sync_with_error_handling(
    invoice_reference="20664",
    payment_mode="virement",
    payment_date=datetime.now()
)

if result['success']:
    print(f"✓ Synchronisation réussie: {result['data']}")
else:
    print(f"✗ Erreur: {result['error']}")
    # Ne bloque pas le flux principal Tempo
```

### Intégration dans votre flux existant

Modifiez votre code de traitement des paiements Tempo :

```python
# Dans votre fonction de traitement Tempo
def process_tempo_payment(invoice_number, payment_data):
    # 1. Mise à jour Tempo
    tempo_response = update_tempo_payment(invoice_number, payment_data)
    
    if tempo_response.status_code == 200:
        # 2. Synchronisation Armado (non-bloquante)
        try:
            from sync_payments import sync_with_error_handling
            
            armado_result = sync_with_error_handling(
                invoice_reference=invoice_number,
                payment_mode=payment_data.get('mode', 'virement'),
                payment_date=datetime.now()
            )
            
            if armado_result['success']:
                print(f"[Armado] ✓ Synchronisé: {invoice_number}")
            else:
                print(f"[Armado] ✗ Erreur: {armado_result['error']}")
                # Optionnel: logger l'erreur pour retry plus tard
                
        except Exception as e:
            print(f"[Armado] ✗ Erreur inattendue: {e}")
            # Ne pas faire échouer le traitement Tempo
    
    return tempo_response
```

## Gestion des erreurs

### Erreurs courantes

- **401 Unauthorized** : API key invalide
- **404 Not Found** : Facture introuvable sur Armado
- **422 Unprocessable Entity** : Données invalides (type de paiement, format de date)

### Stratégie de retry

Le client Armado inclut un système de retry automatique pour les erreurs 5xx :

- 3 tentatives maximum
- Backoff exponentiel : 0.5s, 1s, 2s
- Les erreurs 4xx ne sont pas retentées

### Logging et monitoring

```python
# Exemple de logging détaillé
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_with_logging(invoice_reference, payment_mode, payment_date):
    logger.info(f"Début synchronisation Armado: {invoice_reference}")
    
    try:
        result = sync_armado_after_tempo(invoice_reference, payment_mode, payment_date)
        logger.info(f"Synchronisation réussie: {result}")
        return result
    except ValueError as e:
        logger.error(f"Erreur de synchronisation: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        raise
```

## Tests

### Tests unitaires

```bash
python -m pytest test_armado_integration.py -v
```

### Test de connexion

```python
from sync_payments import test_armado_connection

if test_armado_connection():
    print("✓ Connexion Armado OK")
else:
    print("✗ Problème de connexion Armado")
```

### Test avec données réelles

```python
from armado_client import ArmadoClient

client = ArmadoClient()

# Test de recherche
bill_id = client.find_bill_id_by_reference("20664")
print(f"Facture trouvée: {bill_id}")

# Test de mise à jour (attention: modifie les données réelles)
if bill_id:
    result = client.update_bill_payment(
        bill_id, 
        2,  # virement
        "2024-01-15T10:30:00.000000"
    )
    print(f"Mise à jour: {result}")
```

## Déploiement

### Variables d'environnement en production

```bash
# Production
ARMADO_API_KEY=prod_api_key_here
ARMADO_BASE_URL=https://api.myarmado.fr
ARMADO_TIMEOUT=15
```

### Monitoring

Surveillez les logs pour détecter :

- Taux d'erreur de synchronisation
- Factures non trouvées sur Armado
- Erreurs d'API key
- Timeouts

### File de retry (optionnel)

Pour les cas où la synchronisation échoue, vous pouvez implémenter une file de retry :

```python
import json
from datetime import datetime

def queue_failed_sync(invoice_reference, payment_mode, payment_date, error):
    """Ajoute une synchronisation échouée à la file de retry"""
    retry_item = {
        'invoice_reference': invoice_reference,
        'payment_mode': payment_mode,
        'payment_date': payment_date.isoformat(),
        'error': error,
        'timestamp': datetime.now().isoformat(),
        'retry_count': 0
    }
    
    # Sauvegarder dans un fichier ou base de données
    with open('armado_retry_queue.json', 'a') as f:
        f.write(json.dumps(retry_item) + '\n')

def process_retry_queue():
    """Traite la file de retry"""
    # Implémentation du retry des synchronisations échouées
    pass
```

## Support et maintenance

### Ajout de nouveaux types de paiement

```python
from sync_payments import add_payment_mode_mapping

# Ajouter un nouveau mode
add_payment_mode_mapping('nouveau_mode', 9)
```

### Debugging

Activez les logs détaillés :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Mise à jour de l'API

Si l'API Armado évolue, modifiez les endpoints dans `armado_client.py` :

```python
# Exemple de modification d'endpoint
def find_bill_id_by_reference(self, reference: str) -> Optional[int]:
    # Nouveau endpoint si nécessaire
    url = f"{self.base_url}/v2/bills"  # v2 au lieu de v1
    # ...
```

## Sécurité

- Stockez l'API key dans les variables d'environnement
- Ne commitez jamais l'API key dans le code
- Utilisez HTTPS pour toutes les communications
- Limitez les permissions de l'API key Armado si possible
