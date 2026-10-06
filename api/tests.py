from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import ContactMessage


class APITestCase(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
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

    def test_private_unlock_success(self):
        response = self.client.post('/api/private/unlock/', {'pin': '1234'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('authenticated'))

        # Check session endpoint
        sess_resp = self.client.get('/api/private/session/')
        self.assertEqual(sess_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(sess_resp.json().get('authenticated'))

        # Logout
        logout_resp = self.client.post('/api/private/logout/')
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        sess_resp2 = self.client.get('/api/private/session/')
        self.assertFalse(sess_resp2.json().get('authenticated'))

    def test_private_unlock_invalid_pin(self):
        response = self.client.post('/api/private/unlock/', {'pin': '9999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json().get('authenticated'))
        self.assertEqual(response.json().get('message'), 'Incorrect PIN.')

    def test_private_unlock_rate_limiting(self):
        for _ in range(5):
            self.client.post('/api/private/unlock/', {'pin': '0000'}, format='json')
        
        # 6th attempt should be rate limited
        response = self.client.post('/api/private/unlock/', {'pin': '1234'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.json().get('message'), 'Too many attempts. Try again later.')

    def test_user_data_isolation(self):
        from django.contrib.auth.models import User
        from .models import Task, Subject

        user_a = User.objects.create_user(username='user_a', password='password_a')
        user_b = User.objects.create_user(username='user_b', password='password_b')

        subj_a = Subject.objects.create(user=user_a, name='Math A')
        subj_b = Subject.objects.create(user=user_b, name='Math B')

        task_a = Task.objects.create(user=user_a, subject=subj_a, title='Task for User A')
        task_b = Task.objects.create(user=user_b, subject=subj_b, title='Task for User B')

        # Log in as User A
        self.client.force_login(user_a)
        session = self.client.session
        session['private_authenticated'] = True
        session.save()

        # Get tasks for User A
        res = self.client.get('/api/private/tasks/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        task_ids = [t['id'] for t in res.json()]
        self.assertIn(task_a.id, task_ids)
        self.assertNotIn(task_b.id, task_ids)

        # Attempt to access User B's task directly
        res_b = self.client.get(f'/api/private/tasks/{task_b.id}/')
        self.assertEqual(res_b.status_code, status.HTTP_404_NOT_FOUND)


