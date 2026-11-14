import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import Workbook
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from source_inputs import read_source
from rcsb_download import fetch_resource


class Response:
    def __init__(self, content=b'', status=200, headers=None):
        self.content, self.status_code = content, status
        self.headers, self.url = headers or {}, 'https://data.rcsb.org/test'

    def iter_content(self, chunk_size):
        yield self.content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f'HTTP {self.status_code}')

    def close(self):
        pass


class Session:
    def __init__(self, responses):
        self.responses, self.calls = iter(responses), 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return next(self.responses)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_measurements_preserved_but_download_ids_deduplicated(self):
        path = self.root/'source.xlsx'
        book = Workbook()
        book.active.append(['PDB', 'KD(M)'])
        for row in [('1a22', 1e-9), (' 1A22 ', 2e-9), ('invalid', 3e-9)]:
            book.active.append(row)
        book.save(path)
        rows, ids, _ = read_source(path, 'excel')
        again, _, _ = read_source(path, 'excel')
        self.assertEqual(len(rows), 3)
        self.assertEqual(ids, ['1A22'])
        self.assertEqual(len({x['source_record_id'] for x in rows}), 3)
        self.assertEqual(rows, again)
        self.assertEqual(rows[1]['payload']['PDB'], ' 1A22 ')
        self.assertIsNone(rows[2]['pdb_id'])

    def test_successful_cache_skips_network_and_repairs_corruption(self):
        response = Response(b'{"rcsb_id":"1A22"}')
        session = Session([response, response])
        first = fetch_resource(session, self.root, '1A22', 'entry')
        cached = fetch_resource(session, self.root, '1A22', 'entry')
        self.assertEqual(cached['status'], 'cached')
        self.assertEqual(session.calls, 1)
        (self.root/first['path']).write_bytes(b'broken')
        repaired = fetch_resource(session, self.root, '1A22', 'entry')
        self.assertEqual(repaired['status'], 'downloaded')
        self.assertEqual(session.calls, 2)
        self.assertEqual(repaired['sha256'], first['sha256'])

    def test_404_is_recorded_without_retries(self):
        session = Session([Response(status=404)])
        result = fetch_resource(session, self.root, '1A22', 'entry')
        self.assertEqual(result['status'], 'not_found')
        self.assertEqual(session.calls, 1)
        self.assertFalse((self.root/'index/1A22/entry.json').exists())

    @patch('rcsb_download.time.sleep')
    def test_rate_limit_then_success(self, sleep):
        session = Session([Response(status=429, headers={'Retry-After': '2'}),
                           Response(b'{"rcsb_id":"1A22"}')])
        result = fetch_resource(session, self.root, '1A22', 'entry')
        self.assertEqual(result['status'], 'downloaded')
        self.assertEqual(result['attempts_this_run'], 2)
        sleep.assert_called_once_with(2)

    @patch('rcsb_download.time.sleep')
    def test_wrong_entry_never_enters_cache(self, sleep):
        session = Session([Response(b'{"rcsb_id":"4HHB"}')]*2)
        result = fetch_resource(session, self.root, '1A22', 'entry', attempts=2)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse((self.root/'index/1A22/entry.json').exists())
        self.assertEqual(list((self.root/'objects').iterdir()), [])

    def test_gzip_structure_identity_and_coordinates(self):
        content = gzip.compress(b'data_1A22\n_entry.id 1A22\nloop_\n_atom_site.Cartn_x\n_atom_site.Cartn_y\n_atom_site.Cartn_z\n1 2 3\n')
        result = fetch_resource(Session([Response(content)]), self.root, '1A22', 'structure')
        self.assertEqual(result['status'], 'downloaded')
        self.assertTrue((self.root/result['path']).exists())

    def test_refresh_preserves_previous_object(self):
        session = Session([Response(b'{"rcsb_id":"1A22","revision":1}'),
                           Response(b'{"rcsb_id":"1A22","revision":2}')])
        old = fetch_resource(session, self.root, '1A22', 'entry')
        new = fetch_resource(session, self.root, '1A22', 'entry', refresh=True)
        self.assertNotEqual(old['sha256'], new['sha256'])
        self.assertTrue((self.root/old['path']).exists())
        self.assertTrue((self.root/new['path']).exists())

    def test_id_list_is_not_a_labeled_measurement_table(self):
        path = self.root/'ids.txt'
        path.write_text('# comentario\n1a22\npdb_00001a22\n4HHB\n')
        rows, ids, _ = read_source(path, 'ids')
        self.assertEqual(ids, ['1A22', '4HHB'])
        self.assertTrue(all(r['input_kind']=='structure_request' for r in rows))

    def test_unexpected_json_shape_is_recorded_as_failure(self):
        result = fetch_resource(Session([Response(b'[]')]), self.root, '1A22', 'entry', attempts=1)
        self.assertEqual(result['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
