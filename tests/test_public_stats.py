import unittest
from unittest.mock import patch

import app


class PublicStatsTest(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    @patch.object(app, 'fetch_table_records')
    @patch.object(app, 'get_eures_stats_config')
    @patch.object(app, 'get_form_config')
    def test_public_stats_aggregates_monthly_and_breakdowns(self, get_form_config, get_eures_stats_config, fetch_table_records):
        def fake_config(form_id, role=None):
            if form_id != 'eures-beta':
                return None
            return {
                'doc_id': 'doc-eures',
                'table_id': 'ignored',
                'api_key': 'api-key',
            }

        get_form_config.side_effect = fake_config
        get_eures_stats_config.return_value = {
            'doc_id': 'doc-eures',
            'table_id': 'Pilotage_EURES_Mensuel',
            'api_key': 'api-key',
        }

        def fake_fetch(doc_id, table_id, headers, limit=5000):
            if table_id == app.EURES_CANDIDATS_TABLE:
                return [
                    {'fields': {
                        'tally_submitted_at': '2026-01-03T10:00:00Z',
                        'pays': 'Luxembourg | Allemagne',
                        'metier': 'Vente et commerce',
                        'mobilite': 'Transfrontalière',
                    }},
                    {'fields': {
                        'tally_submitted_at': '2026-02-04T10:00:00Z',
                        'pays': 'Luxembourg',
                        'metier': 'Vente et commerce',
                        'mobilite': 'Transfrontalière',
                    }},
                ]
            if table_id == app.EURES_BESOINS_TABLE:
                return [
                    {'fields': {
                        'tally_submitted_at': '2026-01-10T10:00:00Z',
                        'pays': 'Luxembourg',
                        'poste': 'Vente et commerce',
                    }},
                ]
            if table_id == app.EURES_MATCHINGS_TABLE:
                return [
                    {'fields': {
                        'date_calcul': '2026-01-11T08:00:00Z',
                        'statut': 'auto_envoyable',
                    }},
                    {'fields': {
                        'date_calcul': '2026-02-05T08:00:00Z',
                        'statut': 'a_valider',
                    }},
                ]
            if table_id == 'Pilotage_EURES_Mensuel':
                return [
                    {'fields': {
                        'mois': '2026-01',
                        'candidats_contactes': 3,
                        'candidatures_transmises_employeur': 2,
                        'embauches': 1,
                    }},
                ]
            return []

        fetch_table_records.side_effect = fake_fetch

        response = self.client.get('/api/forms/eures-beta/public-stats')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['totals'], {
            'candidats': 2,
            'besoins_employeurs': 1,
            'matchings': 2,
            'candidats_contactes': 3,
            'candidatures_transmises_employeur': 2,
            'embauches': 1,
        })
        self.assertEqual(payload['monthly'], [
            {
                'mois': '2026-01',
                'candidats': 1,
                'besoins_employeurs': 1,
                'matchings': 1,
                'candidats_contactes': 3,
                'candidatures_transmises_employeur': 2,
                'embauches': 1,
            },
            {
                'mois': '2026-02',
                'candidats': 1,
                'besoins_employeurs': 0,
                'matchings': 1,
                'candidats_contactes': 0,
                'candidatures_transmises_employeur': 0,
                'embauches': 0,
            },
        ])
        self.assertTrue(payload['manual_stats_table']['configured'])
        self.assertEqual(payload['breakdowns']['matchings_par_statut'], [
            {'label': 'Autres', 'count': 2},
        ])


if __name__ == '__main__':
    unittest.main()
