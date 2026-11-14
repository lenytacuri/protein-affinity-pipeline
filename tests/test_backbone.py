import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest
import math
import gemmi
import numpy as np
from backbone_core import extract_one,sequence_link,torsion,pick_atom,bond_angle


def residue(num,points,label='',label_seq=None):
    r=gemmi.Residue();r.name='ALA';r.seqid=gemmi.SeqId(num,' ');r.subchain='Ax';r.label_seq=label_seq or num
    for name,xyz in points.items():
        a=gemmi.Atom();a.name=name;a.element=gemmi.Element('N' if name=='N' else 'C');a.altloc=label or '\x00';a.occ=1.;a.pos=gemmi.Position(*xyz);r.add_atom(a)
    return r

def fixture():
    p=residue(1,{'C':(-1,0,0)})
    r=residue(2,{'N':(0,0,0),'CA':(0,1,0),'C':(1,1,1)})
    n=residue(3,{'N':(2,1,1),'CA':(2,2,1)})
    src={'residue_id':'g:0','geometry_id':'g','partner':'L','chain_id':'A','residue_number':2,'insertion_code':'','residue_name':'ALA','altloc':'','x':0,'y':1,'z':0}
    return p,r,n,src

class BackboneTests(unittest.TestCase):
    def test_all_measurements_with_unselected_neighbors(self):
        p,r,n,s=fixture();v=extract_one('A',r,p,n,s)
        self.assertEqual(v['phi_status'],'ok');self.assertEqual(v['psi_status'],'ok');self.assertEqual(v['omega_status'],'ok')
        self.assertAlmostEqual(v['n_ca_length'],1);self.assertAlmostEqual(v['ca_c_length'],math.sqrt(2))
        self.assertAlmostEqual(v['tau_deg'],90)
        self.assertAlmostEqual(v['phi_deg'],math.degrees(gemmi.calculate_phi_psi(p,r,n)[0]))
        self.assertAlmostEqual(v['psi_deg'],math.degrees(gemmi.calculate_phi_psi(p,r,n)[1]))
        self.assertAlmostEqual(v['omega_deg'],math.degrees(gemmi.calculate_omega(r,n)))
    def test_break_does_not_bridge(self):
        p,r,n,s=fixture();n[0].pos=gemmi.Position(20,1,1)
        v=extract_one('A',r,p,n,s)
        self.assertIsNotNone(v['phi_deg']);self.assertIsNone(v['psi_deg']);self.assertIsNone(v['omega_deg']);self.assertIsNone(v['peptide_cn_length'])
    def test_sequence_gap_even_if_close(self):
        p,r,n,s=fixture();n.label_seq=8
        self.assertIn('sequence_gap',extract_one('A',r,p,n,s)['psi_status'])
    def test_chain_end_and_missing_atom(self):
        p,r,n,s=fixture();v=extract_one('A',r,None,n,s)
        self.assertIsNone(v['phi_deg']);self.assertIsNotNone(v['psi_deg'])
        r.remove_atom('N','\x00',gemmi.Element('N'));v=extract_one('A',r,p,n,s)
        self.assertIsNone(v['phi_deg']);self.assertIsNone(v['psi_deg']);self.assertIsNone(v['tau_deg'])
    def test_conformers_not_mixed(self):
        p,r,n,s=fixture()
        for a in r:a.altloc='A'
        for a in n:a.altloc='B'
        s['altloc']='A';v=extract_one('A',r,p,n,s)
        self.assertIsNone(v['psi_deg']);self.assertIsNotNone(v['phi_deg'])
    def test_ca_identity_checked(self):
        p,r,n,s=fixture();s['x']=9
        with self.assertRaises(ValueError):extract_one('A',r,p,n,s)
    def test_degenerate_geometry_is_missing(self):
        r=residue(1,{'N':(0,0,0),'CA':(1,0,0),'C':(2,0,0)})
        self.assertIsNone(bond_angle(r[0],r[1],r[2]))
    def test_label_sequence_handles_author_insertions(self):
        p,r,n,s=fixture();p.seqid=gemmi.SeqId(50,'A');r.seqid=gemmi.SeqId(50,'B')
        self.assertEqual(sequence_link(p,r),'adjacent')
    def test_signed_dihedral_independent(self):
        for z in [-1,1]:
            r=residue(1,{'A':(1,0,0),'B':(0,0,0),'C':(0,1,0),'D':(0,1,z)})
            points=np.array([[a.pos.x,a.pos.y,a.pos.z] for a in r]);b0=points[0]-points[1];b1=points[2]-points[1];b2=points[3]-points[2]
            b1=b1/np.linalg.norm(b1);v=b0-np.dot(b0,b1)*b1;w=b2-np.dot(b2,b1)*b1
            expected=math.degrees(math.atan2(np.dot(np.cross(b1,v),w),np.dot(v,w)))
            self.assertAlmostEqual(torsion(list(r)),expected)

if __name__=='__main__':unittest.main()
