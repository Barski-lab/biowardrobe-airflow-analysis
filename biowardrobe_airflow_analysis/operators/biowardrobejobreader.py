import logging
import os
import io
from tempfile import mkdtemp
from json import dumps
from contextlib import closing

import schema_salad.schema
from schema_salad.ref_resolver import Loader, file_uri
import ruamel.yaml as yaml
from urllib.parse import urlsplit

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.hooks.mysql_hook import MySqlHook

from ..biowardrobe.analysis import get_biowardrobe_data
from ..biowardrobe.utils import update_status
from ..biowardrobe.constants import biowardrobe_connection_id

from cwltool.main import jobloaderctx, shortname, init_job_order
from cwltool.pathmapper import adjustDirObjs, visit_class, trim_listing
from cwltool.process import normalizeFilesDirs

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

    # def add_defaults(self, job_order_object):
    #     for inp in self.dag.cwlwf.tool["inputs"]:
    #         if "default" in inp and (not job_order_object or shortname(inp["id"]) not in job_order_object):
    #             if not job_order_object:
    #                 job_order_object = {}
    #             job_order_object[shortname(inp["id"])] = inp["default"]

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

            _jobloaderctx = jobloaderctx.copy()
            _jobloaderctx.update(self.dag.cwlwf.metadata.get("$namespaces", {}))
            loader = Loader(_jobloaderctx)

            try:
                job_order_object = yaml.round_trip_load(io.StringIO(initial_value=dumps(_json)))
                job_order_object, _ = loader.resolve_all(job_order_object,
                                                         file_uri(os.getcwd()) + "/",
                                                         checklinks=False)
            except Exception as e:
                _logger.error("Job Loader: {}".format(str(e)))

            # self.add_defaults(job_order_object)

            job_order_object = init_job_order(job_order_object, None, self.dag.cwlwf)

            # if "cwl:tool" in job_order_object:
            #     del job_order_object["cwl:tool"]
            # if "id" in job_order_object:
            #     del job_order_object["id"]
            #
            # adjustDirObjs(job_order_object, trim_listing)
            # normalizeFilesDirs(job_order_object)

            logging.info('{0}: Job object after adjustment and normalization: \n{1}'.
                         format(self.task_id, dumps(job_order_object, indent=4)))

            # fragment = urlsplit(self.dag.default_args["workflow"]).fragment
            # fragment = fragment + '/' if fragment else ''
            # job_order_object_extended = {fragment + key: value for key, value in job_order_object.items()}

            cwl_context['promises'] = job_order_object

            logging.info(
                '{0}: Final job: \n {1}'.format(self.task_id, dumps(cwl_context, indent=4)))

            return cwl_context

        except Exception as e:
            _logger.info(
                'Dispatch Exception {0}: \n {1} {2}'.format(self.task_id, type(e), e))
            pass

