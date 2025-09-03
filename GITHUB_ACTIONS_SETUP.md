# Configuration GitHub Actions

Ce guide explique comment configurer l'exécution automatique de la synchronisation Pennylane-Google Sheets-Armado via GitHub Actions.

## Prérequis

1. **Repository GitHub** : Le code doit être dans un repository GitHub
2. **Secrets GitHub** : Configuration des variables sensibles

## Configuration des Secrets GitHub

Dans votre repository GitHub, allez dans **Settings > Secrets and variables > Actions** et ajoutez les secrets suivants :

### Option 1 : Secrets au niveau du repository
Ajoutez les secrets directement dans **Repository secrets**.

### Option 2 : Secrets dans un environnement (recommandé)
Créez un environnement "production" dans **Environments** et configurez :

**Secrets** (données sensibles) :
- `PENNYLANE_API_KEY`
- `ARMADO_API_KEY` 
- `ARMADO_BASE_URL`
- `ARMADO_TIMEOUT`
- `GOOGLE_CREDENTIALS`

**Variables** (données non-sensibles) :
- `SPREADSHEET_ID`
- `SPREADSHEET_NAME`

Le workflow est configuré pour utiliser l'environnement "production".

### 1. PENNYLANE_API_KEY
Votre clé API Pennylane v2

### 2. SPREADSHEET_ID
L'ID de votre Google Spreadsheet (ex: `1q5xhrst1VyHbym3960K31BuuUI_yLA5c2qNUPBX6GSU`)

### 3. SPREADSHEET_NAME
Le nom de la feuille dans votre spreadsheet (ex: `Tâches à réaliser`)

### 4. GOOGLE_CREDENTIALS
Le contenu complet de votre fichier `credentials.json` Google Service Account

### 5. ARMADO_API_KEY
Votre clé API Armado pour la synchronisation des paiements

### 6. ARMADO_BASE_URL (optionnel)
URL de base de l'API Armado (par défaut: `https://api.myarmado.fr`)

### 7. ARMADO_TIMEOUT (optionnel)
Timeout pour les requêtes Armado en secondes (par défaut: `10`)

## Configuration du Service Account Google

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un projet ou sélectionnez un projet existant
3. Activez les APIs :
   - Google Sheets API
   - Google Drive API
4. Créez un Service Account :
   - IAM & Admin > Service Accounts
   - Créez un nouveau service account
   - Téléchargez le fichier JSON
5. Partagez votre Google Spreadsheet avec l'email du service account

## Structure du Workflow

Le workflow `.github/workflows/pennylane-sync.yml` :

- **Déclenchement** : Tous les jours à 12h00 heure française (11h00 UTC)
- **Exécution manuelle** : Possible via l'interface GitHub avec option mode test
- **Environnement** : Ubuntu latest avec Python 3.11
- **Fonctionnalités** :
  - Synchronisation Pennylane → Google Sheets
  - Synchronisation Pennylane → Armado (paiements)
  - Mode test pour désactiver la synchronisation Armado

## Exécution

### Automatique
Le workflow s'exécute automatiquement tous les jours à 12h00.

### Manuelle
1. Allez dans l'onglet **Actions** de votre repository
2. Sélectionnez le workflow "Synchronisation Pennylane - Google Sheets - Armado"
3. Cliquez sur **Run workflow**
4. Optionnel : Activez le mode test pour désactiver la synchronisation Armado

## Monitoring

### Logs
- Consultez les logs dans l'onglet **Actions** de GitHub
- Chaque exécution génère des logs détaillés

### Notifications
- Les échecs sont automatiquement notifiés
- Vous pouvez configurer des notifications Slack/Email

## Dépannage

### Erreurs courantes

1. **Erreur d'authentification Google**
   - Vérifiez que le fichier credentials.json est correct
   - Vérifiez que le service account a accès au spreadsheet

2. **Erreur API Pennylane**
   - Vérifiez que la clé API est valide
   - Vérifiez les permissions de l'API

3. **Erreur de variables d'environnement**
   - Vérifiez que tous les secrets sont configurés
   - Vérifiez les noms des secrets

4. **Erreur de synchronisation Armado**
   - Vérifiez que ARMADO_API_KEY est valide
   - Vérifiez la connectivité réseau vers api.myarmado.fr
   - Utilisez le mode test pour diagnostiquer

### Test local

Avant de déployer sur GitHub Actions, testez localement :

```bash
# Test avec le mode automatique
python3 main.py --auto

# Test avec le mode test (désactive Armado)
python3 main.py --auto --test-mode

# Test de connexion Armado
python3 test_quick_armado.py
```

## Sécurité

- Les credentials sont automatiquement nettoyés après chaque exécution
- Les secrets GitHub sont chiffrés
- Aucune donnée sensible n'est stockée dans le code

## Maintenance

### Mise à jour des dépendances
Le workflow utilise `requirements.txt` pour installer les dépendances.

### Mise à jour du code
Poussez simplement les modifications sur la branche principale.

### Monitoring des coûts
- GitHub Actions : Gratuit pour les repositories publics
- Google APIs : Gratuit dans les limites usuelles 