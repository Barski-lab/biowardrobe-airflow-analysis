# -*- coding: utf-8 -*-
#
# Download pipeline for BioWardrobe (any url/NCBI SRA/CCHMC core facility)
#

import logging
from contextlib import closing
from datetime import timedelta, datetime
import re
import uuid

import airflow
from airflow.models import DAG, BaseOperator, DagRun
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.hooks.mysql_hook import MySqlHook
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.dagrun_operator import DagRunOrder, TriggerDagRunOperator
from airflow import settings
from airflow.operators.sensors import SqlSensor
from airflow.operators.dummy_operator import DummyOperator
from airflow.exceptions import AirflowSkipException
from airflow.utils.decorators import apply_defaults

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
#    BIOWARDROBE DOWNLOAD PIPELINE (be triggered)
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


download_base = """
UUID="{{ ti.xcom_pull(task_ids='branch_download', key='uid') }}"
URL="{{ ti.xcom_pull(task_ids='branch_download', key='url') }}"

UDIR="{{ ti.xcom_pull(task_ids='branch_download', key='upload') }}"
DIR="{{ ti.xcom_pull(task_ids='branch_download', key='output_folder') }}"
PROXY=""

user_agent="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

TMPFILE='aria2downloadfile'   #`mktemp -u XXXXXXXX` || exit 1

mkdir -p "${DIR}"
chmod 0777 "${DIR}"
cd "${DIR}" || exit 1

"""

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
    dag=dag)
cli_download_sra.set_upstream(branch_download)


#
#  A STEP
#
download_local = download_base + """
#
#check local dir bifore core !!!
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


#
# Core
#

main_page="https://dna.cchmc.org/www/main.php"
login_page="https://dna.cchmc.org/www/logon2.php"
request_page="https://dna.cchmc.org/www/results/nextgen_results.php"
download_url="https://dna.cchmc.org/www/results/nextgen_download.php?file="

cookie_file=`mktemp ./dna.XXXXXX`
file_list=`mktemp ./dna.XXXXXX`

user_name=""
user_pass=""

curl -s -i --insecure -b ${cookie_file} -c ${cookie_file} -A ${user_agent} -X POST --form "username=${user_name}" \
--form "password=${user_pass}" $login_page >/dev/null 2>&1
curl -s -i --insecure -b ${cookie_file} $request_page -A ${user_agent}|grep 'href="javascript:downloadFile'| \
awk -F"'" '{print $2}'|grep "${URL}" >${file_list} 2>&1

#    foo=$1
#    path=${foo%/*}
#    FN=${foo##*/}
#    base=${FN%%.*}
#    ext=${FN#*.}

lines=1
while read download_file; do

 aria2c -q -d ./ --user-agent="${user_agent}" --always-resume --allow-overwrite --max-resume-failure-tries=20 \
 --load-cookies=${cookie_file} \
 "${download_url}${download_file}&name=download_${lines}.fastq.gz"

 ARIA=$?
 if [ ${ARIA} -ne 0 ]; then
    rm -f "download_1.fastq.gz"
    rm -f "download_1.fastq.gz.aria2"
    rm -f "download_2.fastq.gz"
    rm -f "download_2.fastq.gz.aria2"
    exit ${ARIA}
 fi

 lines=$((lines+1))
 [ $lines -gt 2 ] && echo "Error: core 2 files max" && break

done < <(cat ${file_list})

if [ -f "download_1.fastq.gz" ]; then
 7z e -so "download_1.fastq.gz" >"./${UUID}.fastq"
 rm -f "download_1.fastq.gz"
fi

if [ -f "download_2.fastq.gz" ]; then
 7z e -so "download_2.fastq.gz" >"./${UUID}_2.fastq"
 rm -f "download_2.fastq.gz"
fi

rm -f ${cookie_file}
rm -f ${file_list}
"""

download_local_operator = BashOperator(
    task_id='download_local',
    xcom_push=True,
    bash_command=download_local,
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
    sql="""update ems.labdata set libstatus=0,
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
