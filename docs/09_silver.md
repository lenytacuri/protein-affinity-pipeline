# Silver: limpieza y geometria reproducible

Ejecucion inicial validada: `reports/silver.md`. Ampliaciones: `reports/chemistry.md` y `reports/backbone.md`.

## Regla acordada: percentil 25, no 25 angstroms

1. Se identifican los dos participantes usando los grupos Ligand Chains y Receptor Chains del Excel. Un participante puede incluir varias cadenas.
2. Se lee el primer modelo del mmCIF depositado y se identifican los carbonos alfa (CA) de residuos aminoacidos. Se conservan cadena de autor, numero de residuo y codigo de insercion.
3. Para cada CA del ligando se calcula su distancia minima a cualquier CA del receptor. Se hace tambien el calculo inverso.
4. Se calcula Q1 por separado sobre las distancias minimas de cada participante, con interpolacion lineal.
5. Se seleccionan los residuos cuya distancia minima es estrictamente menor que el Q1 de su participante.
6. Se guardan todos los pares entre los residuos seleccionados del ligando y los seleccionados del receptor, sin limite adicional en angstroms.

Un ejemplo: si Q1 del ligando es 12.4 A y el del receptor 8.7 A, cada participante usa su propio umbral. Los umbrales se calculan de nuevo para cada geometria. No se calcula Q1 sobre todas las distancias entre pares.

Los empates pueden producir menos de 25% de residuos, incluso cero. No se modifica el umbral para forzar una cantidad. Los pares entre seleccionados pueden tener distancias grandes: cada residuo se selecciona por su vecino mas cercano, no por estar cerca de todos los seleccionados del otro participante.

Se conserva una bandera WITHIN_10 para comparacion geometrica con el criterio previo de 10 A; no determina la seleccion Q1. No hay corte fijo de 25 A.

## Tablas finales en PROTEIN_AFFINITY.SILVER

| Tabla | Una fila representa | Para que sirve |
|---|---|---|
| AFFINITY_OBSERVATIONS | Una observacion del Excel | Kd, pKd, temperatura y estados de datos/estructura; conserva las observaciones originales |
| OBSERVATION_GEOMETRY | Vinculo de una observacion con una geometria | Varias mediciones pueden usar una geometria sin fusionar sus etiquetas experimentales |
| STRUCTURE_GEOMETRY | Un archivo + grupos de cadenas + version de calculo | Umbrales Q1, conteos, composicion y problemas detectados |
| INTERFACE_RESIDUES | Un CA utilizable de los participantes | Identidad, coordenadas, vecino mas cercano, distancia minima y seleccion Q1; incluye tambien los no seleccionados |
| RESIDUE_PAIRS | Un par L-R de residuos seleccionados por Q1 | Distancia y referencias a ambos residuos; no demuestra enlaces quimicos |
| INTERFACE_CHEMISTRY | Una geometria y un participante (L/R) | Composicion, clases de polaridad e hidropatia de residuos seleccionados; ver docs/10_chemical_features.md |
| BACKBONE_RESIDUES | Un residuo seleccionado por Q1 | Angulos y longitudes del esqueleto, atomos usados y motivos de medidas ausentes |
| BACKBONE_FEATURES | Una geometria y un participante (L/R) | Resumenes circulares de torsiones, medias/desviaciones de longitudes y cobertura; ver docs/11_backbone.md |

GEOMETRY_FILES y BACKBONE_FILES son stages de artefactos, no tablas de datos. dbt lee sus archivos JSON comprimidos para construir las tablas.

## Limpieza tabular

El SQL conserva todas las filas de Bronze y sus PAYLOAD originales. Interpreta temperatura y su anotacion `assumed`, normaliza ausencias de metodo, distingue PMID de referencias textuales o TBD, y calcula pKd = -log10(Kd en mol/L) cuando Kd es positivo y finito. No imputa datos ni elimina observaciones por repetir PDB.

pKd es la etiqueta experimental a predecir, no una caracteristica de entrada del futuro modelo.

## CPU y repeticion

El calculo usa procesos locales en Docker: uno por nucleo disponible, respetando la cuota CPU del contenedor. En esta laptop se detectaron 8. Las bibliotecas internas usan un solo hilo por proceso para evitar multiplicar hilos. Snowflake ejecuta SQL y almacena tablas; las distancias se calculan en la laptop.

Se reutiliza un calculo solo si coinciden archivo estructural (SHA-256), PDB, grupos de cadenas, codigo y parametros. Las mutaciones no se aplican a las coordenadas: varias observaciones pueden compartir geometria de referencia, pero mantienen sus IDs, afinidades y estados separados.

El cache no es obligatorio: si faltan archivos locales, el programa recupera las estructuras por su hash desde RAW.SOURCE_FILES. RAW y Bronze deben estar previamente cargadas en la cuenta del usuario que reproduce el proyecto.

## Validacion estructural y limites

- Se preserva la distincion entre cadenas mayusculas y minusculas y entre codigos de insercion.
- Si hay CA alternativos, se elige ocupacion positiva mas alta; los empates prefieren conformacion sin etiqueta y despues orden lexical.
- Se registran residuos sin CA, residuos no estandar y numero de modelos. No se reconstruyen coordenadas ausentes.
- Cadenas inexistentes, participantes superpuestos o identidades ambiguas producen un estado explicito. No se eliminan las observaciones asociadas.
- Se usa la estructura depositada. No se generan ensamblajes biologicos ni se confirma que toda proximidad corresponda a una interaccion biologica.
- Las mutaciones se comparan con los residuos observados. `reference_geometry_only` indica que la estructura conserva al menos un residuo anterior a la mutacion. `target_residues_present` comprueba identidades en esas posiciones, pero no demuestra que la conformacion o todas las condiciones experimentales correspondan al ensayo.
- `not_annotated` significa que no hay anotacion; no prueba tipo silvestre.
- La composicion corresponde a los aminoacidos observados en la estructura. No representa la composicion corregida de un mutante.
- CA sirve para proximidad de residuos. No se calculan energias, puentes de hidrogeno ni cargas dependientes del pH.

## Ejecutar desde el proyecto

```sh
cd "/Users/lenytacuri/protein affinity/pset_2"
docker compose build dbt
docker compose build geometry
docker compose up -d postgres kestra
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/build_silver.yml --run --wait
```

Para probar solo 32 geometrías sin publicar tablas:

```sh
docker compose run --rm geometry python scripts/run_silver.py --pilot 32
```

Para ejecutar las pruebas independientes del calculo:

```sh
docker compose run --rm geometry python -m unittest discover -s tests -p test_geometry.py -v
```

La construccion de Silver tambien ejecuta pruebas dbt: conservacion de observaciones, claves, relaciones, Q1 calculado independientemente en SQL, distancias frente a coordenadas, pertenencia a cadenas y conteos de pares. La ejecucion de Kestra reconstruye las tablas dos veces y compara su contenido, ademas de comprobar que RAW y Bronze no cambiaron.

## Archivos principales

- `scripts/geometry_core.py`: lectura de CA, distancias, Q1 y comparacion de mutaciones.
- `scripts/run_silver.py`: paralelizacion, cache, carga, dbt y reportes.
- `sql/07_silver_inputs.sql`: entradas desde Bronze sin multiplicar observaciones.
- `dbt/models/silver/`: transformaciones SQL y descripcion de columnas.
- `dbt/tests/silver_*.sql`: pruebas de calidad y conservacion.
- `kestra/build_silver.yml`: coordinacion y reintentos.
- `sql/08_view_silver.sql`: consultas para revisar Silver en Snowflake.

Referencias de las bibliotecas: [Gemmi](https://gemmi.readthedocs.io/en/stable/mol.html), [vecinos exactos en SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query.html). Se comprueba el resultado frente a una matriz completa de distancias en las pruebas.
