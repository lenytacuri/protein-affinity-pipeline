"""Comprueba autenticacion y permisos sin cargar ni modificar datos."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
import snowflake.connector


def connect():
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / '.env')
    required = ['SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER', 'SNOWFLAKE_ROLE',
                'SNOWFLAKE_WAREHOUSE', 'SNOWFLAKE_DATABASE', 'SNOWFLAKE_PRIVATE_KEY_FILE']
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise ValueError('Falta configurar: ' + ', '.join(missing))
    key_file = Path(os.environ['SNOWFLAKE_PRIVATE_KEY_FILE'])
    if not key_file.is_absolute():
        key_file = root / key_file
    if not key_file.is_file():
        raise FileNotFoundError('No se encontro la clave privada en la ruta configurada.')
    return snowflake.connector.connect(
        account=os.environ['SNOWFLAKE_ACCOUNT'], user=os.environ['SNOWFLAKE_USER'],
        role=os.environ['SNOWFLAKE_ROLE'], warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
        database=os.environ['SNOWFLAKE_DATABASE'], schema='RAW',
        authenticator='SNOWFLAKE_JWT', private_key_file=str(key_file),
        login_timeout=30, network_timeout=60,
        session_parameters={'QUERY_TAG': 'protein-affinity-pset2',
                            'STATEMENT_TIMEOUT_IN_SECONDS': 300})


def main():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE()')
            account, user, role, database = cur.fetchone()
            cur.execute('SHOW SCHEMAS IN DATABASE PROTEIN_AFFINITY')
            columns = [column[0].lower() for column in cur.description]
            schemas = [dict(zip(columns, row))['name'] for row in cur.fetchall()]
            expected = {'RAW', 'BRONZE', 'SILVER', 'GOLD', 'ANALYTICS'}
            if not expected.issubset(schemas):
                raise RuntimeError(f'Esquemas no visibles: {sorted(expected-set(schemas))}')
            print(json.dumps({'connection': 'ok', 'account': account, 'user': user,
                              'role': role, 'database': database,
                              'project_schemas': sorted(expected)}, indent=2))


if __name__ == '__main__':
    main()
