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
        response.close()

    @patch.dict(app.os.environ, {
        'ADMIN_AUTH_MODE_EURES_BETA': 'magic_link',
        'ADMIN_ALLOWED_EMAILS_EURES_BETA': 'eric.barthelemy@inclusion.gouv.fr,eric.barthelemy@me.com',
    }, clear=False)
    def test_magic_link_mode_redirects_admin_to_login(self):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/admin/eures-beta/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/eures-beta/login', response.headers['Location'])

    @patch.dict(app.os.environ, {
        'ADMIN_AUTH_MODE_EURES_BETA': 'magic_link',
        'ADMIN_ALLOWED_EMAILS_EURES_BETA': 'eric.barthelemy@inclusion.gouv.fr,eric.barthelemy@me.com',
    }, clear=False)
    @patch.object(app.requests, 'post')
    def test_magic_link_request_rejects_unauthorized_email(self, requests_post):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.post(
                '/admin/eures-beta/login',
                data={'email': 'intrus@example.org'},
            )

        self.assertEqual(response.status_code, 403)
        self.assertIn(b'pas autorisee', response.data)
        requests_post.assert_not_called()
        response.close()

    @patch.dict(app.os.environ, {
        'ADMIN_AUTH_MODE_EURES_BETA': 'magic_link',
        'ADMIN_ALLOWED_EMAILS_EURES_BETA': 'eric.barthelemy@inclusion.gouv.fr,eric.barthelemy@me.com',
        'BREVO_API_KEY': 'brevo-key',
        'BREVO_FROM_EMAIL': 'eures@example.org',
        'BREVO_FROM_NAME': 'EURES beta',
    }, clear=False)
    @patch.object(app.requests, 'post')
    def test_magic_link_request_sends_email_for_allowed_address(self, requests_post):
        requests_post.return_value.status_code = 201
        requests_post.return_value.text = ''

        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.post(
                '/admin/eures-beta/login',
                data={'email': 'Eric.Barthelemy@Inclusion.Gouv.Fr'},
                base_url='https://example.test',
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Un lien de connexion a ete envoye', response.data)
        requests_post.assert_called_once()
        payload = requests_post.call_args.kwargs['json']
        self.assertEqual(payload['to'][0]['email'], 'eric.barthelemy@inclusion.gouv.fr')
        self.assertEqual(payload['subject'], '[eures-beta] Votre lien de connexion admin')
        response.close()

    @patch.dict(app.os.environ, {
        'ADMIN_AUTH_MODE_EURES_BETA': 'magic_link',
        'ADMIN_ALLOWED_EMAILS_EURES_BETA': 'eric.barthelemy@inclusion.gouv.fr,eric.barthelemy@me.com',
        'ADMIN_MAGIC_LINK_TTL_SECONDS_EURES_BETA': '900',
    }, clear=False)
    def test_magic_link_token_authenticates_admin_session(self):
        token = app._get_admin_magic_link_serializer('eures-beta').dumps({
            'form_id': 'eures-beta',
            'email': 'eric.barthelemy@inclusion.gouv.fr',
        })

        with patch.object(app, 'APP_MODE', 'eures-beta'):
            login_response = self.client.get(f'/admin/eures-beta/magic?token={token}')
            admin_response = self.client.get('/admin/eures-beta/')

        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(admin_response.status_code, 200)
        self.assertIn(b'Console admin - EURES beta', admin_response.data)
        login_response.close()
        admin_response.close()

    @patch.object(app, 'build_eures_public_stats')
    def test_eures_public_stats_remains_available_in_isolated_mode(self, build_eures_public_stats):
        build_eures_public_stats.return_value = {'ok': True}

        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/api/forms/eures-beta/public-stats')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'ok': True})

    def test_project_page_is_available_in_isolated_mode(self):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/forms/eures-beta/le-projet/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Match Europe', response.data)
        response.close()

    def test_journal_page_is_available_in_isolated_mode(self):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get('/forms/eures-beta/journal/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Journal du projet', response.data)
        response.close()


if __name__ == '__main__':
    unittest.main()
