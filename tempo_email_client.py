#!/usr/bin/env python3
"""
Client Email Office365 pour l'intégration Tempo
Gère l'envoi d'emails d'alerte en cas d'erreurs
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class TempoEmailClient:
    """Client pour l'envoi d'emails Office365 - Alertes Tempo"""
    
    def __init__(self):
        self.smtp_host = 'smtp.office365.com'
        self.smtp_port = 587
        self.username = os.getenv('OFFICE365_USER')
        self.password = os.getenv('OFFICE365_PASSWORD')
        self.sender_email = os.getenv('OFFICE365_SENDER') or self.username
        self.sender_name = os.getenv('OFFICE365_SENDER_NAME') or 'Intégration Tempo'
        
        # Destinataires par défaut
        self.default_recipients = os.getenv('TEMPO_ALERT_EMAILS', '').split(',')
        self.default_recipients = [email.strip() for email in self.default_recipients if email.strip()]
        
        # Vérifier la configuration
        if not all([self.username, self.password]):
            raise ValueError("Configuration Office365 manquante dans le fichier .env")
    
    def test_connection(self) -> bool:
        """Teste la connexion SMTP Office365"""
        try:
            print("🔧 Test de connexion SMTP Office365...")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                
            print("✅ Connexion SMTP Office365 réussie")
            return True
            
        except Exception as e:
            print(f"❌ Erreur de connexion SMTP: {e}")
            return False
    
    def send_alert_email(self, subject: str, html_content: str, 
                        recipients: Optional[List[str]] = None,
                        error_details: Optional[Dict] = None) -> bool:
        """
        Envoie un email d'alerte
        
        Args:
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            recipients: Liste des destinataires (optionnel)
            error_details: Détails de l'erreur (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Utiliser les destinataires par défaut si aucun fourni
            if not recipients:
                recipients = self.default_recipients
            
            if not recipients:
                print("⚠ Aucun destinataire configuré pour les alertes")
                return False
            
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[ALERTE TEMPO] {subject}"
            
            # Ajouter les détails d'erreur si fournis
            if error_details:
                html_content += self._format_error_details(error_details)
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Envoyer l'email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                
                for recipient in recipients:
                    server.send_message(msg)
                    print(f"✅ Email d'alerte envoyé à: {recipient}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email d'alerte: {e}")
            return False
    
    def send_facture_not_found_alert(self, invoice_number: int, dossier: str, 
                                   base_url: str, error_context: str) -> bool:
        """
        Envoie une alerte spécifique pour facture introuvable
        
        Args:
            invoice_number: Numéro de la facture
            dossier: Dossier Tempo
            base_url: URL de base Tempo
            error_context: Contexte de l'erreur
            
        Returns:
            True si succès, False sinon
        """
        subject = f"Facture {invoice_number} introuvable dans Tempo"
        
        html_content = f"""
        <h2>🚨 ALERTE - Facture introuvable dans Tempo</h2>
        
        <h3>Détails de l'erreur :</h3>
        <ul>
            <li><strong>Numéro de facture :</strong> {invoice_number}</li>
            <li><strong>Dossier Tempo :</strong> {dossier}</li>
            <li><strong>URL Tempo :</strong> {base_url}</li>
            <li><strong>Contexte :</strong> {error_context}</li>
            <li><strong>Date/heure :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
        </ul>
        
        <h3>Actions recommandées :</h3>
        <ol>
            <li>Vérifier que la facture {invoice_number} existe dans le dossier {dossier}</li>
            <li>Vérifier la synchronisation Pennylane-Tempo</li>
            <li>Contrôler le format des numéros de facture</li>
            <li>Vérifier les droits d'accès au dossier {dossier}</li>
        </ol>
        
        <p><em>Cette alerte a été générée automatiquement par l'intégration Tempo.</em></p>
        """
        
        return self.send_alert_email(subject, html_content)
    
    def send_reglement_failed_alert(self, invoice_number: int, operation_type: str,
                                  error_message: str, payload: Dict) -> bool:
        """
        Envoie une alerte pour échec de règlement
        
        Args:
            invoice_number: Numéro de la facture
            operation_type: Type d'opération (règlement total, partiel, etc.)
            error_message: Message d'erreur
            payload: Données envoyées à Tempo
            
        Returns:
            True si succès, False sinon
        """
        subject = f"Échec du {operation_type} - Facture {invoice_number}"
        
        html_content = f"""
        <h2>🚨 ALERTE - Échec du {operation_type}</h2>
        
        <h3>Détails de l'erreur :</h3>
        <ul>
            <li><strong>Numéro de facture :</strong> {invoice_number}</li>
            <li><strong>Type d'opération :</strong> {operation_type}</li>
            <li><strong>Message d'erreur :</strong> {error_message}</li>
            <li><strong>Date/heure :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
        </ul>
        
        <h3>Données envoyées à Tempo :</h3>
        <pre><code>{self._format_payload(payload)}</code></pre>
        
        <h3>Actions recommandées :</h3>
        <ol>
            <li>Vérifier la connectivité avec Tempo</li>
            <li>Contrôler les données envoyées</li>
            <li>Vérifier les logs Tempo</li>
            <li>Contacter l'administrateur Tempo si nécessaire</li>
        </ol>
        
        <p><em>Cette alerte a été générée automatiquement par l'intégration Tempo.</em></p>
        """
        
        return self.send_alert_email(subject, html_content)
    
    def send_integration_summary(self, processed_count: int, error_count: int,
                               details: List[Dict]) -> bool:
        """
        Envoie un résumé de l'intégration
        
        Args:
            processed_count: Nombre de règlements traités
            error_count: Nombre d'erreurs
            details: Détails des opérations
            
        Returns:
            True si succès, False sinon
        """
        subject = f"Résumé intégration Tempo - {processed_count} traités, {error_count} erreurs"
        
        # Générer le résumé des opérations
        operations_summary = ""
        for op in details:
            status_icon = "✅" if op.get('success') else "❌"
            operations_summary += f"""
            <tr>
                <td>{status_icon}</td>
                <td>{op.get('invoice_number', 'N/A')}</td>
                <td>{op.get('operation_type', 'N/A')}</td>
                <td>{op.get('amount', 'N/A')}€</td>
                <td>{op.get('message', 'N/A')}</td>
            </tr>
            """
        
        html_content = f"""
        <h2>📊 Résumé de l'intégration Tempo</h2>
        
        <h3>Statistiques :</h3>
        <ul>
            <li><strong>Date/heure :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
            <li><strong>Règlements traités :</strong> {processed_count}</li>
            <li><strong>Erreurs rencontrées :</strong> {error_count}</li>
            <li><strong>Taux de succès :</strong> {(processed_count/(processed_count+error_count)*100):.1f}%</li>
        </ul>
        
        <h3>Détail des opérations :</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th>Statut</th>
                    <th>Facture</th>
                    <th>Opération</th>
                    <th>Montant</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
                {operations_summary}
            </tbody>
        </table>
        
        <p><em>Ce résumé a été généré automatiquement par l'intégration Tempo.</em></p>
        """
        
        return self.send_alert_email(subject, html_content)
    
    def _format_error_details(self, error_details: Dict) -> str:
        """Formate les détails d'erreur en HTML"""
        html = "<h3>Détails techniques de l'erreur :</h3><ul>"
        
        for key, value in error_details.items():
            if isinstance(value, dict):
                html += f"<li><strong>{key}:</strong> <pre>{self._format_payload(value)}</pre></li>"
            else:
                html += f"<li><strong>{key}:</strong> {value}</li>"
        
        html += "</ul>"
        return html
    
    def _format_payload(self, payload: Dict) -> str:
        """Formate un payload en JSON lisible"""
        import json
        try:
            return json.dumps(payload, indent=2, ensure_ascii=False)
        except:
            return str(payload)
