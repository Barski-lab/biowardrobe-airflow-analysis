import logging
import os
import shutil
from json import dumps, loads
from jsonmerge import merge
from contextlib import closing

from airflow.models import BaseOperator
from airflow.utils import apply_defaults
from airflow.hooks.mysql_hook import MySqlHook

from cwltool.process import relocateOutputs
from cwltool.stdfsaccess import StdFsAccess

from cwl_airflow_parser.cwlstepoperator import CWLStepOperator

from ..biowardrobe.analysis import get_biowardrobe_data
from ..biowardrobe.utils import update_status
from ..biowardrobe.constants import biowardrobe_connection_id, EXP_TYPE_UPLOAD
from ..biowardrobe.db_uploader import upload_results_to_db
from ..biowardrobe.biow_exceptions import BiowBasicException



_logger = logging.getLogger(__name__)


def set_permissions(item, dir_perm=0o0777, file_perm=0o0666, grp_own=os.getgid(), user_own=-1):
    os.chown(item, user_own, grp_own)
    if os.path.isfile(item):
        os.chmod(item, file_perm)
    else:
        os.chmod(item, dir_perm)
        for root, dirs, files in os.walk(item):
            for file in files:
                os.chmod(os.path.join(root, file), file_perm)
                os.chown(os.path.join(root, file), user_own, grp_own)
            for _dir in dirs:
                os.chmod(os.path.join(root, _dir), dir_perm)
                os.chown(os.path.join(root, _dir), user_own, grp_own)


class BioWardrobeJobDone(BaseOperator):

    ui_color = '#1E88E5'
    ui_fgcolor = '#FFF'

    @apply_defaults
    def __init__(
            self,
            task_id=None,
            reader_task_id=None,
            *args, **kwargs):
        task_id = task_id if task_id else self.__class__.__name__
        super(BioWardrobeJobDone, self).__init__(task_id=task_id, *args, **kwargs)

        self.outputs = self.dag.get_output_list()
        self.outdir = None
        self.output_folder = None
        self.reader_task_id = None
        self.reader_task_id = reader_task_id if reader_task_id else self.reader_task_id

    def execute(self, context):
        upstream_task_ids = [t.task_id for t in self.dag.tasks if isinstance(t, CWLStepOperator)] + \
                            ([self.reader_task_id] if self.reader_task_id else [])
        upstream_data = self.xcom_pull(context=context, task_ids=upstream_task_ids)

        _logger.debug('{0}: xcom_pull data: \n {1}'.
                      format(self.task_id, dumps(upstream_data, indent=4)))

        promises = {}
        for data in upstream_data:
            promises = merge(promises, data["promises"]) if "promises" in data else promises
            if "outdir" in data:
                self.outdir = data["outdir"]

        if "output_folder" in promises:
            self.output_folder = os.path.abspath(promises["output_folder"])
        else:
            return

        _logger.info('{0}: Final job: \n{1}\nMoving data: \n{2}'.
                     format(self.task_id,
                            dumps(promises, indent=4),
                            dumps(self.outputs, indent=4)))

        _files_moved = relocateOutputs(promises, self.output_folder, [self.outdir], "move", StdFsAccess(""))
        _job_result = {val.split("/")[-1]: _files_moved[out]  # TODO: is split required?
                       for out, val in self.outputs.items()
                       if out in _files_moved
                       }
        try:
            if self.outdir:
                shutil.rmtree(self.outdir, ignore_errors=False)
            _logger.info('{0}: Delete temporary output directory {1}'.format(self.task_id, self.outdir))
        except Exception as e:
            _logger.error("{0}: Temporary output directory hasn't been set {1}".format(self.task_id, e))
            pass
        _logger.info("Job done: {}".format(dumps(_job_result, indent=4)))

        mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
        with closing(mysql.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                _data = get_biowardrobe_data(cursor, promises['uid'])
                _params = loads(_data['params'])

                if 'promoter' not in _params:
                    _params['promoter'] = 1000
                _params.update(_job_result)
                params = dumps(_params)

                try:
                    upload_results_to_db(upload_set=EXP_TYPE_UPLOAD[_data['etype']],
                                         uid=promises['uid'],
                                         output_folder=self.output_folder,
                                         cursor=cursor,
                                         conn=conn
                                         )
                    update_status(uid=promises['uid'],
                                  message='complete',
                                  code=12,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column=f"dateanalyzee=now(),params='{params}'")
                except BiowBasicException as ex:
                    update_status(uid=promises['uid'],
                                  message=f'Fail:{ex}',
                                  code=2010,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="dateanalyzee=now()")

        return _job_result
