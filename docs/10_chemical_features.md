# Caracteristicas quimicas de los residuos seleccionados

Tabla: `PROTEIN_AFFINITY.SILVER.INTERFACE_CHEMISTRY`.
Reporte de ejecucion y estados: `reports/chemistry.md`.

## Una fila por geometria y participante

Cada GEOMETRY_ID tiene dos filas: PARTNER=L (ligando) y PARTNER=R (receptor). No se cambia la agrupacion de cadenas del Excel ni se deduplican observaciones. La seleccion es la ya calculada: distancia minima del CA < Q1 de su participante.

Los residuos proceden de INTERFACE_RESIDUES con SELECTED_Q1=true. Esta ampliacion usa SQL en Snowflake; no vuelve a calcular distancias ni modifica las cinco tablas anteriores. Tambien esta incluida en las futuras ejecuciones completas de Silver.

## Variables

| Columna o familia | Definicion |
|---|---|
| CHEMISTRY_ID | Identificador unico: geometria + participante. |
| FEATURE_VERSION | Version de definiciones: chemistry_v1. |
| FEATURE_BASIS | observed_structure_q1: propiedades de residuos observados seleccionados. |
| Q1_THRESHOLD_ANGSTROM | Umbral que selecciono los residuos de ese participante. |
| N_SELECTED | Numero total de residuos seleccionados. |
| N_SUPPORTED | Seleccionados canonicos, con nombre y codigo compatibles con los 20 aminoacidos de la tabla de propiedades. |
| N_NONSTANDARD | Residuos seleccionados marcados como no estandar. |
| N_UNSUPPORTED | Seleccionados sin propiedades asignadas. Incluye los no estandar. |
| PROPERTY_COVERAGE | N_SUPPORTED/N_SELECTED. NULL si no hay seleccion o geometria. |
| N_AA_A ... N_AA_Y | Cantidad de cada aminoacido soportado. Codigos de una letra. |
| FRACTION_AA_A ... FRACTION_AA_Y | Cantidad dividida por N_SUPPORTED. Suman 1 cuando hay residuos soportados. |
| N_NONPOLAR / FRACTION_NONPOLAR | G,A,V,L,I,M,P,F,W. |
| N_POLAR_UNCHARGED / FRACTION_POLAR_UNCHARGED | S,T,C,N,Q,Y. Categoria convencional, no estado de protonacion medido. |
| N_ACIDIC / FRACTION_ACIDIC | D,E. |
| N_BASIC / FRACTION_BASIC | K,R,H. |
| N_AROMATIC_RING / FRACTION_AROMATIC_RING | F,W,Y,H, incluyendo el anillo de histidina. |
| N_SULFUR_CONTAINING / FRACTION_SULFUR_CONTAINING | C,M. No cuenta enlaces disulfuro. |
| N_ALIPHATIC_AVIL / FRACTION_ALIPHATIC_AVIL | A,V,I,L. Subconjunto explicito, no pretende clasificar todas las cadenas alifaticas. |
| MEAN_KD_HYDROPATHY | Media de la escala Kyte-Doolittle en los residuos soportados. KD aqui significa Kyte-Doolittle, no Kd de afinidad. |
| AA_ENTROPY_BITS | -suma(p*log2(p)) de las fracciones de aminoacidos. Diversidad de composicion; no entropia termodinamica. |

La media de hidropatia se almacena con 6 decimales. Cada termino de diversidad se redondea a 12 decimales antes de sumarlo, para que el orden de agregacion en paralelo no cambie el resultado.

Las cuatro clases nonpolar/polar_uncharged/acidic/basic son mutuamente excluyentes y cubren los 20 aminoacidos. Los grupos aromatic_ring/sulfur_containing/aliphatic_avil se solapan con esas clases: no deben sumarse entre si como si fueran una particion.

Las clasificaciones de polaridad son una convencion explicita y versionada. No se derivan del signo de la escala de hidropatia: por ejemplo, Cys tiene hidropatia positiva en Kyte-Doolittle, pero se incluye en la clase polar_uncharged de esta convencion.

## Ausencias y residuos modificados

- complete: todos los seleccionados tienen propiedades asignadas.
- partial_coverage: algunos seleccionados no tienen propiedades soportadas. Se informa cobertura; las medias y fracciones usan los soportados.
- no_supported_residues: hay seleccion pero ninguno es soportado. Las cantidades canonicas son cero, las fracciones y medias son NULL.
- empty_selection: el filtro estricto Q1 no selecciono residuos. Cantidades cero; fracciones y medias NULL.
- geometry_unavailable: no se pudo calcular la geometria. Cantidades, fracciones y medias NULL, no cero.

No se asignan propiedades estandar a MSE u otros residuos modificados, aunque el parser haya proporcionado un codigo de una letra equivalente. Los nombres originales siguen en INTERFACE_RESIDUES.

## Interpretacion quimica

Estas variables describen identidad y composicion de residuos observados. No estiman carga neta real a un pH dado, energias, puentes de hidrogeno, area accesible ni contactos atomicos. Histidina pertenece a la clase basica, pero no se supone que este siempre cargada positivamente.

No se aplican las mutaciones del Excel a los residuos. Las observaciones conservan MUTATION_STRUCTURE_STATUS para distinguir geometria de referencia y casos que necesitan revision. Tampoco se modifican ensamblajes biologicos.

La escala de hidropatia se transcribe de [SIB ExPASy, Kyte-Doolittle](https://web.expasy.org/protscale/pscale/Hydropath.Doolittle.html), referencia original: Kyte J., Doolittle R.F., J. Mol. Biol. 157:105-132 (1982). [IMGT](https://www.imgt.org/IMGTeducation/Aide-memoire/_UK/aminoacids/charge/) explica la dependencia de la carga respecto al pH y pKa. El mapa exacto de categorias de este proyecto esta en el macro de propiedades.

## Reproducir y consultar

Desde la carpeta del proyecto, con Silver ya creada:

```sh
docker compose up -d postgres kestra
docker compose run --rm pipeline python scripts/kestra_flow.py kestra/build_chemistry.yml --run --wait
```

El flujo ejecuta dbt, pruebas, reconstruccion y comparacion de contenido. Verifica que las tablas anteriores no cambien. La ejecucion completa `build_silver` tambien incluye esta tabla; no exige ejecutar ambos flujos.

Codigo principal: `dbt/models/silver/silver_interface_chemistry.sql`.
Propiedades de referencia: `dbt/macros/amino_acid_properties.sql`.
Consulta y ejemplo de union sin duplicar observaciones: `sql/10_view_chemistry.sql`.
