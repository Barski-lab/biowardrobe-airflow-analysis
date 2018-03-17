from warnings import filterwarnings
from MySQLdb import Warning
filterwarnings('ignore', category=Warning)
from biowardrobe_airflow_analysis.biowardrobe import Settings


_settings = Settings.Settings()


suffixes = ['_isoforms`', '_genes`', '_common_tss`']

_settings.cursor.execute(
    """ SELECT l.uid 
         FROM labdata l, experimenttype e 
         WHERE e.id=experimenttype_id  and libstatus =12 AND deleted=0 and e.etype like 'RNA%' """)

rows = _settings.cursor.fetchall()

for row in rows:
    table_basename = f"`experiments`.`{row[0]}"
    print(row)
    for suffix in suffixes:
        _settings.cursor.execute(f""" ALTER TABLE {table_basename}{suffix}
                                DROP INDEX `refseq_id_idx`,
                                DROP INDEX `gene_id_idx` ,
                                DROP INDEX `chr_idx` ,
                                DROP INDEX `txStart_idx` ,
                                DROP INDEX `txEnd_idx`;                                
                                """)
        _settings.cursor.execute(f""" ALTER TABLE {table_basename}{suffix}
                                ADD INDEX `refseq_id_idx` USING BTREE (`refseq_id` ASC),
                                ADD INDEX `gene_id_idx` USING BTREE (`gene_id` ASC),
                                ADD INDEX `chr_idx` USING BTREE (`chrom` ASC),
                                ADD INDEX `txStart_idx` USING BTREE (`txStart` ASC),
                                ADD INDEX `txEnd_idx` USING BTREE (`txEnd` ASC);
                                """)
    _settings.conn.commit()
