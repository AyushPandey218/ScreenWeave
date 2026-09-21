import unittest
from fastapi.testclient import TestClient
from app.main import app, job_lock

class DashboardTests(unittest.TestCase):
    def test_dashboard_and_metrics(self):
        with TestClient(app) as client:
            self.assertEqual(client.get('/', follow_redirects=False).headers['location'], '/dashboard')
            page = client.get('/dashboard')
            self.assertEqual(page.status_code, 200)
            self.assertIn('Test reconstruction', page.text)
            before = client.get('/status').json()
            self.assertEqual(client.post('/render', content=b'{}').status_code, 422)
            after = client.get('/status').json()
            self.assertEqual(after['requests'], before['requests'] + 1)
            self.assertEqual(after['failed_requests'], before['failed_requests'] + 1)
            self.assertGreaterEqual(after['average_seconds'], 0)
            self.assertFalse(after['reconstruction_busy'])
            with job_lock:
                self.assertTrue(client.get('/status').json()['reconstruction_busy'])
            self.assertEqual(client.get('/status').json()['requests'], after['requests'])

if __name__ == '__main__':
    unittest.main()
