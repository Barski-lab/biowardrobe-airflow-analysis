import logging
import os
from tempfile import mkdtemp
from json import dumps
from contextlib import closing

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.hooks.mysql_hook import MySqlHook

from ..biowardrobe.analysis import get_biowardrobe_data
from ..biowardrobe.utils import update_status
from ..biowardrobe.constants import biowardrobe_connection_id


_logger = logging.getLogger(__name__)


class BioWardrobeJobReader(BaseOperator):

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
        super(BioWardrobeJobReader, self).__init__(task_id=task_id, *args, **kwargs)

        self.tmp_folder = tmp_folder if tmp_folder else self.dag.default_args['tmp_folder']
        if ui_color: self.ui_color = ui_color

    def execute(self, context):
        try:
            cwl_context = {
                "outdir": mkdtemp(
                    prefix=os.path.abspath(os.path.join(self.tmp_folder, 'dag_tmp_')))
            }
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

            cwl_context['promises'] = _json

            logging.info(
                '{0}: Final job: \n {1}'.format(self.task_id, dumps(cwl_context, indent=4)))

            return cwl_context

        except Exception as e:
            _logger.info(
                'Dispatch Exception {0}: \n {1} {2}'.format(self.task_id, type(e), e))
            pass

