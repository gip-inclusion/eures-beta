import base64
import unittest
from unittest.mock import patch

import app


class RecomputeMatchingsTest(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def _auth_headers(self):
        token = base64.b64encode(b'eures-admin:eures-password').decode('ascii')
        return {'Authorization': f'Basic {token}'}

    def test_recompute_requires_admin_auth(self):
        with patch.object(app, 'APP_MODE', 'eures-beta'):
            resp = self.client.post('/api/forms/eures-beta/admin/recompute-matchings')
        self.assertIn(resp.status_code, (401, 503))

    @patch.dict(app.os.environ, {
        'ADMIN_USERNAME_EURES_BETA': 'eures-admin',
        'ADMIN_PASSWORD_EURES_BETA': 'eures-password',
    }, clear=False)
    @patch.object(app, 'upsert_matching_record')
    @patch.object(app, 'fetch_table_records')
    @patch.object(app, 'get_form_config')
    def test_recompute_covers_every_pair(self, get_form_config, fetch_table_records, upsert_matching_record):
        get_form_config.return_value = {'doc_id': 'doc', 'table_id': 'Candidats', 'api_key': 'k'}

        def fake_fetch(doc_id, table_id, headers, limit=5000):
            if table_id == app.EURES_CANDIDATS_TABLE:
                return [
                    {'fields': {'id_tally': 'c1', 'metier': 'Vente', 'pays': 'France'}},
                    {'fields': {'id_tally': 'c2', 'metier': 'Vente', 'pays': 'France'}},
                ]
            if table_id == app.EURES_BESOINS_TABLE:
                return [
                    {'fields': {'id_tally': 'b1', 'poste': 'Vente', 'pays': 'Luxembourg'}},
                ]
            return []

        fetch_table_records.side_effect = fake_fetch

        with patch.object(app, 'APP_MODE', 'eures-beta'):
            resp = self.client.post(
                '/api/forms/eures-beta/admin/recompute-matchings',
                headers=self._auth_headers(),
            )

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['candidats'], 2)
        self.assertEqual(payload['besoins'], 1)
        self.assertEqual(payload['writes'], 2)
        self.assertFalse(payload['truncated'])
        self.assertEqual(upsert_matching_record.call_count, 2)


if __name__ == '__main__':
    unittest.main()
