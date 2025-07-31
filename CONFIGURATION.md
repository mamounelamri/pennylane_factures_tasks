# Guide de Configuration - Intégration Pennylane - Google Sheets

## Prérequis

1. **Compte Pennylane** avec accès API
2. **Compte Google Cloud** avec API Google Sheets activée
3. **Python 3.7+** installé

## Étape 1: Configuration Pennylane

### 1.1 Obtenir une clé API Pennylane

1. Connectez-vous à votre compte Pennylane
2. Allez dans **Paramètres** > **Intégrations** > **API**
3. Créez une nouvelle clé API
4. Copiez la clé API (elle ne sera plus visible après)

### 1.2 Tester la connexion Pennylane

```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env avec votre clé API
echo "PENNYLANE_API_KEY=votre_clé_api_ici" > .env

# Tester la connexion
python test_pennylane.py
```

## Étape 2: Configuration Google Sheets

### 2.1 Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'API Google Sheets pour ce projet

### 2.2 Créer un compte de service

1. Dans Google Cloud Console, allez dans **IAM & Admin** > **Comptes de service**
2. Cliquez sur **Créer un compte de service**
3. Donnez un nom au compte (ex: "pennylane-sheets-integration")
4. Cliquez sur **Créer et continuer**
5. Pour les rôles, ajoutez **Éditeur** (ou un rôle plus restrictif si nécessaire)
6. Cliquez sur **Terminé**

### 2.3 Télécharger les credentials

1. Cliquez sur le compte de service créé
2. Allez dans l'onglet **Clés**
3. Cliquez sur **Ajouter une clé** > **Créer une nouvelle clé**
4. Sélectionnez **JSON**
5. Téléchargez le fichier et renommez-le `credentials.json`
6. Placez-le dans le répertoire du projet

### 2.4 Créer un Google Sheet

1. Créez un nouveau Google Sheet
2. Notez l'ID du spreadsheet dans l'URL :
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```
3. Partagez le Google Sheet avec l'email du compte de service (visible dans credentials.json)

## Étape 3: Configuration finale

### 3.1 Créer le fichier .env

```bash
# Copier le fichier d'exemple
cp env_example.txt .env

# Éditer le fichier .env avec vos informations
nano .env
```

Contenu du fichier `.env` :
```
PENNYLANE_API_KEY=votre_clé_api_pennylane
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=votre_id_spreadsheet
```

### 3.2 Tester la configuration complète

```bash
# Test de la configuration Google Sheets
python google_sheets_client.py

# Test de l'intégration complète
python main.py
```

## Étape 4: Utilisation

### 4.1 Exécution unique

```bash
python main.py
# Choisir l'option 1
```

### 4.2 Surveillance continue

```bash
python main.py
# Choisir l'option 2
```

Le script surveillera automatiquement les nouvelles factures payées toutes les heures.

## Structure du Google Sheet

Le script créera automatiquement un Google Sheet avec les colonnes suivantes :

| Colonne | Description |
|---------|-------------|
| A | Numéro Client |
| B | Nom Client |
| C | Numéro Facture |
| D | Date Facture |
| E | Date Règlement |
| F | Montant Règlement |
| G | Statut |
| H | Date Création Tâche |

## Gestion des cas particuliers

### Factures partiellement payées

- Le statut sera marqué comme "Partiellement payée"
- Le montant affiché sera le montant du règlement effectué

### Avoirs

- Le numéro de facture sera préfixé par "AVOIR"
- Le statut sera "Avoir payé"

## Dépannage

### Erreur de connexion Pennylane

1. Vérifiez que votre clé API est correcte
2. Vérifiez que votre compte Pennylane a accès à l'API
3. Testez avec `python test_pennylane.py`

### Erreur de connexion Google Sheets

1. Vérifiez que le fichier `credentials.json` est présent
2. Vérifiez que l'API Google Sheets est activée
3. Vérifiez que le Google Sheet est partagé avec le compte de service
4. Testez avec `python google_sheets_client.py`

### Aucune facture traitée

1. Vérifiez qu'il y a des factures payées dans Pennylane
2. Vérifiez que les statuts correspondent à ceux attendus
3. Consultez les logs pour plus de détails

## Sécurité

- Ne partagez jamais votre fichier `credentials.json`
- Ne committez jamais votre fichier `.env` dans Git
- Utilisez des rôles restrictifs pour le compte de service Google
- Régénérez régulièrement votre clé API Pennylane 