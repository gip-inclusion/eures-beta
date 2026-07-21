import base64
import json
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
            'statut': 'fait',
        }, actor='tester')

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['card']['titre'], 'Corriger le bouton de login qui ne répond plus')
        self.assertEqual(result['card']['liens'], ['https://example.org/task'])
        self.assertTrue(any('titre' in warning.lower() for warning in result['warnings']))
        self.assertTrue(any('ignor' in warning.lower() for warning in result['warnings']))

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
                'indicateurs_suivi': 'Taux de completion et nombre de doublons',
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
        self.assertEqual(card['indicateurs_suivi'], 'Taux de completion et nombre de doublons')
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

    @patch.object(app, 'write_grist_records')
    @patch.object(app, '_tracking_find_record_by_card_id')
    def test_save_tracking_card_updates_existing_card_with_same_card_id(self, find_by_card_id, write_grist_records):
        existing_record = {
            'id': 9,
            'fields': {
                'card_id': 'card-test-1',
                'titre': 'Carte test 1',
                'description': 'Version initiale',
                'liens_json': '[]',
                'commentaires_json': '[]',
                'historique_json': '[]',
            },
        }
        find_by_card_id.return_value = (
            existing_record,
            {'doc_id': 'doc-eures', 'table_id': 'Suivi_Projet', 'api_key': 'api-key'},
            {'Authorization': 'Bearer api-key', 'Accept': 'application/json', 'Content-Type': 'application/json'},
        )
        write_grist_records.return_value = SimpleNamespace(status_code=200, text='')

        result = app.save_tracking_card({
            'card_id': 'card-test-1',
            'titre': 'Carte test 1',
            'description': 'Version modifiee',
        }, actor='tester')

        self.assertTrue(result['ok'])
        self.assertEqual(result['card']['record_id'], 9)
        write_grist_records.assert_called_once()
        method, url, payload, _headers = write_grist_records.call_args.args
        self.assertEqual(method, 'PATCH')
        self.assertEqual(url, 'https://grist.numerique.gouv.fr/api/docs/doc-eures/tables/Suivi_Projet/records')
        self.assertEqual(payload['records'][0]['id'], 9)
        self.assertEqual(payload['records'][0]['fields']['description'], 'Version modifiee')

    @patch.object(app, '_tracking_update_card_record')
    @patch.object(app, '_tracking_find_record_by_reference')
    def test_apply_tracking_github_event_updates_card_from_pull_request(self, find_by_reference, update_card_record):
        record = {
            'id': 23,
            'fields': {
                'card_id': 'trk_abc123',
                'titre': 'Automatiser le suivi',
                'description': 'Description',
                'statut': 'a_faire',
                'liens_json': '[]',
                'commentaires_json': '[]',
                'historique_json': '[]',
            },
        }
        find_by_reference.return_value = (
            record,
            {'doc_id': 'doc-eures', 'table_id': 'Suivi_Projet', 'api_key': 'api-key'},
            {'Authorization': 'Bearer api-key'},
        )
        update_card_record.side_effect = lambda rec, _config, _headers, card: card

        result = app.apply_tracking_github_event({
            'action': 'opened',
            'number': 42,
            'pull_request': {
                'number': 42,
                'title': 'EURES-23 autosave',
                'html_url': 'https://github.com/gip-inclusion/eures-beta/pull/42',
                'head': {'ref': 'feature/EURES-23-autosave'},
                'base': {'ref': 'main'},
                'labels': [],
            },
        }, 'pull_request')

        self.assertTrue(result['ok'])
        self.assertTrue(result['updated'])
        self.assertEqual(result['reference'], 'EURES-23')
        self.assertEqual(result['card']['statut'], 'en_cours')
        self.assertEqual(result['card']['github_pr_state'], 'open')
        self.assertEqual(result['card']['github_pr_number'], '42')
        self.assertEqual(result['card']['github_branch'], 'feature/EURES-23-autosave')
        self.assertIn('https://github.com/gip-inclusion/eures-beta/pull/42', result['card']['liens'])
        self.assertTrue(any(event['action'] == 'github_pr_opened' for event in result['card']['historique']))

    @patch.object(app, '_tracking_update_card_record')
    @patch.object(app, '_tracking_find_record_by_reference')
    def test_apply_tracking_deployment_event_marks_card_done(self, find_by_reference, update_card_record):
        record = {
            'id': 23,
            'fields': {
                'card_id': 'trk_abc123',
                'titre': 'Automatiser le suivi',
                'description': 'Description',
                'statut': 'en_cours',
                'liens_json': json.dumps(['https://github.com/gip-inclusion/eures-beta/pull/42']),
                'commentaires_json': '[]',
                'historique_json': '[]',
            },
        }
        find_by_reference.return_value = (
            record,
            {'doc_id': 'doc-eures', 'table_id': 'Suivi_Projet', 'api_key': 'api-key'},
            {'Authorization': 'Bearer api-key'},
        )
        update_card_record.side_effect = lambda rec, _config, _headers, card: card

        result = app.apply_tracking_deployment_event({
            'reference': 'EURES-23',
            'status': 'success',
            'environment': 'production',
            'deployment_url': 'https://eures-beta.osc-fr1.scalingo.io',
        })

        self.assertTrue(result['ok'])
        self.assertTrue(result['updated'])
        self.assertEqual(result['card']['statut'], 'fait')
        self.assertEqual(result['card']['production_environment'], 'production')
        self.assertEqual(result['card']['production_url'], 'https://eures-beta.osc-fr1.scalingo.io')
        self.assertTrue(result['card']['production_deployed_at'])
        self.assertIn('https://eures-beta.osc-fr1.scalingo.io', result['card']['liens'])
        self.assertTrue(any(event['action'] == 'deployment_succeeded' for event in result['card']['historique']))

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
