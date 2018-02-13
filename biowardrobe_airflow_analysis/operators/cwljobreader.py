import logging
import os
from tempfile import mkdtemp
import json

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

# from airflow.hooks.mysql_hook import MySqlHook

_logger = logging.getLogger(__name__)


class CWLJobReader(BaseOperator):

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
        super(CWLJobReader, self).__init__(task_id=task_id, *args, **kwargs)

        self.tmp_folder = tmp_folder if tmp_folder else self.dag.default_args['tmp_folder']
        if ui_color: self.ui_color = ui_color

    def execute(self, context):
        try:
            cwl_context = {
                "outdir": mkdtemp(
                    prefix=os.path.abspath(os.path.join(self.tmp_folder, 'dag_tmp_')))
            }
            _json = {}

            if 'job' in context['dag_run'].conf:
                logging.debug(
                    '{0}: dag_run conf: \n {1}'.format(self.task_id, context['dag_run'].conf['job']))
                _json = context['dag_run'].conf['job']

            cwl_context['promises'] = _json

            logging.info(
                '{0}: Final job: \n {1}'.format(self.task_id, json.dumps(cwl_context, indent=4)))

            return cwl_context

        except Exception as e:
            _logger.info(
                'Dispatch Exception {0}: \n {1} {2}'.format(self.task_id, type(e), e))
            pass

