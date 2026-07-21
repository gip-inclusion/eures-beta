import base64
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import app


class TrackingModuleTest(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_validate_tracking_card_derives_title_and_ignores_invalid_links(self):
        result = app.validate_tracking_card({
            'description': 'Corriger le bouton de login qui ne répond plus.',
            'liens': ['https://example.org/task', 'mailto:test@example.org'],
            'bloquant': True,
            'statut': 'fait',
        }, actor='tester')

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['card']['titre'], 'Corriger le bouton de login qui ne répond plus')
        self.assertEqual(result['card']['liens'], ['https://example.org/task'])
        self.assertTrue(any('titre' in warning.lower() for warning in result['warnings']))
        self.assertTrue(any('ignor' in warning.lower() for warning in result['warnings']))
        self.assertTrue(any('bloquante' in warning.lower() for warning in result['warnings']))

    def test_draft_tracking_card_from_text_detects_bug_and_blocker(self):
        result = app.draft_tracking_card_from_text(
            "Bug critique sur la page admin. Le bouton export bloque toute l'équipe.",
            source_language='fr',
            actor='tester',
            source='assistant',
        )

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['card']['type'], 'bug')
        self.assertEqual(result['card']['priorite'], 'critique')
        self.assertTrue(result['card']['bloquant'])
        self.assertEqual(result['card']['source'], 'assistant')

    @patch.dict(app.os.environ, {
        'ADMIN_USERNAME_EURES_BETA': 'eures-admin',
        'ADMIN_PASSWORD_EURES_BETA': 'eures-password',
        'ADMIN_AUTH_MODE_EURES_BETA': 'basic',
    }, clear=False)
    def test_tracking_admin_page_is_available(self):
        token = base64.b64encode(b'eures-admin:eures-password').decode('ascii')
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            response = self.client.get(
                '/admin/eures-beta/suivi',
                headers={'Authorization': f'Basic {token}'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Suivi projet', response.data)
        response.close()

    @patch.object(app, 'write_grist_records')
    @patch.object(app, '_tracking_table_ready')
    def test_delete_tracking_card_uses_grist_delete_payload_contract(self, tracking_table_ready, write_grist_records):
        tracking_table_ready.return_value = (
            {'doc_id': 'doc-eures', 'table_id': 'Suivi_Projet', 'api_key': 'api-key'},
            {'Authorization': 'Bearer api-key', 'Accept': 'application/json', 'Content-Type': 'application/json'},
        )
        write_grist_records.return_value = SimpleNamespace(status_code=200, text='')

        app.delete_tracking_card(42)

        write_grist_records.assert_called_once_with(
            'POST',
            'https://grist.numerique.gouv.fr/api/docs/doc-eures/tables/Suivi_Projet/records/delete',
            [42],
            {'Authorization': 'Bearer api-key', 'Accept': 'application/json', 'Content-Type': 'application/json'},
        )


if __name__ == '__main__':
    unittest.main()
