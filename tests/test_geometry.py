"""Pruebas independientes de geometria, empates y anotaciones."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest
import numpy as np
from scipy.spatial.distance import cdist
from geometry_core import measure,parse_chains,mutation_check,read_residues

class GeometryTest(unittest.TestCase):
    def test_against_full_distance_matrix(self):
        rng=np.random.default_rng(41)
        a=rng.normal(size=(37,3))*15;b=rng.normal(size=(53,3))*15
        da,ib,db,ia,qa,qb,pairs=measure(a,b)
        d=cdist(a,b)
        np.testing.assert_allclose(da,d.min(axis=1))
        np.testing.assert_allclose(db,d.min(axis=0))
        np.testing.assert_allclose(d[np.arange(len(a)),ib],da)
        self.assertAlmostEqual(qa,float(np.quantile(d.min(axis=1),.25)))
        self.assertAlmostEqual(qb,float(np.quantile(d.min(axis=0),.25)))
        self.assertEqual(set(zip(pairs['i'],pairs['j'])),set((int(i),int(j)) for i in np.flatnonzero(da<qa) for j in np.flatnonzero(db<qb)))
    def test_selected_pairs_are_not_capped_at_25_angstrom(self):
        a=np.array([[1000.*i,0,0] for i in range(8)])
        b=a+np.array([[x,0,0] for x in [1,2,20,30,40,50,60,70]])
        *_,pairs=measure(a,b)
        self.assertEqual(len(pairs),4)
        self.assertGreater(pairs['v'].max(),900)

    def test_strict_boundary_and_ties(self):
        a=np.array([[0.,0,0],[0,2,0]]);b=a+[25.,0,0]
        da,_,db,_,qa,qb,pairs=measure(a,b)
        self.assertEqual(len(pairs),0)
        self.assertEqual(int((da<qa).sum()),0)
        self.assertEqual(int((db<qb).sum()),0)
    def test_chains_are_case_sensitive_and_multicharacter(self):
        self.assertEqual(parse_chains('AA, a, H'),['AA','H','a'])
        self.assertEqual(parse_chains('H,H'),[])
        self.assertEqual(parse_chains(None),[])
    def test_mutation_does_not_change_structure(self):
        residues=[{'chain_id':'A','residue_number':38,'insertion_code':'','amino_acid':'L'}]
        self.assertEqual(mutation_check('A_L38G',residues,'computed')['status'],'reference_geometry_only')
        self.assertEqual(mutation_check('A_G38L',residues,'computed')['status'],'target_residues_present')
        self.assertEqual(mutation_check('A_A38G',residues,'computed')['status'],'needs_review')
        self.assertEqual(mutation_check(None,residues,'computed')['status'],'not_annotated')
        self.assertEqual(residues[0]['amino_acid'],'L')
    def test_atom_selection_uses_carbon_ca_and_highest_occupancy(self):
        import gemmi, tempfile
        st=gemmi.Structure();model=gemmi.Model('1')
        for chain_name in ['A','B']:
            chain=gemmi.Chain(chain_name);res=gemmi.Residue()
            res.name='ALA';res.seqid=gemmi.SeqId(4,'A')
            for alt,occ,x in [('A',.3,1.),('B',.7,2.)]:
                atom=gemmi.Atom();atom.name='CA';atom.element=gemmi.Element('C')
                atom.altloc=alt;atom.occ=occ;atom.pos=gemmi.Position(x,0,0);res.add_atom(atom)
            chain.add_residue(res)
            calcium=gemmi.Residue();calcium.name='CA';calcium.seqid=gemmi.SeqId(5,' ')
            atom=gemmi.Atom();atom.name='CA';atom.element=gemmi.Element('Ca');atom.pos=gemmi.Position(10,0,0)
            calcium.add_atom(atom);chain.add_residue(calcium);model.add_chain(chain)
        st.add_model(model)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.pdb';st.write_pdb(str(path))
            rows,stats=read_residues(path,['A'],['B'])
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['x'],2.)
        self.assertEqual(rows[0]['altloc'],'B')
        self.assertEqual(rows[0]['insertion_code'],'A')
        self.assertEqual(stats['alternate_ca_residues'],2)

    def test_known_structure_and_missing_chain(self):
        import json
        root=Path(__file__).resolve().parents[1]/'data/rcsb'
        receipt=json.loads((root/'index/1A22/structure.json').read_text())
        rows,stats=read_residues(root/receipt['path'],['A'],['B'])
        a=np.array([[r[k] for k in ('x','y','z')] for r in rows if r['partner']=='L'])
        b=np.array([[r[k] for k in ('x','y','z')] for r in rows if r['partner']=='R'])
        da,*_=measure(a,b)
        np.testing.assert_allclose(da,cdist(a,b).min(axis=1))
        self.assertGreater(len(a),100)
        with self.assertRaisesRegex(ValueError,'missing_chains'):
            read_residues(root/receipt['path'],['NONEXISTENT'],['B'])

if __name__=='__main__': unittest.main()
