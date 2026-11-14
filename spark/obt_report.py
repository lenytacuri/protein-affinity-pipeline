from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def write_report(s):
    lines=['# OBT construida con Spark','',f"Ejecucion `{s['run']}`: **SUCCESS**.",
      f"Tabla: **{s['table']}**. Shape: **{s['rows']} filas x {s['columns']} columnas**.",
      'Grano: una fila por observacion experimental original. Todas las observaciones se conservan.',
      f"Spark {s['spark_version']}, modo **{s['master']}**, paralelismo disponible **{s['parallelism']}**. Docker en la Mac; no es un cluster remoto.",'',
      '## Validaciones','',
      '- Claves unicas, no nulas y relaciones validas antes de unir.',
      '- LEFT JOIN sin multiplicar ni eliminar observaciones.',
      '- Todas las columnas del hecho se conservan, incluidas Kd, pKd y estados.',
      '- Segunda construccion Spark con otra particion de entrada: contenido identico.',
      '- Escritura y lectura Parquet: contenido identico.',
      '- Todas las columnas cargadas coinciden con una comprobacion independiente contra Gold en Snowflake.',
      '- RAW, Bronze, Silver y Gold permanecen intactas.',
      '- Publicacion atomica de una copia validada; no se acumulan filas al repetir.',
      f"- Comparacion con una ejecucion anterior de iguales entradas: **{s['previous_same_inputs_verified']}**.",'',
      '## Columnas','',
      'Se conservan las columnas del hecho; se agregan fuente, condiciones experimentales y geometria general. Las caracteristicas por participante usan LIGAND_ y RECEPTOR_.',
      'Cada columna tiene procedencia en column_lineage.json. No hay imputacion, escalado, split ni seleccion final de predictores.',
      'pKd es la etiqueta; Kd es su transformacion inversa y no debe incluirse como predictor. Identificadores, fuentes, referencias y estados no se incorporan automaticamente a X.',
      'Las variantes y casos de geometria incompleta conservan sus indicadores; tener una fila en la OBT no equivale a estar aprobado para entrenamiento.',
      '', '## Ejecucion real','',
      'El conector Python exporta cada tabla Gold por separado a Parquet. Spark lee esos archivos y ejecuta las cinco uniones. El conector carga despues los Parquet producidos por Spark a Snowflake.',
      'Las consultas SQL de uniones se usan exclusivamente para verificar el resultado, no para construirlo.',
      'Este transporte local esta pensado para el ejercicio y requiere espacio en disco; para terabytes se usaria almacenamiento compartido y un cluster/conector distribuido.',
      '', f"Evidencia: reports/obt/{s['run']}/ (plan, eventos Spark, esquema, linaje, manifest y resumen).",
      'Codigo de uniones: spark/obt_transform.py. Ejecucion: spark/build_obt.py.',
      'Guia: docs/13_obt.md. Consultas: sql/14_view_obt.sql.']
    (ROOT/'reports/obt.md').write_text('\n'.join(lines)+'\n')
