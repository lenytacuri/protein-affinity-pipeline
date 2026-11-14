"""Geometria CA: dos grupos de cadenas de autor, primer modelo, distancias en A.

Q1 usa las distancias minimas por participante, interpolacion lineal y filtro <.
No infiere enlaces, no reconstruye ensamblajes ni aplica mutaciones.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import time

import gemmi
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

PARAMETERS = {'algorithm':'ca_min_q1_v2','atom':'CA','model':'first',
    'chain_namespace':'author','assembly':'deposited_coordinates',
    'quantile':0.25,'quantile_method':'linear','comparison':'strict_less_than',
    'pairs':'all_cross_pairs_between_q1_selected_residues','reference_threshold_angstrom':10.0,
    'altloc':'highest_positive_occupancy_then_blank_then_lexical'}
AA20 = 'ACDEFGHIKLMNPQRSTVWY'


def digest_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def parse_chains(value):
    if not isinstance(value,str) or not value.strip(): return []
    result=[s.strip() for s in value.split(',')]
    if any(not re.fullmatch(r'[A-Za-z0-9]+',s) for s in result) or len(set(result))!=len(result):
        return []
    return sorted(result)  # Case is significant; multi-character author IDs stay intact.


def clean_char(value):
    return value.strip().replace('\x00','')


def read_residues(path, ligand, receptor):
    st=gemmi.read_structure(str(path))
    if len(st)==0: raise ValueError('no_models')
    model=st[0]
    chains={c.name for c in model}
    missing=sorted((set(ligand)|set(receptor))-chains)
    if missing: raise ValueError('missing_chains:'+','.join(missing))
    if not ligand or not receptor: raise ValueError('invalid_chain_annotation')
    if set(ligand)&set(receptor): raise ValueError('overlapping_participants')
    selected=[]; counts={'amino_acids_without_ca':0,'alternate_ca_residues':0,'nonstandard_residues':0}
    keys=set()
    for chain in model:
        if chain.name not in set(ligand)|set(receptor): continue
        side='L' if chain.name in ligand else 'R'
        for res in chain:
            info=gemmi.find_tabulated_residue(res.name)
            if not info.is_amino_acid(): continue
            atoms=[a for a in res if a.name=='CA' and a.element.name=='C' and a.occ>0
                   and np.isfinite([a.pos.x,a.pos.y,a.pos.z]).all()]
            if not atoms:
                counts['amino_acids_without_ca']+=1; continue
            atoms.sort(key=lambda a:(-a.occ, bool(clean_char(a.altloc)),clean_char(a.altloc)))
            atom=atoms[0]
            counts['alternate_ca_residues']+=int(len(atoms)>1)
            key=(chain.name,res.seqid.num,clean_char(res.seqid.icode))
            if key in keys: raise ValueError('ambiguous_residue_identity')
            keys.add(key)
            aa=info.one_letter_code.upper()
            if aa not in AA20: aa='X'
            standard=res.name in {'ALA','CYS','ASP','GLU','PHE','GLY','HIS','ILE','LYS','LEU','MET','ASN','PRO','GLN','ARG','SER','THR','VAL','TRP','TRP','TYR'}
            counts['nonstandard_residues']+=int(not standard)
            selected.append({'partner':side,'chain_id':chain.name,'residue_number':res.seqid.num,
                'insertion_code':key[2],'residue_name':res.name,'amino_acid':aa,
                'is_standard':standard,'altloc':clean_char(atom.altloc),'occupancy':float(atom.occ),
                'x':atom.pos.x,'y':atom.pos.y,'z':atom.pos.z})
    selected.sort(key=lambda r:(r['partner'],r['chain_id'],r['residue_number'],r['insertion_code']))
    for chain in ligand+receptor:
        if not any(r['chain_id']==chain for r in selected): raise ValueError('chain_without_protein_ca:'+chain)
    return selected,dict(counts,model_count=len(st),selected_model=str(model.num))


def measure(a,b):
    """Exact nearest neighbours; pairs among Q1-selected residues, without distance cap."""
    ta,tb=cKDTree(a),cKDTree(b)
    da,ib=tb.query(a,k=1,eps=0,workers=1)
    db,ia=ta.query(b,k=1,eps=0,workers=1)
    qa=float(np.quantile(da,0.25,method='linear'))
    qb=float(np.quantile(db,0.25,method='linear'))
    li,ri=np.flatnonzero(da<qa),np.flatnonzero(db<qb)
    pairs=np.empty(len(li)*len(ri),dtype=[('i',np.int64),('j',np.int64),('v',np.float64)])
    pairs['i']=np.repeat(li,len(ri));pairs['j']=np.tile(ri,len(li))
    pairs['v']=cdist(a[li],b[ri]).ravel()
    return da,ib,db,ia,qa,qb,pairs


def composition(rows):
    counts={aa:0 for aa in AA20+'X'}
    for r in rows: counts[r['amino_acid']]+=1
    return {'count':len(rows),'counts':counts,
        'fractions':{a:(n/len(rows) if rows else None) for a,n in counts.items()}}


def write_lines(path,rows):
    with gzip.open(path,'wt',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,separators=(',',':'),allow_nan=False)+'\n')


def calculate_job(job):
    start=time.monotonic()
    out=Path(job['output_dir'])/job['geometry_id'];out.mkdir(parents=True,exist_ok=True)
    cached=out/'result.json'
    if cached.exists():
        result=json.loads(cached.read_text())
        if all((out/name).exists() and digest_file(out/name)==sha for name,sha in result.get('files',{}).items()):
            return result
    result={k:job[k] for k in ['geometry_id','pdb_id','structure_sha256','ligand_chains','receptor_chains','code_sha256']}
    result.update(parameters=PARAMETERS,files={})
    try:
        rows,stats=read_residues(job['path'],job['ligand_chains'],job['receptor_chains'])
        left=[r for r in rows if r['partner']=='L'];right=[r for r in rows if r['partner']=='R']
        a=np.array([[r[k] for k in ('x','y','z')] for r in left]);b=np.array([[r[k] for k in ('x','y','z')] for r in right])
        da,ib,db,ia,qa,qb,pairs=measure(a,b)
        for i,r in enumerate(rows): r.update(geometry_id=job['geometry_id'],residue_index=i)
        for group,other,dist,neighbour,q in [(left,right,da,ib,qa),(right,left,db,ia,qb)]:
            for i,r in enumerate(group):
                r.update(min_distance=float(dist[i]),nearest_residue_index=other[int(neighbour[i])]['residue_index'],
                    q1_threshold=q,selected_q1=bool(dist[i]<q),within_10=bool(dist[i]<10))
        def pair_rows():
            for p in pairs:
                l,r=left[int(p['i'])],right[int(p['j'])]
                yield {'geometry_id':job['geometry_id'],'ligand_residue_index':l['residue_index'],
                       'receptor_residue_index':r['residue_index'],'distance':float(p['v']),
                       'both_selected_q1':l['selected_q1'] and r['selected_q1']}
        write_lines(out/'residues.jsonl.gz',rows)
        write_lines(out/'pairs.jsonl.gz',pair_rows())
        result.update(status='computed',stats=stats,n_ligand=len(left),n_receptor=len(right),
            q1_ligand=qa,q1_receptor=qb,min_distance=float(da.min()),
            selected_pairs_lt10=int(np.sum(pairs['v']<10)),selected_pair_count=len(pairs),
            n_selected_q1_ligand=int(np.sum(da<qa)),n_selected_q1_receptor=int(np.sum(db<qb)),
            has_ca_contacts_10=bool(da.min()<10),biological_assembly_validated=False,
            composition_ligand_q1=composition([r for r in left if r['selected_q1']]),
            composition_receptor_q1=composition([r for r in right if r['selected_q1']]),
            files={name:digest_file(out/name) for name in ['residues.jsonl.gz','pairs.jsonl.gz']})
    except (ValueError,RuntimeError) as exc:
        # Scientific/structure problems retain an explicit result; unexpected programming errors fail the run.
        result.update(status='structure_not_usable',reason=str(exc)[:500])
    result['seconds']=round(time.monotonic()-start,4)
    temporary=out/'result.tmp';temporary.write_text(json.dumps(result,indent=2,allow_nan=False));temporary.replace(cached)
    return result


def mutation_check(annotation, residues, status):
    if not annotation or str(annotation).strip().lower() in {'none','nan','unknown','n/a','null'}:
        return {'status':'not_annotated','items':[]}
    if status!='computed': return {'status':'structure_unavailable','items':[]}
    lookup={(r['chain_id'],r['residue_number'],r['insertion_code']):r for r in residues}
    items=[]
    for text in str(annotation).split(','):
        text=text.strip()
        m=re.fullmatch(r'([A-Za-z0-9]+)_([A-Z])(-?\d+)([A-Za-z]?)([A-Z])',text)
        if not m:
            items.append({'annotation':text,'status':'unparsed'});continue
        chain,wt,num,icode,mut=m.groups();r=lookup.get((chain,int(num),icode))
        observed=r['amino_acid'] if r else None
        state=('residue_missing' if r is None else 'target_present' if observed==mut else
               'reference_residue_present' if observed==wt else 'residue_mismatch')
        items.append({'annotation':text,'chain':chain,'position':int(num),'insertion_code':icode,
            'from':wt,'to':mut,'observed':observed,'status':state})
    states={i['status'] for i in items}
    state='target_residues_present' if states=={'target_present'} else 'reference_geometry_only' if states<= {'target_present','reference_residue_present'} else 'needs_review'
    return {'status':state,'items':items}
