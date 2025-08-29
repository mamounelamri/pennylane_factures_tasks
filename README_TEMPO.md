# Intégration Tempo - Automatisation des Règlements de Factures

## Vue d'ensemble

Cette intégration automatise l'enregistrement des règlements de factures dans Tempo basé sur les données de Pennylane. Elle gère tous les cas d'usage des règlements selon les spécifications Tempo.

## Fonctionnalités

### Cas d'usage supportés

- **Cas A** : Règlement total d'une facture
- **Cas B** : Règlement partiel (ajout d'un versement)
- **Cas C** : Fixation du total des partiels (écraser le cumul)
- **Cas D** : Règlement partiel + solde de la facture

### Fonctionnalités principales

- ✅ Authentification Basic Auth automatique
- ✅ Formatage automatique des dates (AAAAMMJJ)
- ✅ Gestion des montants avec décimales
- ✅ Vérification automatique des factures après règlement
- ✅ Intégration avec Pennylane pour la détection des paiements
- ✅ Traitement automatique des factures payées quotidiennement
- ✅ Suivi des règlements déjà traités
- ✅ Mode planifié (tous les midis à 12h00)
- ✅ **Alertes email automatiques en cas d'erreur**
- ✅ **Résumés d'intégration par email**
- ✅ **Intégration Office365 identique à dan-interim-app**

## Installation

### 1. Dépendances

Les dépendances sont déjà incluses dans `requirements.txt` :
```bash
pip install -r requirements.txt
```

### 2. Configuration

Créez un fichier `.env` basé sur `tempo_config_example.txt` :

```bash
# Configuration Tempo
TEMPO_BASE_URL=https://<host>/API/Tempo
TEMPO_DOSSIER=DAN02
TEMPO_USERNAME=votre_identifiant
TEMPO_PASSWORD=votre_mot_de_passe

# Configuration Office365 (même que dan-interim-app)
OFFICE365_USER=your-email@yourdomain.com
OFFICE365_PASSWORD=your-app-password
OFFICE365_SENDER=your-email@yourdomain.com
OFFICE365_SENDER_NAME=Intégration Tempo

# Destinataires des alertes Tempo (séparés par des virgules)
TEMPO_ALERT_EMAILS=admin@yourdomain.com,comptabilite@yourdomain.com

# Configuration Pennylane (existante)
PENNYLANE_API_KEY=votre_cle_api_pennylane

# Configuration Google Sheets (existante)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=votre_spreadsheet_id
```

## Utilisation

### 1. Test des fonctionnalités Tempo

Utilisez le script de démonstration pour tester les différents cas d'usage :

```bash
# Règlement total (Cas A)
python tempo_demo.py --id-facture 20653 --cas A --date 20250828

# Règlement partiel (Cas B)
python tempo_demo.py --id-facture 20653 --cas B --montant 795.60 --date 20250828

# Fixation du total des partiels (Cas C)
python tempo_demo.py --id-facture 20653 --cas C --montant 795.60 --date 20250828

# Partiel + solde (Cas D)
python tempo_demo.py --id-facture 20653 --cas D --montant 795.60 --date 20250828

# Traitement automatique
python tempo_demo.py --id-facture 20653 --cas auto --montant 795.60 --date 20250828 --solder
```

### 2. Intégration automatique Pennylane-Tempo

L'intégration automatique traite les factures payées quotidiennement :

```bash
# Exécution unique
python tempo_integration.py --once

# Mode planifié (tous les midis)
python tempo_integration.py --scheduled

# Mode automatique (GitHub Actions)
python tempo_integration.py --auto
```

### 3. Utilisation programmatique

```python
from tempo_client import TempoClient

# Initialiser le client
tempo = TempoClient()

# Règlement total
success = tempo.enregistrer_reglement_total(20653, "20250828")

# Règlement partiel
success = tempo.enregistrer_reglement_partiel(20653, 795.60, "20250828")

# Vérifier l'état
facture = tempo.get_facture(20653)
```

## Architecture

### Fichiers principaux

- **`tempo_client.py`** : Client API Tempo avec tous les cas d'usage
- **`tempo_demo.py`** : Script de démonstration et tests
- **`tempo_integration.py`** : Intégration automatique Pennylane-Tempo
- **`tempo_email_client.py`** : Client email Office365 pour les alertes
- **`test_tempo_email.py`** : Script de test des emails d'alerte
- **`tempo_config_example.txt`** : Exemple de configuration
- **`tempo_email_config_example.txt`** : Exemple de configuration email

### Classes principales

#### TempoClient
Gère toutes les interactions avec l'API Tempo :
- Authentification Basic Auth
- Formatage des dates AAAAMMJJ
- Gestion des différents types de règlements
- Vérification des factures

#### TempoIntegration
Intègre Pennylane et Tempo :
- Détection automatique des factures payées
- Extraction des numéros de facture
- Traitement automatique des règlements
- Suivi des règlements traités

## Cas d'usage détaillés

### Cas A - Paiement TOTAL
```python
# Marque la facture comme "Payée"
tempo.enregistrer_reglement_total(20653, "20250828")
```

**Payload envoyé :**
```json
{
  "IdFacture": 20653,
  "RegleeTotale": "OUI",
  "DateReglementTotal": "20250828"
}
```

### Cas B - Paiement PARTIEL
```python
# Ajoute un versement partiel
tempo.enregistrer_reglement_partiel(20653, 795.60, "20250828")
```

**Payload envoyé :**
```json
{
  "IdFacture": 20653,
  "MontantReglementPartiel": 795.60,
  "DateReglementTotal": "20250828"
}
```

### Cas C - Fixer le TOTAL des partiels
```python
# Fixe le total des partiels (écrase le cumul)
tempo.fixer_total_partiels(20653, 795.60, "20250828")
```

**Payload envoyé :**
```json
{
  "IdFacture": 20653,
  "MontantReglementPartielTotal": 795.60,
  "DateReglementTotal": "20250828"
}
```

### Cas D - Partiel + solder
```python
# Règlement partiel + solde de la facture
tempo.solder_avec_partiel(20653, 795.60, "20250828")
```

**Payload envoyé :**
```json
{
  "IdFacture": 20653,
  "MontantReglementPartielTotal": 795.60,
  "RegleeTotale": "OUI",
  "DateReglementTotal": "20250828"
}
```

## Règles métier importantes

1. **Pour que l'UI Tempo affiche "Payée"** : 
   - Il faut poser le flag `RegleeTotale="OUI"` + `DateReglementTotal`

2. **Si seul un montant est envoyé** :
   - L'UI peut rester "non soldée" tant que `RegleeTotale` n'est pas "OUI"

3. **`MontantReglementPartielTotal`** :
   - PRIME sur `MontantReglementPartiel`
   - Remplace le cumul calculé

4. **Format des dates** :
   - Strictement AAAAMMJJ (ex: 20250828)

5. **Format des montants** :
   - Décimales avec point (ex: 795.60)

## Dépannage

### Erreurs courantes

1. **Erreur de configuration** :
   ```
   ValueError: Configuration Tempo manquante dans le fichier .env
   ```
   → Vérifiez que toutes les variables Tempo sont définies

2. **Erreur d'authentification** :
   ```
   Erreur lors de la récupération de la facture: 401
   ```
   → Vérifiez vos identifiants Tempo

3. **Facture introuvable** :
   ```
   Impossible de récupérer la facture de test
   ```
   → Vérifiez l'ID de la facture et votre dossier Tempo

### Logs et débogage

Le client Tempo génère des logs détaillés :
- URL des requêtes
- Payloads envoyés
- Codes de réponse
- Contenu des réponses
- Comparaison des états avant/après

## Sécurité

- Les identifiants sont stockés dans le fichier `.env` (non versionné)
- Authentification Basic Auth avec encodage Base64
- Aucun identifiant en dur dans le code
- Validation des paramètres d'entrée

## Performance

- Délai de 1 seconde entre les traitements (évite les quotas)
- Traitement par lot des factures payées quotidiennement
- Suivi des règlements déjà traités (évite les doublons)
- Mode planifié optimisé (vérification toutes les minutes)

## Alertes Email Automatiques

### 🚨 Types d'alertes

L'intégration Tempo envoie automatiquement des emails d'alerte en cas de problème :

1. **Facture introuvable** : Quand une facture n'existe pas dans Tempo
2. **Échec de règlement** : Quand l'enregistrement d'un règlement échoue
3. **Résumé d'intégration** : Bilan quotidien des opérations (succès + erreurs)

### 📧 Configuration des alertes

Ajoutez ces variables dans votre `.env` :

```bash
# Configuration Office365 (même que dan-interim-app)
OFFICE365_USER=your-email@yourdomain.com
OFFICE365_PASSWORD=your-app-password
OFFICE365_SENDER=your-email@yourdomain.com
OFFICE365_SENDER_NAME=Intégration Tempo

# Destinataires des alertes (séparés par des virgules)
TEMPO_ALERT_EMAILS=admin@yourdomain.com,comptabilite@yourdomain.com
```

### 🧪 Test des alertes

Testez l'envoi d'emails avec :

```bash
# Test complet des alertes
python test_tempo_email.py

# Test avec un destinataire spécifique
python test_tempo_email.py --recipient test@yourdomain.com

# Test sans vérification de connexion
python test_tempo_email.py --skip-connection
```

### 📊 Exemple de résumé d'intégration

Chaque jour, vous recevrez un email avec :
- Nombre de règlements traités avec succès
- Nombre d'erreurs rencontrées
- Taux de succès
- Détail de chaque opération avec statut

## Support

Pour toute question ou problème :
1. Vérifiez les logs de débogage
2. Testez avec le script de démonstration
3. Vérifiez votre configuration Tempo
4. Testez l'envoi d'emails avec `test_tempo_email.py`
5. Consultez la documentation de l'API Tempo
