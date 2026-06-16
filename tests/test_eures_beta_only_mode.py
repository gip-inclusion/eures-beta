import base64
import unittest
from unittest.mock import patch

import app


class EuresBetaOnlyModeTest(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_root_redirects_to_eures_beta_in_isolated_mode(self):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/forms/eures-beta/')

    def test_fagerh_routes_are_hidden_in_isolated_mode(self):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/forms/fagerh/')

        self.assertEqual(response.status_code, 404)

    @patch.dict(app.os.environ, {
        'ADMIN_USERNAME': 'shared-admin',
        'ADMIN_PASSWORD': 'shared-password',
        'ADMIN_USERNAME_EURES_BETA': 'eures-admin',
        'ADMIN_PASSWORD_EURES_BETA': 'eures-password',
    }, clear=False)
    def test_eures_admin_prefers_form_specific_credentials(self):
        token = base64.b64encode(b'eures-admin:eures-password').decode('ascii')

        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get(
                '/admin/eures-beta/',
                headers={'Authorization': f'Basic {token}'},
            )

        self.assertNotEqual(response.status_code, 401)

    @patch.object(app, 'build_eures_public_stats')
    def test_eures_public_stats_remains_available_in_isolated_mode(self, build_eures_public_stats):
        build_eures_public_stats.return_value = {'ok': True}

        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/api/forms/eures-beta/public-stats')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'ok': True})


if __name__ == '__main__':
    unittest.main()
