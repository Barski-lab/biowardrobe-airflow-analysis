import logging
import os
import io
from tempfile import mkdtemp
from json import dumps
from contextlib import closing

from airflow.utils.decorators import apply_defaults
from airflow.hooks.mysql_hook import MySqlHook

from ..biowardrobe import get_biowardrobe_data, biowardrobe_connection_id, update_status

from cwl_airflow_parser import CWLJobDispatcher

_logger = logging.getLogger(__name__)


class BioWardrobeJobDispatcher(CWLJobDispatcher):

    ui_color = '#1E88E5'
    ui_fgcolor = '#FFF'

    @apply_defaults
    def __init__(
            self,
            task_id=None,
            ui_color=None,
            tmp_folder=None,
            *args, **kwargs):
        task_id = task_id if task_id else self.__class__.__name__
        super(BioWardrobeJobDispatcher, self).__init__(task_id=task_id, *args, **kwargs)

        self.tmp_folder = tmp_folder if tmp_folder else self.dag.default_args['tmp_folder']
        if ui_color: self.ui_color = ui_color

    def execute(self, context):
        try:
            _json = {}
            _data = {}

            if 'job' in context['dag_run'].conf:
                logging.debug(
                    '{0}: dag_run conf: \n {1}'.format(self.task_id, context['dag_run'].conf['job']))
                _json = context['dag_run'].conf['job']

            mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
            with closing(mysql.get_conn()) as conn:
                with closing(conn.cursor()) as cursor:
                    if 'biowardrobe_uid' in context['dag_run'].conf:
                        _data = get_biowardrobe_data(cursor, context['dag_run'].conf['biowardrobe_uid'])
                        _json = _data['job']

                    update_status(uid=_json['uid'],
                                  message='Analysing',
                                  code=11,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="forcerun=0, dateanalyzes=now()")

                    update_status(uid=_json['uid'],
                                  message='Analysing',
                                  code=11,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="dateanalyzed=now()",
                                  optional_where="and dateanalyzed is null")

            return self.cwl_dispatch(_json)

            # fragment = urlsplit(self.dag.default_args["workflow"]).fragment
            # fragment = fragment + '/' if fragment else ''
            # job_order_object_extended = {fragment + key: value for key, value in job_order_object.items()}

        except Exception as e:
            _logger.info(
                'Dispatch Exception {0}: \n {1} {2}'.format(self.task_id, type(e), e))
            pass

