# -*- coding: utf-8 -*-
#
# Download pipeline for BioWardrobe (any url/NCBI SRA/CCHMC core facility)
#

import os
import uuid
import logging
from contextlib import closing
from datetime import timedelta, datetime
from time import sleep
from shutil import rmtree
from subprocess import check_output

from airflow.models import DAG, Variable, BaseOperator, DagRun
from airflow.hooks.mysql_hook import MySqlHook
from airflow import settings
from airflow.utils.decorators import apply_defaults
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowSkipException

from .analysis import get_biowardrobe_data
from .constants import biowardrobe_connection_id

from warnings import filterwarnings
from MySQLdb import Warning

filterwarnings('ignore', category=Warning)


_logger = logging.getLogger(__name__)


class BioWardrobeForceRun(BaseOperator):
    ui_color = '#ffefeb'

    @apply_defaults
    def __init__(
            self,
            poke_interval=60*5,
            timeout=60*60*24*7,
            *args, **kwargs):
        super(BioWardrobeForceRun, self).__init__(*args, **kwargs)
        self.poke_interval = poke_interval
        self.timeout = timeout

    def drop_sql(self, cursor, data):
        biowardrobe_uid = data['uid']
        cursor.execute("SELECT DISTINCT db FROM genome")
        for DB in cursor.fetchall():
            for _t in ['_wtrack', '_islands', '_f_wtrack',
                       '_upstream_f_wtrack', '_downstream_f_wtrack']:
                cursor.execute("DROP TABLE IF EXISTS `{}`.`{}{}`".
                               format(DB['db'], str(biowardrobe_uid).replace("-", "_"), _t))
            cursor.execute("DROP VIEW IF EXISTS `{}`.`{}_islands`".
                           format(DB['db'], str(biowardrobe_uid).replace("-", "_")))

        for _t in ['_islands', '_atdp', '_atdph', '_isoforms', '_genes', '_common_tss']:
            cursor.execute("DROP TABLE IF EXISTS `{}`.`{}{}`".
                           format(data['experimentsdb'], biowardrobe_uid, _t))

        cursor.execute("DROP view IF EXISTS `{}`.`{}_genes`".
                       format(data['experimentsdb'], biowardrobe_uid))
        cursor.execute("DROP view IF EXISTS `{}`.`{}_common_tss`".
                       format(data['experimentsdb'], biowardrobe_uid))

    def get_force_run_data(self):
        mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
        with closing(mysql.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("""select uid from labdata
                                  where ((forcerun=1 AND libstatus >11 AND deleted=0) OR deleted=1) """)
                return cursor.fetchall()

    def get_record_data(self, biowardrobe_uid):
        mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
        with closing(mysql.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                return get_biowardrobe_data(cursor=cursor, biowardrobe_uid=biowardrobe_uid)

    def execute(self, context):

        started_at = datetime.utcnow()
        _keep_going = True
        while _keep_going:

            _force_run_data = self.get_force_run_data()
            _logger.info("Force run data: {}".format(_force_run_data))

            if not _force_run_data:
                if (datetime.utcnow() - started_at).total_seconds() > self.timeout:
                    raise AirflowSkipException('Snap. Time is OUT.')
                sleep(self.poke_interval)
                continue

            for row in _force_run_data:
                _keep_going = False
                biowardrobe_uid = row['uid']
                #  TODO: Check if dag is running in airflow

                #  TODO: If not running!
                data = self.get_record_data(biowardrobe_uid)
                if not data:
                    _logger.error('No biowardrobe data {}'.format(biowardrobe_uid))
                    continue
                #
                #  Actual Force RUN
                basedir = data['output_folder']
                try:
                    os.chdir(basedir)

                    for root, dirs, files in os.walk(".", topdown=False):
                        for name in files:
                            if "fastq" in name:
                                continue
                            os.remove(os.path.join(root, name))
                    rmtree(os.path.join(basedir, 'tophat'), True)
                except:
                    pass

                if int(data['deleted']) == 0:
                    # cmd = 'bunzip2 {}*.fastq.bz2'.format(biowardrobe_uid)
                    # try:
                    #     check_output(cmd, shell=True)
                    # except Exception as e:
                    #     _logger.error("Can't uncompress: {} {}".format(cmd, str(e)))

                    if not os.path.isfile(biowardrobe_uid + '.fastq.bz2'):
                        _logger.error("File does not exist: {}".format(biowardrobe_uid))
                        continue
                    if not os.path.isfile(biowardrobe_uid + '_2.fastq.bz2') and data['pair']:
                        _logger.error("File 2 does not exist: {}".format(biowardrobe_uid))
                        continue
                else:
                    rmtree(basedir, True)

                mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
                with closing(mysql.get_conn()) as conn:
                    with closing(conn.cursor()) as cursor:
                        self.drop_sql(cursor, data)
                        if int(data['deleted']) == 0:
                            cursor.execute(
                                "update labdata set libstatustxt=%s, libstatus=10, forcerun=0, tagstotal=0,"
                                "tagsmapped=0,tagsribo=0,tagsused=0,tagssuppressed=0 where uid=%s",
                                ("Ready to be reanalyzed", biowardrobe_uid))
                            conn.commit()
                        else:
                            cursor.execute(
                                "update labdata set libstatustxt=%s, deleted=2, datedel=CURDATE() where uid=%s",
                                ("Deleted", biowardrobe_uid))
                            conn.commit()
                            _logger.info("Deleted: {}".format(biowardrobe_uid))
                            continue

                _dag_id = os.path.basename(os.path.splitext(data['workflow'])[0])
                _run_id = 'forcerun__{}__{}'.format(biowardrobe_uid, uuid.uuid4())
                session = settings.Session()
                dr = DagRun(
                    dag_id=_dag_id,
                    run_id=_run_id,
                    conf={'biowardrobe_uid': biowardrobe_uid, 'run_id': _run_id},
                    execution_date=datetime.now(),
                    start_date=datetime.now(),
                    external_trigger=True)
                logging.info("Creating DagRun {}".format(dr))
                session.add(dr)
                session.commit()
                session.close()


#
#      BIOWARDROBE FORCE RUN DAG
#


dag = DAG(
    dag_id='biowardrobe-force-run',
    default_args={
        "owner": "airflow",
        "start_date": days_ago(1),
        'depends_on_past': False,
        'email': ['biowardrobe@biowardrobe.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 20,
        'retry_exponential_backoff': True,
        'retry_delay': timedelta(minutes=10),
        'max_retry_delay': timedelta(minutes=60*4)
    },
    schedule_interval='*/10 * * * *',
    catchup=True,
    max_active_runs=1
)
# dagrun_timeout = timedelta(minutes=60 * 24 * 8)

bio_force_run = BioWardrobeForceRun(task_id='BioWardrobeForceRun',
                                    dag=dag)
