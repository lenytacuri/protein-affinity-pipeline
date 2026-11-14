"""Entrada reproducible del proyecto; solo requiere Python estandar y Docker Compose."""
import argparse
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def execute(*args):
    subprocess.run(list(args), cwd=ROOT, check=True)


def compose(*args):
    execute('docker', 'compose', *args)


def local_input(value, mode):
    if mode == 'reference':
        if value: raise ValueError('reference no acepta --input; para otro Excel usar curated.')
        return ''
    if not value: raise ValueError('curated y replay requieren --input.')
    path = Path(value)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(ROOT) or not path.exists():
        raise ValueError('La entrada debe existir dentro del proyecto.')
    if mode == 'curated' and (not path.is_file() or path.suffix.lower() != '.xlsx'):
        raise ValueError('curated requiere un archivo .xlsx.')
    if mode == 'replay' and not path.is_dir():
        raise ValueError('replay requiere la carpeta de un lote anterior.')
    return '/workspace/' + path.relative_to(ROOT).as_posix()


def setup(account):
    if not account or not re.fullmatch(r'[A-Za-z0-9_.-]+', account):
        raise ValueError('Usa --account ORGANIZACION-CUENTA, sin URL ni contrasena.')
    env = ROOT / '.env'
    if env.exists():
        raise FileExistsError('.env ya existe; se conserva. Editarlo si se necesita otra cuenta.')
    values = (ROOT / '.env.example').read_text()
    values = values.replace('organization-account', account)
    values = values.replace('/ruta/absoluta/protein affinity/pset_2', str(ROOT))
    values = values.replace('REEMPLAZAR_con_clave_aleatoria_1', secrets.token_urlsafe(32))
    values = values.replace('REEMPLAZAR_con_otra_clave_aleatoria', secrets.token_urlsafe(32))
    fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream: stream.write(values)
    execute(sys.executable, 'scripts/prepare_snowflake_auth.py')
    print('Configuracion local preparada. Ejecutar en TU Snowflake: sql/01_bootstrap.sql y sql/02_service_user.local.sql.')
    print('Las credenciales locales de Kestra estan en .env; no se muestran ni se versionan.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'build', 'start', 'check', 'run', 'template'])
    parser.add_argument('--account')
    parser.add_argument('--mode', choices=['reference', 'curated', 'replay'], default='reference')
    parser.add_argument('--input')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--no-wait', action='store_true')
    args = parser.parse_args()
    if args.action == 'setup': setup(args.account); return
    if not (ROOT / '.env').exists(): raise FileNotFoundError('Ejecutar setup o configurar .env primero.')
    if args.action == 'build':
        compose('config', '--quiet')
        # geometry y spark dependen de imagenes locales; construir en este orden.
        compose('build', 'pipeline', 'dbt')
        compose('build', 'geometry')
        compose('build', 'spark')
    elif args.action == 'start':
        compose('up', '-d', '--wait', 'postgres', 'kestra')
    elif args.action == 'check':
        compose('run', '--rm', 'pipeline', 'python', 'scripts/check_snowflake.py')
    elif args.action == 'template':
        compose('run', '--rm', 'pipeline', 'python', 'scripts/batch_contract.py',
                '--template', 'data/incoming/plantilla_mediciones.xlsx')
    else:
        path = local_input(args.input, args.mode)
        if args.mode == 'replay' and args.refresh:
            raise ValueError('replay reutiliza originales; no acepta --refresh.')
        options = ['--run', '--input', 'mode=' + args.mode, '--input', 'input_path=' + path,
                   '--input', 'refresh=' + str(args.refresh).lower()]
        if not args.no_wait: options += ['--wait', '--wait-timeout', '43200']
        compose('run', '--rm', 'pipeline', 'python', 'scripts/kestra_flow.py',
                'kestra/affinity_pipeline.yml', *options)


if __name__ == '__main__':
    main()
