from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import ContactMessage


class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_contact_success(self):
        data = {
            'name': 'Omm Prasad Jena',
            'email': 'omm@example.com',
            'subject': 'Portfolio Contact Test',
            'message': 'Hello from unit test!'
        }
        response = self.client.post('/api/contact/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json().get('success'))
        self.assertEqual(ContactMessage.objects.count(), 1)
        
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.name, 'Omm Prasad Jena')
        self.assertEqual(msg.email, 'omm@example.com')
        self.assertFalse(msg.is_read)

    def test_contact_validation_error(self):
        data = {
            'name': '',
            'email': 'invalid-email',
            'subject': '',
            'message': ''
        }
        response = self.client.post('/api/contact/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json().get('success'))
        self.assertIn('errors', response.json())

    def test_chat_empty_messages(self):
        response = self.client.post('/api/chat/', {'messages': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_missing_api_key(self):
        response = self.client.post('/api/chat/', {'messages': [{'role': 'user', 'content': 'Hi'}]}, format='json')
        # Without GROQ_API_KEY set, it should return 500 error gracefully
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.json().get('success'))
