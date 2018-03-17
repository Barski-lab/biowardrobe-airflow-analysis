"""Strategy pattern to run BaseUploader.execute depending on types of files to be uploaded"""

import warnings
import os
import types
import MySQLdb
import string
import glob
from .biow_exceptions import BiowUploadException
from .utils import biowardrobe_settings


class BaseUploader:
    def __init__(self, conn, cursor, func=None):
        self.conn = conn
        self.cursor = cursor
        self.settings = biowardrobe_settings(cursor)
        if func is not None:
            self.execute = types.MethodType(func, self)


def upload_results_to_db(upload_set, uid, output_folder, conn, cursor):
    """Call execute function for all created BaseUploader"""
    for key, value in upload_set.items():
        try:
            BaseUploader(conn, cursor, value).execute(uid, os.path.join(output_folder, key.format(uid)))
        except Exception as ex:
            raise BiowUploadException(uid, message="Failed to upload {}  : {}".format(key.format(uid), str(ex)))


def upload_results_to_db2(upload_rules, uid, output_folder, conn, cursor):
    """Call execute function for all created BaseUploader"""
    for value in upload_rules:
        try:
            BaseUploader(conn, cursor, BIOWARDROBE_UPLOAD_FUNCTIONS[value])\
                .execute(uid, os.path.join(output_folder, BIOWARDROBE_UPLOAD_TEMPLATES[value].format(uid)))
        except Exception as ex:
            raise BiowUploadException(uid, message="Failed to upload {} : {} : {}".format(value, uid, str(ex)))


def upload_macs2_fragment_stat(self, uid, filename):
    with open(filename, 'r') as input_file:
        data = input_file.read().strip().split()
        data.append(uid)
        self.cursor.execute("update labdata set fragmentsize=%s,fragmentsizeest=%s,islandcount=%s where uid=%s", tuple(data))
        self.conn.commit()


def upload_iaintersect_result(self, uid, filename):
    warnings.filterwarnings('ignore', category=MySQLdb.Warning)
    table_name = "`{}`.`{}_islands`".format(self.settings['experimentsdb'], uid)
    self.cursor.execute("select g.db from labdata l inner join genome g ON g.id=genome_id where uid=%s", (uid,))
    db_tuple = self.cursor.fetchone()
    if not db_tuple:
        raise BiowUploadException(uid, message="DB not found")
    gb_table_name = "`{}`.`{}_islands`".format(db_tuple['db'], str(uid).replace("-", "_"))

    self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    self.cursor.execute(f"DROP TABLE IF EXISTS {gb_table_name}")

    self.cursor.execute(f""" CREATE TABLE {table_name}
                          ( refseq_id VARCHAR(500) NULL,
                            gene_id VARCHAR(500) NULL,
                            txStart INT NULL,
                            txEnd INT NULL,
                            strand VARCHAR(1),
                            chrom VARCHAR(255) NOT NULL,
                            start INT(10) UNSIGNED NOT NULL,
                            end INT(10) UNSIGNED NOT NULL,
                            length INT(10) UNSIGNED NOT NULL,
                            abssummit INT(10),
                            pileup FLOAT,
                            log10p FLOAT,
                            foldenrich FLOAT,
                            log10q FLOAT,
                            region VARCHAR(50),
                            INDEX chrom_idx (chrom) USING BTREE,
                            INDEX start_idx (start) USING BTREE,
                            INDEX end_idx (end) USING BTREE,
                            INDEX region_idx (region ASC) USING BTREE,
                            INDEX txEnd_idx (txEnd ASC) USING BTREE,
                            INDEX txStart_idx (txStart ASC) USING BTREE,
                            INDEX gene_idx (gene_id(100) ASC) USING BTREE,
                            INDEX strand (strand ASC) USING BTREE,
                            INDEX refseq_idx (refseq_id(100) ASC) USING BTREE
                            ) ENGINE=MyISAM DEFAULT CHARSET=utf8 """)
    self.conn.commit()

    self.cursor.execute(f""" CREATE TABLE {gb_table_name}
                          ( bin int(7) unsigned NOT NULL,
                            chrom varchar(255) NOT NULL,
                            chromStart int(10) unsigned NOT NULL,
                            chromEnd int(10) unsigned NOT NULL,
                            name varchar(255) NOT NULL,
                            score int(5) not null,
                            INDEX bin_idx (bin) using btree,
                            INDEX chrom_idx (chrom) using btree,
                            INDEX chrom_start_idx (chromStart) using btree,
                            INDEX chrom_end_idx (chromEnd) using btree
                            ) ENGINE=MyISAM DEFAULT CHARSET=utf8 """)
    self.conn.commit()

    SQL = f"""INSERT INTO {table_name} 
                (refseq_id,gene_id,txStart,txEnd,strand,
                chrom,start,end,length,abssummit,pileup,
                log10p,foldenrich,log10q,region) 
              VALUES"""
    with open(filename, 'r') as input_file:
        for line in input_file.readlines():
            line = line.strip()
            if not line or "gene_id" in line or "pileup" in line:
                continue
            line_splitted = [None if item == "NULL" else item for item in line.split()]
            self.cursor.execute(SQL + " (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", tuple(line_splitted))
        self.conn.commit()

    self.cursor.execute(f"""insert into  {gb_table_name}
                        (bin, chrom, chromStart, chromEnd, name, score)
                         select 0 as bin, chrom, start as chromStart, end as chromEnd,
                         max(log10p) as name, max(log10q) as score
                         from {table_name} group by chrom,start,end; """)
    self.conn.commit()

    # self.cursor.execute("""update labdata set params='{"promoter":1000}' where uid=%s""", (uid,))
    # self.conn.commit()


def upload_get_stat(self, uid, filename):
    # for DNA: TOTAL, ALIGNED, SUPRESSED, USED       > TOTAL, ALIGNED, SUPRESSED, SUPRESSED, USED
    # for RNA: TOTAL, ALIGNED, RIBO, SUPRESSED, USED > TOTAL, ALIGNED, RIBO, SUPRESSED, USED
    with open(filename, 'r') as input_file:
        data = input_file.read().strip().split()
        if len(data) == 4:  # we got file from DNA experiment
            tagssuppressed = data[2]
            data.insert(2, tagssuppressed)
        data.append(uid)
        self.cursor.execute(
            "update labdata set tagstotal=%s,tagsmapped=%s,tagsribo=%s,tagssuppressed=%s,tagsused=%s where uid=%s",
            (data[0],     data[1],      data[2],    data[3],          data[4],          data[5]))
        self.conn.commit()


def upload_rpkm(self, uid, filename):
    warnings.filterwarnings('ignore', category=MySQLdb.Warning)
    table_basename = "`{}`.`{}".format(self.settings['experimentsdb'], uid)

    # each suffix includes also '`' to complement '.`' in table_basename
    suffixes = ['_isoforms`', '_genes`', '_common_tss`']
    # Drop all VIEW and TABLE for this experiment
    for suffix in suffixes:
        self.cursor.execute("DROP VIEW IF EXISTS " + table_basename + suffix)
        self.cursor.execute("DROP TABLE IF EXISTS " + table_basename + suffix)
        self.cursor.execute(""" CREATE TABLE """ + table_basename + suffix +
                            """ (refseq_id VARCHAR(100) NOT NULL,
                                 gene_id VARCHAR(100) NOT NULL,
                                 chrom VARCHAR(255) NOT NULL,
                                 txStart INT NULL,
                                 txEnd INT NULL,
                                 strand VARCHAR(1),
                                 TOT_R_0 FLOAT,
                                 RPKM_0 FLOAT
                                ) ENGINE=MyISAM DEFAULT CHARSET=utf8 """)

    self.conn.commit()

    # Insert values into _isoforms table
    SQL = f" INSERT INTO {table_basename}" + suffixes[0] + \
          " (refseq_id,gene_id,chrom,txStart,txEnd,strand,TOT_R_0,RPKM_0) VALUES"
    with open(filename, 'r') as input_file:
        for line in input_file.read().splitlines():
            # RefseqId, GeneId, Chrom, TxStart, TxEnd, Strand, TotalReads, Rpkm
            if not line or "RefseqId" in line or "GeneId" in line:
                continue
            self.cursor.execute(SQL + " (%s,%s,%s,%s,%s,%s,%s,%s)", tuple(line.split(',')))
        self.conn.commit()

    # Insert values into _genes table
    self.cursor.execute(""" INSERT INTO """ + table_basename + suffixes[1] + # _genes
                        """ SELECT
                                GROUP_CONCAT(DISTINCT refseq_id ORDER BY refseq_id SEPARATOR ',') AS refseq_id,
                                gene_id AS gene_id,
                                MAX(chrom) AS chrom,
                                MAX(txStart) AS txStart,
                                MAX(txEnd) AS txEnd,
                                MAX(strand) AS strand,
                                COALESCE(SUM(TOT_R_0),0) AS TOT_R_0,
                                COALESCE(SUM(RPKM_0),0) AS RPKM_0
                            FROM """ + table_basename + suffixes[0] +        # _isoforms
                        """ GROUP BY gene_id """)

    self.conn.commit()

    # Insert values into _common_tss table
    self.cursor.execute(""" INSERT INTO """ + table_basename + suffixes[2] +    # _common_tss
                        """ SELECT
                                GROUP_CONCAT(DISTINCT refseq_id ORDER BY refseq_id SEPARATOR ',') AS refseq_id,
                                GROUP_CONCAT(DISTINCT gene_id ORDER BY gene_id SEPARATOR ',') AS gene_id,
                                chrom AS chrom,
                                txStart AS txStart,
                                MAX(txEnd) AS txEnd,
                                strand AS strand,
                                COALESCE(SUM(TOT_R_0), 0) AS TOT_R_0,
                                COALESCE(SUM(RPKM_0), 0) AS RPKM_0
                            FROM """ + table_basename + suffixes[0] +
                        """ WHERE strand = '+'
                            GROUP BY chrom, txStart, strand
                            UNION
                            SELECT
                                GROUP_CONCAT(DISTINCT refseq_id ORDER BY refseq_id SEPARATOR ',') AS refseq_id,
                                GROUP_CONCAT(DISTINCT gene_id ORDER BY gene_id SEPARATOR ',') AS gene_id,
                                chrom AS chrom,
                                MIN(txStart) AS txStart,
                                txEnd AS txEnd,
                                strand AS strand,
                                COALESCE(SUM(TOT_R_0),0) AS TOT_R_0,
                                COALESCE(SUM(RPKM_0),0) AS RPKM_0
                            FROM """ + table_basename + suffixes[0] +
                        """ WHERE strand = '-'
                            GROUP BY chrom, txEnd, strand""")

    for suffix in suffixes:
        self.cursor.execute(f""" ALTER TABLE {table_basename}{suffix}
                                ADD INDEX `refseq_id_idx` USING BTREE (`refseq_id` ASC),
                                ADD INDEX `gene_id_idx` USING BTREE (`gene_id` ASC),
                                ADD INDEX `chr_idx` USING BTREE (`chrom` ASC),
                                ADD INDEX `txStart_idx` USING BTREE (`txStart` ASC),
                                ADD INDEX `txEnd_idx` USING BTREE (`txEnd` ASC);
                                """)
    self.conn.commit()


def upload_atdp(self, uid, filename):
    warnings.filterwarnings('ignore', category=MySQLdb.Warning)
    table_name = "`{}`.`{}_atdp`".format(self.settings['experimentsdb'], uid)

    self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    self.conn.commit()
    self.cursor.execute(f"""CREATE TABLE {table_name}
                           ( X INT NULL,
                             Y FLOAT NULL,
                             INDEX X_idx (X) USING BTREE
                            ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT = 'created by atdp' """)
    self.conn.commit()
    SQL = f"INSERT INTO {table_name} (X,Y) VALUES"
    with open(filename, 'r') as input_file:
        for line in input_file.readlines():
            line = line.strip()
            if not line or "X" in line or "Y" in line:
                continue
            self.cursor.execute(SQL + " (%s,%s)", tuple(line.split()))
        self.conn.commit()


def upload_bigwig(self, uid, filename, strand=None):
    self.cursor.execute("SELECT g.db FROM labdata l INNER JOIN genome g ON g.id=genome_id WHERE uid=%s", (uid,))
    db_tuple = self.cursor.fetchone()
    if not db_tuple:
        raise BiowUploadException(uid, message="DB not found")
    gb_bigwig_table_name = {
        '+': db_tuple['db'] + '.`' + str(uid).replace("-", "_") + '_upstream_f_wtrack`',
        '-': db_tuple['db'] + '.`' + str(uid).replace("-", "_") + '_downstream_f_wtrack`',
        None: db_tuple['db'] + '.`' + str(uid).replace("-", "_") + '_f_wtrack`'
    }[strand]
    self.cursor.execute(f" DROP TABLE IF EXISTS {gb_bigwig_table_name}")
    self.cursor.execute(f""" CREATE TABLE {gb_bigwig_table_name}
                         (fileName VARCHAR(255) not NULL) ENGINE=MyISAM DEFAULT CHARSET=utf8""")
    self.cursor.execute(f" INSERT INTO {gb_bigwig_table_name} VALUES (%s)", (filename,))
    self.conn.commit()


def upload_bigwig_upstream(self, uid, filename):
    upload_bigwig(self, uid, filename, strand='+')


def upload_bigwig_downstream(self, uid, filename):
    upload_bigwig(self, uid, filename, strand='-')


def upload_dateanalyzed(self, uid, filename):
    self.cursor.execute("update labdata set dateanalyzed=now() where uid=%s and dateanalyzed is null", (uid,))
    self.conn.commit()


def upload_folder_size(self, uid, filename):
    total_size = 0
    for root, dirs, files in os.walk(os.path.dirname(filename)):
        for f in files:
            fp = os.path.join(root, f)
            total_size += os.path.getsize(fp)
    self.cursor.execute("update labdata set size = %s where uid=%s", (int(total_size)/1024.0, uid))
    self.conn.commit()


def delete_files(self, uid, filename):
    for item_file in glob.glob(filename):
        os.remove(item_file)


BIOWARDROBE_UPLOAD_FUNCTIONS = {
    "upload_macs2_fragment_stat": upload_macs2_fragment_stat,
    "upload_iaintersect_result": upload_iaintersect_result,
    "upload_get_stat": upload_get_stat,
    "upload_atdp": upload_atdp,
    "upload_bigwig": upload_bigwig,
    "upload_bigwig_upstream": upload_bigwig_upstream,
    "upload_bigwig_downstream": upload_bigwig_downstream,
    "upload_rpkm": upload_rpkm,
    "upload_folder_size": upload_folder_size,
    "delete_files": delete_files
}

BIOWARDROBE_UPLOAD_TEMPLATES = {
    "upload_macs2_fragment_stat": '{}_fragment_stat.tsv',
    "upload_iaintersect_result": '{}_macs_peaks_iaintersect.tsv',
    "upload_get_stat": '{}.stat',
    "upload_atdp": '{}_atdp.tsv',
    "upload_bigwig": '{}.bigWig',
    "upload_bigwig_upstream": '{}_upstream.bigWig',
    "upload_bigwig_downstream": '{}_downstream.bigWig',
    "upload_rpkm": '{}.isoforms.csv',
    "upload_folder_size": 'upload_folder_size',
    "delete_files": '{}*.fastq'
}
