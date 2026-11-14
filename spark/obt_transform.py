"""Actual Spark joins. No Snowflake joins or pandas merges construct the OBT."""
from pyspark.sql import functions as F

TABLES={'f':'FACT_AFFINITY','s':'DIM_SOURCE','e':'DIM_EXPERIMENT',
        'g':'DIM_GEOMETRY','l':'DIM_PARTICIPANT_FEATURES','r':'DIM_PARTICIPANT_FEATURES'}
KEYS={'FACT_AFFINITY':'OBSERVATION_ID','DIM_SOURCE':'SOURCE_KEY','DIM_EXPERIMENT':'EXPERIMENT_KEY',
      'DIM_GEOMETRY':'GEOMETRY_ID','DIM_PARTICIPANT_FEATURES':'PARTICIPANT_KEY'}
JOINS=[('s','SOURCE_KEY','SOURCE_KEY'),('e','EXPERIMENT_KEY','EXPERIMENT_KEY'),
       ('g','GEOMETRY_ID','GEOMETRY_ID'),('l','LIGAND_PARTICIPANT_KEY','PARTICIPANT_KEY'),
       ('r','RECEPTOR_PARTICIPANT_KEY','PARTICIPANT_KEY')]

def projection(columns):
    result=[];seen=set()
    for alias,table in TABLES.items():
        for name in columns[table]:
            if alias=='s' and name=='SOURCE_KEY':continue
            if alias=='e' and name=='EXPERIMENT_KEY':continue
            if alias=='g' and name in columns['FACT_AFFINITY']:continue
            if alias in ('l','r') and name in ('PARTICIPANT_KEY','GEOMETRY_ID','PDB_ID','PARTNER','GEOMETRY_STATUS','CHAINS_JSON'):continue
            output=('LIGAND_' if alias=='l' else 'RECEPTOR_' if alias=='r' else '')+name
            if output in seen:raise ValueError('Duplicated output column: '+output)
            seen.add(output);result.append({'output':output,'alias':alias,'table':table,'column':name})
    return result

def require_unique(df,key):
    if df.filter(F.col(key).isNull()).limit(1).count():raise ValueError('NULL key: '+key)
    if df.groupBy(key).count().filter(F.col('count')>1).limit(1).count():raise ValueError('Duplicated key: '+key)

def validate_inputs(frames):
    counts={}
    for table,df in frames.items():
        require_unique(df,KEYS[table]);counts[table]=df.count()
    f=frames['FACT_AFFINITY']
    for alias,fk,pk in JOINS:
        dimension=frames[TABLES[alias]].select(pk)
        if f.filter(F.col(fk).isNotNull()).alias('fact').join(dimension.alias('dim'),F.col('fact.'+fk)==F.col('dim.'+pk),'left_anti').limit(1).count():
            raise ValueError('Orphan foreign key: '+fk)
    return counts

def assemble(frames,mapping):
    joined=frames['FACT_AFFINITY'].alias('f')
    for alias,fk,pk in JOINS:
        dimension=F.broadcast(frames[TABLES[alias]]).alias(alias)
        joined=joined.join(dimension,F.col('f.'+fk)==F.col(alias+'.'+pk),'left')
    return joined.select(*[F.col(m['alias']+'.'+m['column']).alias(m['output']) for m in mapping])

def validate_output(df,facts):
    expected=facts.count();actual=df.count()
    require_unique(df,'OBSERVATION_ID')
    if expected!=actual:raise ValueError('Join multiplied or removed observations')
    original=df.select(*facts.columns)
    if original.exceptAll(facts).limit(1).count() or facts.exceptAll(original).limit(1).count():
        raise ValueError('Fact attributes changed, including affinity or observation IDs')
    return {'rows':actual,'unique_observation_ids':actual,'fact_columns_preserved':True}
