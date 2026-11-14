"""Pruebas de limites de ingreso y aislamiento entre ejecuciones, sin Snowflake."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import requests
from types import SimpleNamespace
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pipeline_stage as stages
from batch_contract import validate_measurements
from kestra_flow import wait_for_api


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(stages, 'ROOT', self.root); self.root_patch.start()
        self.source = self.root / 'curated.xlsx'
        self.headers = ['PDB', 'KD(M)', 'Ligand Chains', 'Receptor Chains', 'Source Data Set', 'Complex ID']

    def tearDown(self):
        self.root_patch.stop(); self.temp.cleanup()

    def excel(self, rows, headers=None):
        book = Workbook(); book.active.append(headers or self.headers)
        for row in rows: book.active.append(row)
        book.save(self.source)

    def test_pdb_only_is_rejected_before_ingestion(self):
        self.excel([['1A22']], ['PDB'])
        with self.assertRaisesRegex(ValueError, 'Faltan columnas'): validate_measurements(self.source)

    def test_repeated_complex_measurements_and_missing_kd_are_preserved(self):
        self.excel([['1A22', 1e-9, 'A', 'B', 'paper', 'obs1'],
                    ['1A22', None, 'A', 'B', 'paper', 'obs2']])
        result = validate_measurements(self.source)
        self.assertEqual((result['records'], result['unique_pdb_ids']), (2, 1))

    def test_invalid_pdb_prevents_downstream_bronze_failure(self):
        self.excel([['bad', 1e-9, 'A', 'B', 'paper', 'obs1']])
        with self.assertRaisesRegex(ValueError, 'Fila 2'): validate_measurements(self.source)

    def test_snapshots_are_isolated_and_retry_preserves_original(self):
        self.excel([['1A22', 1e-9, 'A', 'B', 'paper', 'obs1']])
        one = self.root / 'one'; two = self.root / 'two'; one.mkdir(); two.mkdir()
        initial = stages.prepare(one, 'curated', str(self.source), False)
        self.excel([['1A22', 2e-9, 'A', 'B', 'paper', 'obs2']])
        other = stages.prepare(two, 'curated', str(self.source), False)
        retried = stages.prepare(one, 'curated', str(self.source), False)
        self.assertEqual(initial, retried)
        self.assertNotEqual(initial['source_sha256'], other['source_sha256'])
        self.assertNotEqual(initial['source_path'], other['source_path'])

    def test_retry_rejects_changed_snapshot_or_parameters(self):
        self.excel([['1A22', 1e-9, 'A', 'B', 'paper', 'obs1']])
        folder = self.root / 'one'; folder.mkdir()
        info = stages.prepare(folder, 'curated', str(self.source), False)
        with self.assertRaisesRegex(ValueError, 'otros parametros'):
            stages.prepare(folder, 'curated', str(self.source), True)
        Path(info['source_path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'modificada'):
            stages.prepare(folder, 'curated', str(self.source), False)

    def test_duplicate_observation_labels_are_rejected_before_raw(self):
        self.excel([['1A22', 1e-9, 'A', 'B', 'paper', 'obs1'],
                    ['1A22', 2e-9, 'A', 'B', 'paper', 'obs1']])
        with self.assertRaisesRegex(ValueError, 'Complex ID repetido'):
            validate_measurements(self.source)

    @patch('kestra_flow.time.sleep')
    def test_startup_waits_through_unavailable_api(self, sleep):
        session = Mock()
        session.get.side_effect = [requests.ConnectionError(), SimpleNamespace(status_code=503),
                                   SimpleNamespace(status_code=404)]
        self.assertEqual(wait_for_api(session, 'http://kestra/flow').status_code, 404)
        self.assertEqual(session.get.call_count, 3)

    def test_wrong_kestra_credentials_fail_without_waiting(self):
        session = Mock(); session.get.return_value.status_code = 401
        with self.assertRaisesRegex(RuntimeError, 'rechazo el acceso'):
            wait_for_api(session, 'http://kestra/flow')
        self.assertEqual(session.get.call_count, 1)

    def test_replay_cannot_silently_refresh_originals(self):
        with self.assertRaisesRegex(ValueError, 'refresh=false'):
            stages.prepare(self.root, 'replay', 'data/rcsb/batches/x', True)

    def test_paths_outside_project_are_rejected(self):
        with self.assertRaises(ValueError): stages.project_path('../outside.xlsx')


if __name__ == '__main__': unittest.main()
