"""Descarga verificable del Excel principal. AlphaFold queda fuera del alcance vigente."""
import argparse
import hashlib
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=Path('data/reference'))
args = parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=True)
files=[
    ('PPB-Affinity.xlsx','PPB-Affinity.zenodo-14271435.xlsx','032a5ce1f24212aef5cdedf8117ef084'),
]
for remote,name,expected in files:
    url='https://zenodo.org/records/14271435/files/'+remote+'?download=1'
    path=args.output_dir/name
    if path.exists():
        if hashlib.md5(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Existe un archivo diferente; se conserva sin sobrescribir: '+str(path))
        print('Referencia ya disponible y verificada:',path)
    else:
        with urllib.request.urlopen(url,timeout=60) as response:
            data=response.read()
        if hashlib.md5(data).hexdigest()!=expected:
            raise RuntimeError('La descarga no coincide con la huella publicada: '+name)
        with path.open('xb') as stream:
            stream.write(data)
        print('Referencia descargada y verificada:',path)
