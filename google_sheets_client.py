import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsClient:
    """Client pour interagir avec Google Sheets"""
    
    def __init__(self):
        self.credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.sheet_name = os.getenv('SPREADSHEET_NAME')
        
        if not self.spreadsheet_id:
            raise ValueError("SPREADSHEET_ID non définie dans les variables d'environnement")
        
        if not self.sheet_name:
            raise ValueError("SPREADSHEET_NAME non définie dans les variables d'environnement")
        
        # Configuration des scopes nécessaires
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Initialisation des services
        self.credentials = self._get_credentials()
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
    
    def _get_credentials(self):
        """Charge les credentials depuis le fichier JSON"""
        try:
            return Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=self.scopes
            )
        except Exception as e:
            raise Exception(f"Erreur lors du chargement des credentials: {e}")
    
    def generate_unique_id(self) -> str:
        """Génère un ID unique aléatoire"""
        return str(uuid.uuid4())
    
    def get_or_create_sheet(self) -> str:
        """Trouve ou crée la feuille dans le spreadsheet existant"""
        try:
            # Récupérer les informations du spreadsheet
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            print(f"✓ Spreadsheet trouvé: {spreadsheet['properties']['title']}")
            print(f"  Feuilles disponibles: {sheet_names}")
            
            # Vérifier si la feuille existe
            if self.sheet_name in sheet_names:
                print(f"✓ Feuille '{self.sheet_name}' trouvée")
                return self.sheet_name
            else:
                print(f"⚠ Feuille '{self.sheet_name}' non trouvée, création...")
                return self.create_sheet()
                
        except HttpError as e:
            print(f"Erreur lors de l'accès au spreadsheet: {e}")
            return None
    
    def create_sheet(self) -> str:
        """Crée une nouvelle feuille dans le spreadsheet existant"""
        try:
            # Créer la nouvelle feuille
            request = {
                'addSheet': {
                    'properties': {
                        'title': self.sheet_name,
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 8
                        }
                    }
                }
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            print(f"✓ Nouvelle feuille '{self.sheet_name}' créée")
            
            # Configurer les en-têtes
            self.setup_headers()
            
            return self.sheet_name
            
        except HttpError as e:
            print(f"Erreur lors de la création de la feuille: {e}")
            return None
    
    def setup_headers(self):
        """Configure les en-têtes de la feuille"""
        try:
            headers = [
                'ID',
                'Statut', 
                'Date',
                'Nom de la tâche',
                'Champs modifiés',
                'ID Mission',
                'Modification faite par',
                'Commentaire interne'
            ]
            
            # Écrire les en-têtes
            range_name = f'{self.sheet_name}!A1:H1'
            body = {
                'values': [headers]
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Formater les en-têtes (gras, couleur de fond)
            # D'abord récupérer l'ID de la feuille
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == self.sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is not None:
                requests = [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': 8
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.2,
                                        'green': 0.6,
                                        'blue': 0.9
                                    },
                                    'textFormat': {
                                        'bold': True,
                                        'foregroundColor': {
                                            'red': 1,
                                            'green': 1,
                                            'blue': 1
                                        }
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    },
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': sheet_id,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': 8
                            }
                        }
                    }
                ]
                
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
            
            print("✓ En-têtes configurés avec formatage")
            
        except HttpError as e:
            print(f"Erreur lors de la configuration des en-têtes: {e}")
    
    def create_task(self, task_data: Dict) -> bool:
        """
        Crée une nouvelle tâche dans la feuille
        Format spécifié par l'utilisateur avec calculs de montants améliorés:
        - ID: ID unique aléatoire
        - Statut: "A faire"
        - Date: date du jour et heure (horodatage)
        - Nom de la tâche: "Règlement de facture" ou "Règlement partiel de facture"
        - Champs modifiés: "Numéro : X / Montant total : X€ / Montant payé : X€ / Reste : X€"
        - ID Mission: vide
        - Modification faite par: "Pennylane"
        - Commentaire interne: "Date facture : X / Client / Statut : X (X%)"
        - Colonne L: ID client tempo = nom du client extrait du libellé
        - Colonne S: Numéro de contrat Tempo = numéro de facture
        """
        try:
            # Préparer les données selon le format spécifié
            current_datetime = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            unique_id = self.generate_unique_id()

            # Utiliser les nouvelles données calculées
            row_data = [
                unique_id,  # ID = ID unique aléatoire
                'À faire',  # Statut
                current_datetime,  # Date = date du jour et heure
                task_data.get('task_name', 'Règlement de facture'),  # Nom de la tâche
                task_data.get('champs_modifies', ''),  # Champs modifiés avec détails
                '',  # ID Mission = vide
                'Pennylane',  # Modification faite par
                task_data.get('commentaire_interne', '')  # Commentaire interne avec statut
            ]

            # Trouver la prochaine ligne vide dans la feuille spécifiée
            range_name = f'{self.sheet_name}!A:A'
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            # Délai de 1 seconde pour respecter les limites de quota
            time.sleep(1)

            values = result.get('values', [])
            next_row = len(values) + 1

            # Écrire la nouvelle ligne principale (colonnes A à H)
            range_name = f'{self.sheet_name}!A{next_row}:H{next_row}'
            body = {
                'values': [row_data]
            }

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            # Délai de 1 seconde après l'écriture
            time.sleep(1)

            # Écrire le nom du client dans la colonne L (ID client tempo)
            client_range = f'{self.sheet_name}!L{next_row}'
            client_body = {
                'values': [[task_data.get('client_name', '')]]
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=client_range,
                valueInputOption='RAW',
                body=client_body
            ).execute()

            # Délai de 1 seconde
            time.sleep(1)

            # Écrire le numéro de facture dans la colonne S (Numéro de contrat Tempo)
            invoice_range = f'{self.sheet_name}!S{next_row}'
            invoice_body = {
                'values': [[task_data.get('invoice_number', '')]]
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=invoice_range,
                valueInputOption='RAW',
                body=invoice_body
            ).execute()

            # Délai de 1 seconde après l'écriture
            time.sleep(1)

            print(f"✓ Tâche créée à la ligne {next_row} dans '{self.sheet_name}' (ID: {unique_id})")
            print(f"  - {task_data.get('payment_status', 'N/A')} ({task_data.get('payment_percentage', 0):.0f}%)")
            print(f"  - Montant payé: {task_data.get('payment_amount', 'N/A')} sur {task_data.get('total_amount', 'N/A')}")
            print(f"  - Numéro facture: {task_data.get('invoice_number', 'N/A')} (colonne S)")
            print(f"  - Client: {task_data.get('client_name', 'N/A')} (colonne L)")
            return True

        except HttpError as e:
            if e.resp.status == 429:
                print(f"⚠️ Quota dépassé, attente de 60 secondes avant de réessayer...")
                time.sleep(60)
                # Réessayer une fois après l'attente
                try:
                    self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    print(f"✓ Tâche créée après réessai (ID: {unique_id})")
                    return True
                except HttpError as retry_error:
                    print(f"✗ Échec du réessai: {retry_error}")
                    return False
            else:
                print(f"Erreur lors de la création de la tâche: {e}")
                return False
    
    def setup_spreadsheet(self):
        """Configuration initiale de la feuille"""
        print("Configuration de la feuille Google Sheets...")
        
        # Trouver ou créer la feuille
        sheet_name = self.get_or_create_sheet()
        
        if sheet_name:
            print(f"✓ Feuille configurée: {sheet_name}")
            print(f"  URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        else:
            print("✗ Erreur lors de la configuration de la feuille")
            raise Exception("Impossible de configurer la feuille")

if __name__ == "__main__":
    # Test du client
    try:
        client = GoogleSheetsClient()
        client.setup_spreadsheet()
        print("Test terminé avec succès!")
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        print("Vérifiez votre configuration dans le fichier .env") 