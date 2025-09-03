import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

from armado_client import ArmadoClient
from sync_payments import sync_armado_after_tempo, sync_with_error_handling, get_available_payment_modes

class TestArmadoClient(unittest.TestCase):
    """Tests unitaires pour ArmadoClient"""
    
    def setUp(self):
        """Configuration des tests"""
        with patch.dict('os.environ', {
            'ARMADO_API_KEY': 'test_api_key',
            'ARMADO_BASE_URL': 'https://api.test.armado.fr'
        }):
            self.client = ArmadoClient()
    
    @patch('requests.request')
    def test_find_bill_id_by_reference_success(self, mock_request):
        """Test de recherche de facture avec succès"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 12345, 'reference': '20664'}]
        mock_request.return_value = mock_response
        
        # Test
        result = self.client.find_bill_id_by_reference('20664')
        
        # Vérifications
        self.assertEqual(result, 12345)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['method'], 'GET')
        self.assertEqual(call_args[1]['url'], 'https://api.test.armado.fr/v1/bill')
        self.assertEqual(call_args[1]['params']['reference'], '20664')
    
    @patch('requests.request')
    def test_find_bill_id_by_reference_not_found(self, mock_request):
        """Test de recherche de facture non trouvée"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response
        
        # Test
        result = self.client.find_bill_id_by_reference('99999')
        
        # Vérifications
        self.assertIsNone(result)
    
    @patch('requests.request')
    def test_find_bill_id_by_reference_unauthorized(self, mock_request):
        """Test de recherche avec API key invalide"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        # Test
        with self.assertRaises(ValueError) as context:
            self.client.find_bill_id_by_reference('20664')
        
        self.assertIn("API key invalide", str(context.exception))
    
    @patch('requests.request')
    def test_update_bill_payment_success(self, mock_request):
        """Test de mise à jour de paiement avec succès"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 12345,
            'paymentType': 2,
            'paymentDate': '2024-01-15T10:30:00.000000'
        }
        mock_request.return_value = mock_response
        
        # Test
        result = self.client.update_bill_payment(12345, 2, '2024-01-15T10:30:00.000000')
        
        # Vérifications
        self.assertEqual(result['id'], 12345)
        self.assertEqual(result['paymentType'], 2)
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[1]['method'], 'PUT')
        self.assertIn('/v1/bill/12345', call_args[1]['url'])
        self.assertEqual(call_args[1]['json']['paymentType'], 2)
        self.assertEqual(call_args[1]['json']['paymentDate'], '2024-01-15T10:30:00.000000')
    
    @patch('requests.request')
    def test_update_bill_payment_not_found(self, mock_request):
        """Test de mise à jour avec facture introuvable"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        # Test
        with self.assertRaises(ValueError) as context:
            self.client.update_bill_payment(99999, 2, '2024-01-15T10:30:00.000000')
        
        self.assertIn("introuvable", str(context.exception))
    
    @patch('requests.request')
    def test_update_bill_payment_validation_error(self, mock_request):
        """Test de mise à jour avec erreur de validation"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {'message': 'Invalid payment type'}
        mock_request.return_value = mock_response
        
        # Test
        with self.assertRaises(ValueError) as context:
            self.client.update_bill_payment(12345, 999, '2024-01-15T10:30:00.000000')
        
        self.assertIn("Invalid payment type", str(context.exception))

class TestSyncPayments(unittest.TestCase):
    """Tests unitaires pour le module de synchronisation"""
    
    @patch('sync_payments.ArmadoClient')
    def test_sync_armado_after_tempo_success(self, mock_client_class):
        """Test de synchronisation réussie"""
        # Mock du client Armado
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.find_bill_id_by_reference.return_value = 12345
        mock_client.update_bill_payment.return_value = {
            'id': 12345,
            'paymentType': 2,
            'paymentDate': '2024-01-15T10:30:00.000000'
        }
        
        # Test
        result = sync_armado_after_tempo(
            invoice_reference='20664',
            payment_mode='virement',
            payment_date=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        # Vérifications
        self.assertEqual(result['id'], 12345)
        mock_client.find_bill_id_by_reference.assert_called_once_with('20664')
        mock_client.update_bill_payment.assert_called_once_with(
            12345, 2, '2024-01-15T10:30:00.000000'
        )
    
    @patch('sync_payments.ArmadoClient')
    def test_sync_armado_after_tempo_bill_not_found(self, mock_client_class):
        """Test de synchronisation avec facture introuvable"""
        # Mock du client Armado
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.find_bill_id_by_reference.return_value = None
        
        # Test
        with self.assertRaises(ValueError) as context:
            sync_armado_after_tempo(
                invoice_reference='99999',
                payment_mode='virement',
                payment_date=datetime.now()
            )
        
        self.assertIn("introuvable", str(context.exception))
    
    @patch('sync_payments.ArmadoClient')
    def test_sync_armado_after_tempo_invalid_payment_mode(self, mock_client_class):
        """Test de synchronisation avec mode de paiement invalide"""
        # Mock du client Armado
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.find_bill_id_by_reference.return_value = 12345
        
        # Test
        with self.assertRaises(ValueError) as context:
            sync_armado_after_tempo(
                invoice_reference='20664',
                payment_mode='mode_invalide',
                payment_date=datetime.now()
            )
        
        self.assertIn("paymentType introuvable", str(context.exception))
    
    def test_get_available_payment_modes(self):
        """Test de récupération des modes de paiement disponibles"""
        modes = get_available_payment_modes()
        
        # Vérifications
        self.assertIsInstance(modes, list)
        self.assertIn('virement', modes)
        self.assertIn('cb', modes)
        self.assertIn('cheque', modes)
        self.assertIn('especes', modes)
    
    @patch('sync_payments.ArmadoClient')
    def test_sync_with_error_handling_success(self, mock_client_class):
        """Test de synchronisation avec gestion d'erreur (succès)"""
        # Mock du client Armado
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.find_bill_id_by_reference.return_value = 12345
        mock_client.update_bill_payment.return_value = {'id': 12345}
        
        # Test
        result = sync_with_error_handling(
            invoice_reference='20664',
            payment_mode='virement',
            payment_date=datetime.now()
        )
        
        # Vérifications
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['data'])
        self.assertIsNone(result['error'])
    
    @patch('sync_payments.ArmadoClient')
    def test_sync_with_error_handling_failure(self, mock_client_class):
        """Test de synchronisation avec gestion d'erreur (échec)"""
        # Mock du client Armado
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.find_bill_id_by_reference.return_value = None
        
        # Test
        result = sync_with_error_handling(
            invoice_reference='99999',
            payment_mode='virement',
            payment_date=datetime.now()
        )
        
        # Vérifications
        self.assertFalse(result['success'])
        self.assertIsNone(result['data'])
        self.assertIsNotNone(result['error'])
        self.assertIn("introuvable", result['error'])

class TestIntegration(unittest.TestCase):
    """Tests d'intégration (nécessitent une vraie API key pour les tests complets)"""
    
    def test_armado_client_initialization(self):
        """Test d'initialisation du client Armado"""
        with patch.dict('os.environ', {
            'ARMADO_API_KEY': 'test_key',
            'ARMADO_BASE_URL': 'https://api.test.armado.fr'
        }):
            client = ArmadoClient()
            self.assertEqual(client.api_key, 'test_key')
            self.assertEqual(client.base_url, 'https://api.test.armado.fr')
    
    def test_armado_client_missing_api_key(self):
        """Test d'initialisation sans API key"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                ArmadoClient()
            self.assertIn("ARMADO_API_KEY non définie", str(context.exception))

if __name__ == '__main__':
    # Configuration des tests
    unittest.main(verbosity=2)
