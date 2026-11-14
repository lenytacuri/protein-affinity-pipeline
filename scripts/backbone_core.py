"""Backbone geometry of existing Q1 residues; original first model and CA conformer.

phi_i=Cprev,N_i,CA_i,C_i; psi_i=N_i,CA_i,C_i,Nnext;
omega_i=CA_i,C_i,Nnext,CAnext (outgoing peptide bond).
"""
import gzip
import json
import math
from pathlib import Path

import gemmi
import numpy as np
from geometry_core import clean_char,digest_file,write_lines

PARAMETERS={'version':'backbone_v1','model':'first','selection':'existing_selected_q1',
 'altloc':'CA_label_or_blank_only; blank_CA_requires_blank_atoms',
 'peptide_cn_min':0.8,'peptide_cn_max':1.8,'angle_unit':'degrees',
 'omega_convention':'outgoing_CA_C_Nnext_CAnext',
 'sequence':'adjacent_label_seq_in_same_subchain; author_number_fallback',
 'coordinate_match_tolerance':1e-6}
MEASUREMENTS=['phi_deg','psi_deg','omega_deg','tau_deg','n_ca_length','ca_c_length','peptide_cn_length']


def residue_key(chain,res):return (chain,res.seqid.num,clean_char(res.seqid.icode))


def pick_atom(res,name,label):
    if res is None:return None
    element='N' if name=='N' else 'C'
    candidates=[a for a in res if a.name==name and a.element.name==element and a.occ>0
       and clean_char(a.altloc) in ({label,''} if label else {''})
       and all(math.isfinite(x) for x in (a.pos.x,a.pos.y,a.pos.z))]
    candidates.sort(key=lambda a:(clean_char(a.altloc)!=label,-a.occ,clean_char(a.altloc)))
    return candidates[0] if candidates else None


def pos(atom):return np.array([atom.pos.x,atom.pos.y,atom.pos.z])


def length(a,b):
    if a is None or b is None:return None
    d=float(np.linalg.norm(pos(a)-pos(b)))
    return d if math.isfinite(d) and d>1e-10 else None


def torsion(atoms):
    if any(a is None for a in atoms):return None
    points=[pos(a) for a in atoms]
    u,v,w=np.diff(points,axis=0)
    if min(np.linalg.norm(np.cross(u,v)),np.linalg.norm(np.cross(v,w)),np.linalg.norm(v))<1e-10:return None
    d=math.degrees(gemmi.calculate_dihedral(*(a.pos for a in atoms)))
    return d if math.isfinite(d) else None


def bond_angle(n,ca,c):
    if any(a is None for a in (n,ca,c)):return None
    u,v=pos(n)-pos(ca),pos(c)-pos(ca)
    if min(np.linalg.norm(u),np.linalg.norm(v),np.linalg.norm(np.cross(u,v)))<1e-10:return None
    d=math.degrees(gemmi.calculate_angle(n.pos,ca.pos,c.pos))
    return d if math.isfinite(d) else None


def sequence_link(left,right):
    if left is None or right is None:return 'chain_end'
    if not gemmi.find_tabulated_residue(left.name).is_amino_acid() or not gemmi.find_tabulated_residue(right.name).is_amino_acid():return 'non_amino_acid_neighbor'
    if left.subchain!=right.subchain:return 'different_subchain'
    if left.label_seq is not None and right.label_seq is not None:
        return 'adjacent' if right.label_seq==left.label_seq+1 else 'sequence_gap'
    ln,rn=left.seqid.num,right.seqid.num
    li,ri=clean_char(left.seqid.icode),clean_char(right.seqid.icode)
    consecutive=(rn==ln+1) or (rn==ln and ((not li and ri=='A') or (len(li)==len(ri)==1 and ord(ri)==ord(li)+1)))
    return 'adjacent_author_inferred' if consecutive else 'sequence_adjacency_unresolved'


def peptide_link(left,right,c,n):
    state=sequence_link(left,right)
    if state not in ('adjacent','adjacent_author_inferred'):return state
    if c is None or n is None:return 'missing_or_incompatible_peptide_atom'
    d=length(c,n)
    if d is None or not PARAMETERS['peptide_cn_min']<=d<=PARAMETERS['peptide_cn_max']:return 'peptide_distance_break'
    return 'connected' if state=='adjacent' else 'connected_author_inferred'


def is_connected(state):return state in ('connected','connected_author_inferred')


def atom_record(a):
    if a is None:return None
    return {'xyz':[a.pos.x,a.pos.y,a.pos.z],'altloc':clean_char(a.altloc),'occupancy':float(a.occ)}


def extract_one(chain,res,previous,following,source):
    label=source['altloc'] or ''
    ca=pick_atom(res,'CA',label)
    if ca is None or clean_char(ca.altloc)!=label or res.name!=source['residue_name']:
        raise ValueError('Selected CA identity does not match the source structure')
    if np.max(np.abs(pos(ca)-np.array([source[k] for k in ('x','y','z')])))>PARAMETERS['coordinate_match_tolerance']:
        raise ValueError('Selected CA coordinates do not match the source structure')
    n,c=pick_atom(res,'N',label),pick_atom(res,'C',label)
    pc=pick_atom(previous,'C',label)
    nn,nca=pick_atom(following,'N',label),pick_atom(following,'CA',label)
    before=peptide_link(previous,res,pc,n);after=peptide_link(res,following,c,nn)
    result={k:source[k] for k in ('residue_id','geometry_id','partner','chain_id','residue_number','insertion_code','residue_name','altloc')}
    result.update(previous_link_status=before,next_link_status=after,
        previous_residue=None if previous is None else {'number':previous.seqid.num,'insertion_code':clean_char(previous.seqid.icode),'name':previous.name},
        next_residue=None if following is None else {'number':following.seqid.num,'insertion_code':clean_char(following.seqid.icode),'name':following.name},
        atoms={k:atom_record(a) for k,a in {'previous_c':pc,'n':n,'ca':ca,'c':c,'next_n':nn,'next_ca':nca}.items()})
    for name,atoms,link,prefix in [
        ('phi_deg',[pc,n,ca,c],before,'previous'),
        ('psi_deg',[n,ca,c,nn],after,'next'),
        ('omega_deg',[ca,c,nn,nca],after,'next')]:
        value=torsion(atoms) if is_connected(link) else None
        reason='ok' if value is not None else prefix+'_'+link if not is_connected(link) else 'missing_or_degenerate_atoms'
        result[name]=value;result[name.replace('_deg','_status')]=reason
    tau=bond_angle(n,ca,c)
    result.update(tau_deg=tau,tau_status='ok' if tau is not None else 'missing_or_degenerate_atoms',
        n_ca_length=length(n,ca),ca_c_length=length(ca,c),
        peptide_cn_length=length(c,nn) if is_connected(after) else None)
    return result


def extract_rows(path,sources):
    st=gemmi.read_structure(str(path));model=st[0]
    locations={}
    for chain in model:
        for i,res in enumerate(chain):
            key=residue_key(chain.name,res)
            # Only entries requested by Silver matter; duplicate keys are rejected below.
            locations.setdefault(key,[]).append((chain,i,res))
    rows=[]
    for src in sources:
        key=(src['chain_id'],src['residue_number'],src['insertion_code'])
        matches=locations.get(key,[])
        matches=[item for item in matches if item[2].name==src['residue_name']]
        if len(matches)!=1:raise ValueError(f'Cannot uniquely locate selected residue: {key}')
        chain,i,res=matches[0]
        prev=chain[i-1] if i else None
        nxt=chain[i+1] if i+1<len(chain) else None
        rows.append(extract_one(chain.name,res,prev,nxt,src))
    return rows


def calculate_backbone(job):
    folder=Path(job['cache'])/job['job_key'];folder.mkdir(parents=True,exist_ok=True)
    meta=folder/'result.json';output=folder/'backbone.jsonl.gz'
    if meta.exists() and output.exists():
        result=json.loads(meta.read_text())
        if result['sha256']==digest_file(output):return result
    rows=extract_rows(job['path'],job['residues'])
    for r in rows:r.update(backbone_version=PARAMETERS['version'],backbone_code_sha256=job['code_sha256'],structure_sha256=job['structure_sha256'])
    write_lines(output,rows)
    result={'geometry_id':job['geometry_id'],'job_key':job['job_key'],'rows':len(rows),'sha256':digest_file(output),'path':str(output)}
    temporary=folder/'result.tmp';temporary.write_text(json.dumps(result));temporary.replace(meta)
    return result
