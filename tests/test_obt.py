"""Small Spark fixtures catch destructive joins and role swaps before publication."""
import sys
from pathlib import Path
import unittest
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'spark'))
from pyspark.sql import SparkSession,functions as F
from obt_transform import projection,validate_inputs,assemble,validate_output,require_unique

class ObtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark=SparkSession.builder.master('local[2]').appName('obt-tests').config('spark.ui.enabled','false').config('spark.sql.shuffle.partitions','2').getOrCreate()
        cls.spark.sparkContext.setLogLevel('ERROR')
    @classmethod
    def tearDownClass(cls):cls.spark.stop()
    def frames(self):
        s=self.spark
        return {
          'FACT_AFFINITY':s.createDataFrame([
             ('o1','s1','e1','g1','g1:L','g1:R',Decimal('0.00000001'),8.0),
             ('o2','s1','e1','g1','g1:L','g1:R',Decimal('0.00000002'),7.698970004336019),
             ('o3','s1','e1',None,None,None,Decimal('0.00000100'),6.0)],
             'OBSERVATION_ID string,SOURCE_KEY string,EXPERIMENT_KEY string,GEOMETRY_ID string,LIGAND_PARTICIPANT_KEY string,RECEPTOR_PARTICIPANT_KEY string,KD_M decimal(20,10),PKD double'),
          'DIM_SOURCE':s.createDataFrame([('s1','test')],'SOURCE_KEY string,SOURCE_DATASET string'),
          'DIM_EXPERIMENT':s.createDataFrame([('e1',None)],'EXPERIMENT_KEY string,TEMPERATURE_K double'),
          'DIM_GEOMETRY':s.createDataFrame([('g1',2.5)],'GEOMETRY_ID string,MIN_DISTANCE_ANGSTROM double'),
          'DIM_PARTICIPANT_FEATURES':s.createDataFrame([('g1:L','g1','L',0.1),('g1:R','g1','R',0.9)],'PARTICIPANT_KEY string,GEOMETRY_ID string,PARTNER string,CHEM_PROPERTY_COVERAGE double')}
    def test_preserves_repeated_complex_null_geometry_and_roles(self):
        frames=self.frames();validate_inputs(frames)
        output=assemble(frames,projection({k:v.columns for k,v in frames.items()}))
        self.assertEqual(validate_output(output,frames['FACT_AFFINITY'])['rows'],3)
        rows={r.OBSERVATION_ID:r.asDict() for r in output.collect()}
        self.assertEqual(rows['o1']['LIGAND_CHEM_PROPERTY_COVERAGE'],0.1)
        self.assertEqual(rows['o2']['RECEPTOR_CHEM_PROPERTY_COVERAGE'],0.9)
        self.assertIsNone(rows['o3']['LIGAND_CHEM_PROPERTY_COVERAGE'])
        self.assertEqual(rows['o2']['KD_M'],Decimal('0.00000002'))
        self.assertIsNone(rows['o1']['TEMPERATURE_K'])
    def test_duplicate_dimension_key_rejected(self):
        f=self.frames();d=f['DIM_PARTICIPANT_FEATURES']
        with self.assertRaisesRegex(ValueError,'Duplicated key'):require_unique(d.unionByName(d),'PARTICIPANT_KEY')
    def test_missing_dimension_rejected(self):
        f=self.frames();f['DIM_GEOMETRY']=f['DIM_GEOMETRY'].filter('false')
        with self.assertRaisesRegex(ValueError,'Orphan foreign key'):validate_inputs(f)
    def test_chain_columns_come_from_geometry_once(self):
        cols={k:v.columns for k,v in self.frames().items()}
        cols['DIM_GEOMETRY']+=['LIGAND_CHAINS_JSON','RECEPTOR_CHAINS_JSON']
        cols['DIM_PARTICIPANT_FEATURES']+=['CHAINS_JSON']
        mapping=projection(cols)
        chains=[m for m in mapping if m['output'].endswith('CHAINS_JSON')]
        self.assertEqual(len(chains),2)
        self.assertTrue(all(m['table']=='DIM_GEOMETRY' for m in chains))
    def test_changed_affinity_rejected(self):
        f=self.frames();output=assemble(f,projection({k:v.columns for k,v in f.items()})).withColumn('PKD',F.lit(0.0))
        with self.assertRaisesRegex(ValueError,'Fact attributes changed'):validate_output(output,f['FACT_AFFINITY'])

if __name__=='__main__':unittest.main()
