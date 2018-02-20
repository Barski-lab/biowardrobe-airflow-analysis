
import logging
from contextlib import closing
from datetime import timedelta, datetime
from time import sleep
import os
import uuid

import airflow
from airflow.models import DAG, BaseOperator, DagRun
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.dagrun_operator import DagRunOrder
from airflow import settings
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.sensors import SqlSensor
from airflow.operators.dummy_operator import DummyOperator
from airflow.hooks.mysql_hook import MySqlHook
from airflow.exceptions import AirflowSkipException
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.decorators import apply_defaults

from ..biowardrobe import biowardrobe_connection_id, get_biowardrobe_data

_logger = logging.getLogger(__name__)


class BioWardrobeTriggerDownloadOperator(BaseOperator):
    """
    Triggers a DAG run for a specified ``dag_id`` if a criteria is met

    :param trigger_dag_id: the dag_id to trigger
    :type trigger_dag_id: str
    :param python_callable: a reference to a python function that will be
        called while passing it the ``context`` object and a placeholder
        object ``obj`` for your callable to fill and return if you want
        a DagRun created. This ``obj`` object contains a ``run_id`` and
        ``payload`` attribute that you can modify in your function.
        The ``run_id`` should be a unique identifier for that DAG run, and
        the payload has to be a picklable object that will be made available
        to your tasks while executing that DAG run. Your function header
        should look like ``def foo(context, dag_run_obj):``
    :type python_callable: python callable
    """
    ui_color = '#ffefeb'

    @apply_defaults
    def __init__(
            self,
            trigger_dag_id,
            poke_interval=60 * 5,
            timeout=60 * 60 * 24 * 7,
            *args, **kwargs):
        super(BioWardrobeTriggerDownloadOperator, self).__init__(*args, **kwargs)
        self.trigger_dag_id = trigger_dag_id
        self.poke_interval = poke_interval
        self.timeout = timeout

    def execute(self, context):

        started_at = datetime.utcnow()

        _keep_going = True
        while _keep_going:

            mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
            with closing(mysql.get_conn()) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("""select id, uid from ems.labdata
                                      where libstatus = 0 and deleted=0 and url is not NULL and url <> "" """)
                    _download_data = cursor.fetchall()

            if not _download_data:
                if (datetime.utcnow() - started_at).total_seconds() > self.timeout:
                    raise AirflowSkipException('Snap. Time is OUT.')
                sleep(self.poke_interval)
                continue

            _keep_going = False
            with closing(mysql.get_conn()) as conn:
                with closing(conn.cursor()) as cursor:
                    session = settings.Session()
                    for row in _download_data:
                        _logger.info("Trigger download with: {}".format(row))
                        _run_id = 'trig__{}__{}'.format(row['uid'], uuid.uuid4())

                        dr = DagRun(
                            dag_id=self.trigger_dag_id,
                            run_id=_run_id,
                            conf={'biowardrobe_uid': row['uid'], 'run_id': _run_id},
                            execution_date=datetime.now(),
                            start_date=datetime.now(),
                            external_trigger=True)
                        logging.info("Creating DagRun {}".format(dr))
                        session.add(dr)
                        session.commit()

                        cursor.execute("update ems.labdata set libstatus=1, deleted=0 where uid=%s ", (row['uid'],))
                        conn.commit()

                    session.close()


class BioWardrobeTriggerBasicAnalysisOperator(BaseOperator):
    ui_color = '#ffefeb'

    @apply_defaults
    def __init__(
            self,
            *args, **kwargs):
        super(BioWardrobeTriggerBasicAnalysisOperator, self).__init__(*args, **kwargs)

    def execute(self, context):

        biowardrobe_uid = context['dag_run'].conf['biowardrobe_uid'] \
            if 'biowardrobe_uid' in context['dag_run'].conf else None

        if not biowardrobe_uid:
            raise Exception('biowardrobe_id must be provided')

        run_id = context['dag_run'].conf['run_id'] \
            if 'run_id' in context['dag_run'].conf else 'trig__{}__{}'.format(biowardrobe_uid, uuid.uuid4())

        _logger.info('Successfully finished: {}'.format(biowardrobe_uid))

        mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
        with closing(mysql.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("update ems.labdata set libstatus=10, libstatustxt='downloaded' where uid=%s",
                               (biowardrobe_uid,))
                conn.commit()
                data = get_biowardrobe_data(cursor=cursor,
                                            biowardrobe_uid=biowardrobe_uid)
                dag_id = os.path.basename(os.path.splitext(data['workflow'])[0])

                payload = {'biowardrobe_uid': biowardrobe_uid, 'run_id': run_id}

                _logger.info("Trigger basic analysis with: {}".format(payload))
                session = settings.Session()
                dr = DagRun(
                    dag_id=dag_id,
                    run_id=run_id,
                    conf=payload,
                    execution_date=datetime.now(),
                    external_trigger=True)
                logging.info("Creating DagRun {}".format(dr))
                session.add(dr)
                session.commit()
                session.close()
