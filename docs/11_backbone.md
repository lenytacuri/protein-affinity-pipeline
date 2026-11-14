# Geometria interna del esqueleto peptidico

Resultados de la ultima ejecucion validada: `reports/backbone.md`.

## Dos tablas nuevas en Silver

- **BACKBONE_RESIDUES**: una fila por residuo de INTERFACE_RESIDUES con SELECTED_Q1=true. Guarda mediciones individuales, atomos usados y motivos de ausencia.
- **BACKBONE_FEATURES**: una fila por GEOMETRY_ID y PARTNER (L/R). Guarda resumenes de tamaño fijo para modelos clasicos. Incluye participantes de geometria no disponible con valores NULL.

Las tablas previas y la seleccion Q1 no se modifican. Las observaciones experimentales se conectan con estos resumenes por GEOMETRY_ID; se deben unir L y R por separado para mantener una fila por observacion en la OBT.

## Identificacion de los atomos originales

Cada trabajo usa el SHA-256 de la estructura de STRUCTURE_GEOMETRY. Si el archivo no esta en el cache local, se recupera su copia exacta de RAW.SOURCE_FILES y se comprueba el hash.

Se lee el primer modelo, igual que en la geometria CA. Cadena de autor, numero de residuo, codigo de insercion, nombre y ALTLOC identifican el residuo. Antes de calcular se comprueba que el CA encontrado tenga las mismas coordenadas que Silver (tolerancia 1e-6 A). Una discrepancia de identidad detiene la ejecucion; no se asigna otro residuo silenciosamente.

Los vecinos pueden no estar seleccionados por Q1. Se usan sus atomos originales sin agregarlos a la seleccion.

## Medidas individuales

Para el residuo i:

| Medida | Atomos | Unidad |
|---|---|---|
| PHI_DEG | C(i-1), N(i), CA(i), C(i) | Grados |
| PSI_DEG | N(i), CA(i), C(i), N(i+1) | Grados |
| OMEGA_DEG | CA(i), C(i), N(i+1), CA(i+1) | Grados |
| TAU_DEG | N(i), CA(i), C(i) | Grados |
| N_CA_LENGTH | N(i), CA(i) | Angstroms |
| CA_C_LENGTH | CA(i), C(i) | Angstroms |
| PEPTIDE_CN_LENGTH | C(i), N(i+1) | Angstroms |

OMEGA se asigna al enlace **saliente** hacia el siguiente residuo. Al comparar con otros programas hay que comprobar si usan esa convencion o la del enlace entrante.

ATOMS conserva coordenadas, etiqueta de conformacion y ocupacion de los atomos utilizados. PREVIOUS_RESIDUE y NEXT_RESIDUE conservan identidad de los vecinos. Los valores individuales se almacenan con ocho decimales; esa precision numerica no implica precision experimental equivalente.

## Continuidad y conformaciones

Se exige que los vecinos inmediatos pertenezcan a la misma cadena/subcadena y sean aminoacidos. Cuando existe LABEL_SEQ, sus posiciones deben ser consecutivas. Si falta, se usa como aproximacion la consecutividad de numeros de autor y codigos de insercion, dejando el estado CONNECTED_AUTHOR_INFERRED.

Ademas, la distancia C-N del enlace debe estar entre **0.8 y 1.8 A**. Es una regla conservadora de conectividad/calidad versionada, no un nuevo criterio para seleccionar la interfaz. Un salto de secuencia o una distancia fuera del intervalo impide calcular las torsiones que cruzan ese enlace.

Los atomos deben tener ocupacion positiva y coordenadas finitas. Se permiten atomos con el mismo ALTLOC del CA o compartidos sin etiqueta. Cuando el CA no tiene etiqueta, se utilizan solo atomos sin etiqueta; se prefiere informar una medida ausente antes que elegir otra conformacion sin evidencia. Tambien se rechazan geometrias degeneradas que no definen un angulo.

## Resumen para ML clasico

Para cada torsion PHI/PSI/OMEGA se calcula:

- Numero de valores validos y cobertura respecto a N_SELECTED.
- Media del seno y media del coseno: columnas recomendadas para representar orientacion en ML sin salto artificial de -180 a 180 grados.
- Longitud del vector medio R, entre 0 y 1.
- Varianza circular 1-R: cero indica concentracion; cerca de uno, dispersion.
- Media circular en grados, obtenida con ATAN2. Si R <= 1e-8, la orientacion media queda NULL porque no esta bien definida.

Para TAU y las tres longitudes se calcula cantidad valida, cobertura, media y desviacion **poblacional**. Con un solo valor valido, la desviacion es cero. N_PHI_PSI_COMPLETE cuenta residuos que tienen ambos angulos disponibles.

Las medias de seno/coseno usan terminos decimales redondeados a 12 posiciones; los resumenes lineales usan agregacion decimal. Esto evita que el orden del procesamiento paralelo produzca diferencias irrelevantes al reconstruir las tablas.

No se calculan asignaciones de helice/lamina, regiones favorecidas de Ramachandran, energias ni cambios conformacionales de mutantes. La estructura sigue siendo la observada y deben consultarse los estados de mutaciones existentes antes de decidir elegibilidad para entrenamiento.

## Estados

BACKBONE_STATUS del resumen:

| Estado | Significado |
|---|---|
| complete | Todos los seleccionados tienen phi, psi, omega y tau. |
| partial_angles | Una o varias de esas medidas faltan en parte de la seleccion. |
| no_valid_angles | Ninguna de esas medidas esta disponible. |
| empty_selection | No hay residuos que cumplan el filtro Q1 estricto. |
| geometry_unavailable | No habia geometria CA utilizable; cantidades y medidas NULL. |

PHI_STATUS, PSI_STATUS, OMEGA_STATUS y TAU_STATUS detallan por residuo si la medida es `ok`, si hay extremos de cadena, saltos de secuencia, ruptura por distancia, atomos ausentes/incompatibles o geometria degenerada. No se rellenan angulos ausentes.

## Reproducir

Con Silver y quimica ya construidas, desde la carpeta del proyecto:

```sh
docker compose up -d postgres kestra
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/build_backbone.yml --run --wait
```

Para una prueba pequeña sin publicar tablas:

```sh
docker compose run --rm geometry python scripts/build_backbone.py --pilot 24
```

Pruebas matematicas y de conectividad:

```sh
docker compose run --rm geometry python -m unittest discover -s tests -p test_backbone.py -v
```

El flujo completo `kestra/build_silver.yml` ejecuta primero geometria CA/quimica y despues backbone. Cada etapa tiene sus propios reintentos. Las distancias CA no se recalculan al ejecutar solamente build_backbone.

El cache de backbone usa la estructura, los residuos Q1 exactos, los parametros y el codigo. Docker usa todos sus nucleos disponibles (8 en esta laptop) mediante procesos independientes. dbt ejecuta las transformaciones y las pruebas en Snowflake.

## Codigo y evidencia

- `scripts/backbone_core.py`: atomos, conectividad y geometria.
- `scripts/build_backbone.py`: entradas, procesos, carga y verificacion.
- `sql/11_backbone_inputs.sql`: identifica residuos Q1 desde Silver.
- `dbt/models/backbone/`: tablas individuales y resumen.
- `dbt/tests/backbone_*.sql`: conservacion, coherencia y comprobaciones.
- `sql/12_view_backbone.sql`: consultas listas para Snowflake.
- `reports/backbone/`: logs, resultados de pruebas y motivos de ausencia.

Las pruebas comparan las formulas con Gemmi y geometria independiente, comprueban extremos/rupturas/ALTLOC, la identidad del CA, las longitudes desde coordenadas y el caso circular 179/-179 grados. Dos construcciones dbt deben tener el mismo contenido; RAW, Bronze y las seis tablas anteriores de Silver deben permanecer intactas.

Referencia tecnica: [Gemmi, analisis estructural](https://gemmi.readthedocs.io/en/stable/analysis.html).
