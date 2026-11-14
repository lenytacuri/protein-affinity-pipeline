"""Prepara una clave LOCAL y el SQL publico que el titular ejecuta en Snowflake."""
import os
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    secrets = root / '.secrets'
    secrets.mkdir(mode=0o700, exist_ok=True)
    secrets.chmod(0o700)
    private = secrets / 'snowflake_key.p8'
    old_mask = os.umask(0o077)
    try:
        if not private.exists():
            subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt',
                            'rsa_keygen_bits:2048', '-out', str(private)],
                           check=True, capture_output=True)
        private.chmod(0o600)
        pem = subprocess.check_output(['openssl', 'pkey', '-in', str(private), '-pubout'], text=True)
    finally:
        os.umask(old_mask)
    public_key = ''.join(line for line in pem.splitlines() if not line.startswith('---'))
    sql = root / 'sql' / '02_service_user.local.sql'
    sql.parent.mkdir(exist_ok=True)
    sql.write_text(
        '-- Ejecutar por el titular de la cuenta. Contiene SOLO la clave publica.\n'
        '-- Crea acceso automatico limitado al rol del proyecto.\n'
        '-- CREATE USER falla si el usuario ya existe: no reemplaza sus credenciales.\n'
        'USE ROLE SECURITYADMIN;\n'
        'CREATE USER PPA_SERVICE\n'
        '  TYPE = SERVICE\n'
        "  DEFAULT_ROLE = 'PPA_PIPELINE'\n"
        "  DEFAULT_WAREHOUSE = 'PPA_WH'\n"
        "  DEFAULT_NAMESPACE = 'PROTEIN_AFFINITY.RAW'\n"
        f"  RSA_PUBLIC_KEY = '{public_key}';\n"
        'GRANT ROLE PPA_PIPELINE TO USER PPA_SERVICE;\n'
        'DESCRIBE USER PPA_SERVICE;\n', encoding='utf-8')
    print('Clave privada conservada localmente; no se muestra ni se envia.')
    print(f'SQL publico para ejecutar: {sql}')


if __name__ == '__main__':
    main()
