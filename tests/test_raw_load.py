"""Pruebas de integridad antes de tocar Snowflake. La repeticion real se prueba en la cuenta."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from load_raw import inspect_batch
from source_inputs import write_jsonl


class RawInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name)
        self.batch = self.cache/'batches/test_batch'
        self.batch.mkdir(parents=True)
        (self.cache/'objects').mkdir()
        (self.batch/'source.txt').write_text('1A22\n1A22\n')
        source_sha = hashlib.sha256((self.batch/'source.txt').read_bytes()).hexdigest()
        summary = {'run_id':'test_batch','status':'PARTIAL','records':2,
                   'source_file':'source.txt','source_sha256':source_sha}
        (self.batch/'summary.json').write_text(json.dumps(summary))
        (self.batch/'requested_ids.json').write_text('["1A22"]')
        self.records = [{'source_record_id':str(i),'source_sha256':source_sha,'pdb_id':'1A22'} for i in (1,2)]
        write_jsonl(self.batch/'records.jsonl', self.records)
        self.resources = [{'pdb_id':'1A22','resource':kind,'status':'not_found'} for kind in ('entry','structure')]
        write_jsonl(self.batch/'download_manifest.jsonl',self.resources)

    def test_same_pdb_keeps_both_source_rows_and_not_found_receipts(self):
        result = inspect_batch(self.batch,self.cache)
        self.assertEqual(len(result[1]),2)
        self.assertEqual(len(result[2]),2)

    def test_duplicate_technical_key_rejected(self):
        write_jsonl(self.batch/'records.jsonl',[self.records[0]]*2)
        with self.assertRaisesRegex(ValueError,'Claves repetidas'):
            inspect_batch(self.batch,self.cache)

    def test_missing_manifest_resource_rejected(self):
        write_jsonl(self.batch/'download_manifest.jsonl',self.resources[:1])
        with self.assertRaisesRegex(ValueError,'manifiesto'):
            inspect_batch(self.batch,self.cache)

    def test_altered_original_rejected(self):
        (self.batch/'source.txt').write_text('Changed')
        with self.assertRaisesRegex(ValueError,'original'):
            inspect_batch(self.batch,self.cache)

    def test_corrupted_resource_rejected(self):
        sha = 'a'*64
        path = self.cache/f'objects/{sha}.json'
        path.write_text('{}')
        self.resources[0].update(status='downloaded',sha256=sha,path=f'objects/{sha}.json',bytes=2)
        write_jsonl(self.batch/'download_manifest.jsonl',self.resources)
        with self.assertRaisesRegex(ValueError,'Integridad'):
            inspect_batch(self.batch,self.cache)


if __name__ == '__main__':
    unittest.main()
