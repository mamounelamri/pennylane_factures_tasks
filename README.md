# Intégration Pennylane - Google Sheets :

Ce projet surveille automatiquement les factures et avoirs payés dans Pennylane et crée des tâches correspondantes dans Google Sheets.

## Fonctionnalités

- Surveillance des factures et avoirs passés en statut "payé" dans Pennylane
- Création automatique de tâches dans Google Sheets avec :
  - Numéro (tempo) et nom du client
  - Numéro de la facture
  - Date de la facture
  - Date de règlement
  - Montant du règlement
- Gestion spéciale des factures partiellement payées

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurer les variables d'environnement dans `.env` :
```
PENNYLANE_API_KEY=votre_clé_api_pennylane
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=votre_id_spreadsheet
```

3. Configurer l'authentification Google Sheets (voir section Configuration)

## Configuration

### Pennylane API
- Obtenir une clé API depuis votre compte Pennylane
- Ajouter la clé dans le fichier `.env`

### Google Sheets
1. Créer un projet dans Google Cloud Console
2. Activer l'API Google Sheets
3. Créer un compte de service et télécharger le fichier credentials.json
4. Partager votre Google Sheet avec l'email du compte de service

## Utilisation

```bash
python main.py
```

Le script surveillera automatiquement les nouvelles factures payées et créera les tâches correspondantes. 