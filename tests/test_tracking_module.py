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

    def test_validate_tracking_card_archives_and_restores_with_history(self):
        created = app.validate_tracking_card({
            'titre': 'Carte de test',
            'description': 'Tester le comportement d archivage.'
        }, actor='alice@example.org')
        existing = created['card']

        archived = app.validate_tracking_card({
            'record_id': 12,
            'card_id': existing['card_id'],
            'titre': existing['titre'],
            'description': existing['description'],
            'archived': True,
        }, existing=existing, actor='bob@example.org')

        self.assertEqual(archived['errors'], [])
        self.assertTrue(archived['card']['archived'])
        self.assertEqual(archived['card']['archived_by'], 'bob@example.org')
        self.assertTrue(archived['card']['archived_at'])
        self.assertTrue(any(event['action'] == 'archived' for event in archived['card']['historique']))

        restored = app.validate_tracking_card({
            'record_id': 12,
            'card_id': archived['card']['card_id'],
            'titre': archived['card']['titre'],
            'description': archived['card']['description'],
            'archived': False,
        }, existing=archived['card'], actor='carol@example.org')

        self.assertEqual(restored['errors'], [])
        self.assertFalse(restored['card']['archived'])
        self.assertEqual(restored['card']['archived_at'], '')
        self.assertEqual(restored['card']['archived_by'], '')
        self.assertTrue(any(event['action'] == 'restored' for event in restored['card']['historique']))

    def test_tracking_card_roundtrip_includes_archive_fields(self):
        record = {
            'id': 17,
            'fields': {
                'card_id': 'card-17',
                'titre': 'Carte archivee',
                'description': 'Description',
                'archived': True,
                'archived_at': '2026-07-21T10:00:00Z',
                'archived_by': 'eric@example.org',
                'liens_json': '[]',
                'commentaires_json': '[]',
                'historique_json': '[]',
            },
        }

        card = app._tracking_card_from_record(record)

        self.assertTrue(card['archived'])
        self.assertEqual(card['archived_at'], '2026-07-21T10:00:00Z')
        self.assertEqual(card['archived_by'], 'eric@example.org')
        self.assertTrue(app._tracking_record_fields(card)['archived'])

    def test_tracking_metadata_exposes_archive_filters(self):
        metadata = app.tracking_metadata()

        self.assertEqual(metadata['archive_filters'], ['active', 'archived', 'all'])

    def test_validate_tracking_card_keeps_valid_images_and_rejects_invalid_ones(self):
        result = app.validate_tracking_card({
            'titre': 'Carte avec image',
            'description': 'Ajout d une capture ecran.',
            'images': [
                {
                    'id': 'img-1',
                    'name': 'capture.png',
                    'mime': 'image/png',
                    'size': 12345,
                    'width': 800,
                    'height': 600,
                    'data_url': 'data:image/png;base64,AAAA',
                },
                {
                    'id': 'img-2',
                    'name': 'document.pdf',
                    'mime': 'application/pdf',
                    'size': 900,
                    'data_url': 'data:application/pdf;base64,BBBB',
                },
            ],
        }, actor='tester')

        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['card']['images']), 1)
        self.assertEqual(result['card']['images'][0]['name'], 'capture.png')
        self.assertTrue(any('ignor' in warning.lower() for warning in result['warnings']))

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

    @patch.dict(app.os.environ, {}, clear=True)
    def test_translate_tracking_card_payload_reports_missing_api_key(self):
        translated, warnings = app.translate_tracking_card_payload({
            'langue_source': 'fr',
            'titre': 'Titre',
            'description': 'Description',
            'attendu': '',
            'observe': '',
            'contexte': '',
        }, 'en')

        self.assertEqual(translated['target_language'], 'en')
        self.assertEqual(warnings, [
            "Automatic translation is not enabled. Use your computer's built-in translation tools or another translation tool, then paste the translated text here.",
        ])

    @patch.object(app.requests, 'post')
    @patch.dict(app.os.environ, {'OPENAI_API_KEY': 'test-key'}, clear=False)
    def test_translate_tracking_card_payload_reports_http_error(self, requests_post):
        requests_post.return_value = SimpleNamespace(status_code=429, text='rate limited')

        translated, warnings = app.translate_tracking_card_payload({
            'langue_source': 'fr',
            'titre': 'Titre',
            'description': 'Description',
            'attendu': '',
            'observe': '',
            'contexte': '',
        }, 'de')

        self.assertEqual(translated['target_language'], 'de')
        self.assertEqual(warnings, [
            'Die automatische Ubersetzung ist derzeit nicht verfugbar (OpenAI HTTP 429). Nutzen Sie die integrierten Ubersetzungstools Ihres Computers oder ein anderes Ubersetzungstool und fugen Sie den ubersetzten Text anschliessend hier ein.',
        ])


if __name__ == '__main__':
    unittest.main()
