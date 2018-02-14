# -*- coding: utf-8 -*-
#
# Download pipeline for BioWardrobe (any url/NCBI SRA/CCHMC core facility)
#

import logging
from contextlib import closing
from datetime import timedelta, datetime
import re
import uuid
import os

import airflow
from airflow.models import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.hooks.mysql_hook import MySqlHook
from airflow.utils.trigger_rule import TriggerRule
from airflow.models import Variable
from airflow.exceptions import AirflowException, AirflowSensorTimeout, AirflowSkipException

from .analysis import get_biowardrobe_data
from .constants import biowardrobe_connection_id
from ..operators.biowardrobetriggers import BioWardrobeTriggerDownloadOperator, BioWardrobeTriggerBasicAnalysisOperator


_logger = logging.getLogger(__name__)


# Create some placeholder operators
# class DummySkipOperator(DummyOperator):
#     ui_color = '#e8b7e4'
#
#     def execute(self, context):
#         raise AirflowSkipException


PROXY = Variable.get("PROXY", default_var="")
EXTRA_LOCAL_SCRIPT = Variable.get("EXTRA_LOCAL_SCRIPT", default_var="")


#
#  On Retry Callback
#
def on_retry(context):
    biowardrobe_uid = context['dag_run'].conf['biowardrobe_uid'] \
        if 'biowardrobe_uid' in context['dag_run'].conf else None

    if not biowardrobe_uid:
        raise Exception('biowardrobe_id must be provided')

    mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
    with closing(mysql.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                "update labdata set libstatus=1000, libstatustxt='Download Failed. Retry!' where uid='{}'".format(
                    biowardrobe_uid))
            conn.commit()


_extra_local_file_ = EXTRA_LOCAL_SCRIPT if EXTRA_LOCAL_SCRIPT else \
    os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/extra_local_download.sh")
_extra_local_file_content = ""
if os.path.isfile(_extra_local_file_):
    with open(_extra_local_file_, 'r') as content_file:
        _extra_local_file_content = content_file.read()

download_base = """
UUID="{{ ti.xcom_pull(task_ids='branch_download', key='uid') }}"
URL="{{ ti.xcom_pull(task_ids='branch_download', key='url') }}"

UDIR="{{ ti.xcom_pull(task_ids='branch_download', key='upload') }}"
DIR="{{ ti.xcom_pull(task_ids='branch_download', key='output_folder') }}"

user_agent="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

TMPFILE='aria2downloadfile'   #`mktemp -u XXXXXXXX` || exit 1

mkdir -p "${DIR}"
chmod 0777 "${DIR}"
cd "${DIR}" || exit 1

"""+f"""

PROXY="{PROXY}"

"""

args = {
    'owner': 'airflow',
    'start_date': datetime.now(),
    'depends_on_past': False,
    'email': ['biowardrobe@biowardrobe.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1000,
    'retry_exponential_backoff': True,
    'retry_delay': timedelta(minutes=10),
    'max_retry_delay': timedelta(minutes=60*24)
}

#
#    BIOWARDROBE DOWNLOAD WORKFLOW (be triggered)
#

DAG_NAME = 'biowardrobe_download'

dag = DAG(
    dag_id=DAG_NAME,
    default_args=args,
    schedule_interval=None,
    max_active_runs=5,
    default_view='tree'
)


#
#  A STEP
#
def branch_download_func(**context):
    biowardrobe_uid = context['dag_run'].conf['biowardrobe_uid'] \
        if 'biowardrobe_uid' in context['dag_run'].conf else None

    if not biowardrobe_uid:
        raise Exception('biowardrobe_id must be provided')

    data = {}
    mysql = MySqlHook(mysql_conn_id=biowardrobe_connection_id)
    with closing(mysql.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            data = get_biowardrobe_data(cursor=cursor,
                                        biowardrobe_uid=biowardrobe_uid)
    _logger.info("Data: ", data)

    context['ti'].xcom_push(key='url', value=data['url'])
    context['ti'].xcom_push(key='uid', value=data['uid'])
    context['ti'].xcom_push(key='upload', value=data['upload'])
    context['ti'].xcom_push(key='output_folder', value=data['output_folder'])

    if re.match("^https?://|^s?ftp://|^-", data['url']):
        return "download_aria2"

    if re.match("^(GSM|SR[ARX])[0-9]+$", data['url']):
        return "download_sra"

    return "download_local"


branch_download = BranchPythonOperator(
    task_id='branch_download',
    provide_context=True,
    python_callable=branch_download_func,
    dag=dag)

#
#  A STEP
#
download_aria2 = download_base + """

aria2c -q -d "./" --user-agent="${user_agent}" --all-proxy="${PROXY}"\
--always-resume --allow-overwrite --max-resume-failure-tries=40 \
-o "${TMPFILE}" "${URL}"

ARIA=$?
if [ ${ARIA} -ne 0 ]; then
    rm -f "${TMPFILE}"
    rm -f "${TMPFILE}".aria2
    echo "Error: aria2 can't download file"
    exit ${ARIA}
fi

T=`file -b "${DIR}/${TMPFILE}" |awk '{print $1}'`
echo ${T}

case "${T}" in
  "bzip2"|"gzip"|"Zip")
    7z e -so "${TMPFILE}" >"./${UUID}.fastq"
    rm -f "${TMPFILE}"
    ;;
  "ASCII")
    mv "${TMPFILE}" "./${UUID}.fastq"
    ;;
  *)
    rm -f "${TMPFILE}"
    echo "Error: file type unknown"
    exit 1
esac

N1=`awk '(NR+3) % 4 == 0 && $1 ~ /^@/' ${UUID}.fastq |wc -l`
N2=`awk '(NR+1) % 4 == 0 && $1 ~ /^\+/' ${UUID}.fastq |wc -l`
echo "is it fastq? $N1 == $N2"
if [ $N1 = $N2 ]; then
  echo "Ok: fastq"
else
  echo "Error: not a fastq"
  exit 1
fi
"""

url_download = BashOperator(
    task_id='download_aria2',
    xcom_push=True,
    bash_command=download_aria2,
    on_retry_callback=on_retry,
    dag=dag)
url_download.set_upstream(branch_download)


#
#  A STEP
#
download_sra = download_base + """
fastq-dump --split-files "${URL}"

if [ -f ${URL}_1.fastq ]; then
 mv "${URL}_1.fastq" "${UUID}".fastq
fi

if [ -f "${URL}_2.fastq" ]; then
 mv "${URL}_2.fastq" "${UUID}"_2.fastq
fi

echo "Ok: fastq"
"""

cli_download_sra = BashOperator(
    task_id='download_sra',
    xcom_push=True,
    bash_command=download_sra,
    on_retry_callback=on_retry,
    dag=dag)
cli_download_sra.set_upstream(branch_download)


#
#  A STEP
#
download_local = download_base + """
#
#check local dir !!!
#

FTEST=`find ${UDIR}  -type f -name "*${URL}*" -print|wc -l`
if [ ${FTEST} -lt 1 ]; then
  echo "Skip local: File not found ${FTEST}"
  exit 1
else
  if [ ${FTEST} -gt 2 ]; then
    echo "Error: Bad filter"
    exit 1
  else
    lines=1
    for i in $(find ${UDIR}  -type f -name "*${URL}*" -print); do
        mv "${i}" "./${UUID}_${lines}"

        T=`file -b "./${UUID}_${lines}" | awk '{print $1}'`
        echo ${T}

        case "${T}" in
          "bzip2"|"gzip"|"Zip")
            7z e -so "./${UUID}_${lines}" >"./${UUID}_${lines}.fastq"
            rm -f "./${UUID}_${lines}"
            ;;
          "ASCII")
            mv "./${UUID}_${lines}" "./${UUID}_${lines}.fastq"
            ;;
          *)
            echo "Error: file type unknown"
            exit 1
        esac

      lines=$((lines+1))
    done
    mv "./${UUID}_1.fastq" "./${UUID}.fastq"
  fi
fi

"""+_extra_local_file_content

download_local_operator = BashOperator(
    task_id='download_local',
    xcom_push=True,
    bash_command=download_local,
    on_retry_callback=on_retry,
    dag=dag)
download_local_operator.set_upstream(branch_download)

#
#  A STEP
#
# skip = DummySkipOperator(task_id='skip', dag=dag)
# skip.set_upstream(branch_download)


#
#  A STEP
#
success_finish_operator = \
    BioWardrobeTriggerBasicAnalysisOperator(task_id='success_finish',
                                            trigger_rule=TriggerRule.ONE_SUCCESS,
                                            dag=dag)
success_finish_operator.set_upstream([cli_download_sra, url_download, download_local_operator])


#
#  A STEP
#
error_finish_operator = MySqlOperator(
    task_id="finish_with_error",
    mysql_conn_id=biowardrobe_connection_id,
    sql="""update labdata set libstatus=2000,
        libstatustxt="{{ ti.xcom_pull(task_ids=['download_sra','download_local', 'download_aria2'], key=None) }}"
        where uid='{{ ti.xcom_pull(task_ids='branch_download', key='uid') }}'""",
    trigger_rule=TriggerRule.ONE_FAILED,
    autocommit=True,
    dag=dag)
error_finish_operator.set_upstream([cli_download_sra, url_download, download_local_operator])


#
#      BIOWARDROBE DOWNLOAD TRIGGER
#


dag_t = DAG(
    dag_id='biowardrobe_download_trigger',
    default_args={
        "owner": "airflow",
        "start_date": airflow.utils.dates.days_ago(1),
        'depends_on_past': False,
        'email': ['biowardrobe@biowardrobe.com'],
        'email_on_failure': False,
        'email_on_retry': False
    },
    schedule_interval='*/5 * * * *',
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=60*24)
)


trigger = BioWardrobeTriggerDownloadOperator(task_id='trigger',
                                             trigger_dag_id=DAG_NAME,
                                             dag=dag_t)
