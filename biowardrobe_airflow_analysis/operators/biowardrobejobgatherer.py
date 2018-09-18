import logging
import os
from json import dumps, loads
from contextlib import closing

from airflow.utils import apply_defaults
from airflow.hooks.mysql_hook import MySqlHook
from airflow.models import BaseOperator


from cwl_airflow_parser import CWLJobGatherer

from ..biowardrobe import get_biowardrobe_data, biowardrobe_connection_id, update_status, upload_results_to_db2
from ..biowardrobe.biow_exceptions import BiowBasicException, BiowFileNotFoundException


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


class BioWardrobeJobGatherer(CWLJobGatherer):

    ui_color = '#1E88E5'
    ui_fgcolor = '#FFF'

    @apply_defaults
    def __init__(
            self,
            task_id=None,
            reader_task_id=None,
            *args, **kwargs):
        task_id = task_id if task_id else self.__class__.__name__
        super(BioWardrobeJobGatherer, self).__init__(task_id=task_id, *args, **kwargs)

        self.outputs = self.dag.get_output_list()
        self.outdir = None
        self.output_folder = None
        self.reader_task_id = None
        self.reader_task_id = reader_task_id if reader_task_id else self.reader_task_id

    def execute(self, context):

        _job_result, promises = self.cwl_gather(context)

        mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
        with closing(mysql.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                _data = get_biowardrobe_data(cursor, promises['uid'])
                _params = loads(_data['params'])

                _promoter = _params['promoter'] if 'promoter' in _params else 1000
                _params = _job_result
                _params['promoter'] = _promoter

                try:
                    upload_results_to_db2(upload_rules=loads(_data['upload_rules']),
                                          uid=promises['uid'],
                                          output_folder=self.output_folder,
                                          cursor=cursor,
                                          conn=conn
                                          )
                    update_status(uid=promises['uid'],
                                  message='Complete:upgraded',
                                  code=12,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="dateanalyzee=now(),params='{}'".format(dumps(_params)))
                except BiowBasicException as ex:
                    update_status(uid=promises['uid'],
                                  message=f'Fail:{ex}',
                                  code=2010,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="dateanalyzee=now(),params='{}'".format(dumps(_params)))

        return _job_result


class BioWardrobeJobFinalizing(BaseOperator):

    ui_color = '#1E88E5'
    ui_fgcolor = '#FFF'

    @apply_defaults
    def __init__(
            self,
            task_id=None,
            reader_task_id=None,
            *args, **kwargs):
        task_id = task_id if task_id else self.__class__.__name__
        super(BioWardrobeJobFinalizing, self).__init__(task_id=task_id, *args, **kwargs)

        self.outputs = self.dag.get_output_list()
        self.outdir = None
        self.output_folder = None
        self.reader_task_id = None
        self.reader_task_id = reader_task_id if reader_task_id else self.reader_task_id

    def execute(self, context):
        upstream_task_ids = [t.task_id for t in self.dag.tasks if isinstance(t, CWLJobGatherer)] + \
                            ([self.reader_task_id] if self.reader_task_id else [])
        _job_result, promises = self.xcom_pull(context=context, task_ids=upstream_task_ids)[0]

        if "output_folder" in promises:
            self.output_folder = os.path.abspath(promises["output_folder"])
        else:
            raise BiowFileNotFoundException(promises['uid'],404, "Can't find data directory")

        _logger.debug('{0}: xcom_pull data _job_result: \n {1}'.
                      format(self.task_id, dumps(_job_result, indent=4)))

        _logger.debug('{0}: xcom_pull data promises: \n {1}'.
                      format(self.task_id, dumps(promises, indent=4)))

        mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
        with closing(mysql.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                _data = get_biowardrobe_data(cursor, promises['uid'])
                _params = loads(_data['params'])

                _promoter = _params['promoter'] if 'promoter' in _params else 1000
                _params = _job_result
                _params['promoter'] = _promoter

                try:
                    upload_results_to_db2(upload_rules=loads(_data['upload_rules']),
                                          uid=promises['uid'],
                                          output_folder=self.output_folder,
                                          cursor=cursor,
                                          conn=conn
                                          )
                    update_status(uid=promises['uid'],
                                  message='Complete:upgraded',
                                  code=12,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="dateanalyzee=now(),params='{}'".format(dumps(_params)))
                except BiowBasicException as ex:
                    update_status(uid=promises['uid'],
                                  message=f'Fail:{ex}',
                                  code=2010,
                                  conn=conn,
                                  cursor=cursor,
                                  optional_column="dateanalyzee=now(),params='{}'".format(dumps(_params)))

        return _job_result

