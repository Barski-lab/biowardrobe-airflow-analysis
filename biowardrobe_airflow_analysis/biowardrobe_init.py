#! /usr/bin/env python3
"""
****************************************************************************

 Copyright (C) 2018 Datirium. LLC.
 All rights reserved.
 Contact: Datirium, LLC (datirium@datirium.com)

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 ****************************************************************************"""


import os
from sys import platform
from shutil import copyfile
from sqlparse import split

from airflow.utils.db import merge_conn
from airflow import models
from airflow.settings import DAGS_FOLDER, AIRFLOW_HOME
from airflow.bin.cli import api_client
from airflow import configuration as conf

from warnings import filterwarnings
from MySQLdb import Warning
filterwarnings('ignore', category=Warning)

from .biowardrobe import Settings

sql_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql_patch"))
system_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "system"))

_settings = Settings.Settings()


def apply_sql_patch(file):
    file_abs_path = os.path.join(sql_folder, "biowardrobe_tables", file)
    print(file_abs_path)
    with open(file_abs_path) as ef:
        for _sql in split(ef.read()):
            if not _sql:
                continue
            try:
                _settings.cursor.execute(_sql)
                _settings.conn.commit()
            except Exception as e:
                print("Error: {}".format(e))
                pass


def generate_biowardrobe_workflow():

    _settings.cursor.execute("select * from experimenttype limit 1")

    field_names = [i[0] for i in _settings.cursor.description]
    if 'workflow' not in field_names:
        apply_sql_patch("labdata_alter.sql")
        apply_sql_patch("experimenttype_alter.sql")

    apply_sql_patch("experimenttype_patch.sql")

    _template = u"""#!/usr/bin/env python3
from airflow import DAG
from biowardrobe_airflow_analysis import biowardrobe_workflow
dag = biowardrobe_workflow("{}")
"""
    _settings.cursor.execute("select workflow from experimenttype")
    for (workflow,) in _settings.cursor.fetchall():
        if not workflow:
            continue

        _filename = os.path.abspath(os.path.join(
            DAGS_FOLDER,
            os.path.basename(os.path.splitext(workflow)[0]) + '.py')
        )
        with open(_filename, 'w') as generated_workflow_stream:
            generated_workflow_stream.write(_template.format(workflow))

    _template = u"""#!/usr/bin/env python3
from airflow import DAG
from biowardrobe_airflow_analysis import BioWardrobeDownloadDAG, BioWardrobeDownloadTriggerDAG
d = BioWardrobeDownloadDAG
dt= BioWardrobeDownloadTriggerDAG
"""
    with open(os.path.join(DAGS_FOLDER, 'biowardrobe_download.py'), 'w') as generated_workflow_stream:
        generated_workflow_stream.write(_template)

    _template = u"""#!/usr/bin/env python3
from airflow import DAG
from biowardrobe_airflow_analysis import BioWardrobeForceRunDAG
d = BioWardrobeForceRunDAG
"""
    with open(os.path.join(DAGS_FOLDER, 'biowardrobe_force_run.py'), 'w') as generated_workflow_stream:
        generated_workflow_stream.write(_template)

    merge_conn(
        models.Connection(
            conn_id='biowardrobe', conn_type='mysql',
            host=_settings.config[0], login=_settings.config[1],
            password=_settings.config[2], schema=_settings.config[3],
            extra="{\"cursor\":\"dictcursor\"}"))

    pools = [api_client.create_pool(name='biowardrobe_download',
                                    slots=5,
                                    description="pool to download files")]
    pools = [api_client.create_pool(name='biowardrobe_basic_analysis',
                                    slots=1,
                                    description="pool to run basic analysis")]

    if not conf.has_option('cwl', 'tmp_folder'):
        if not os.path.exists(conf.AIRFLOW_CONFIG+'.orig'):
            copyfile(conf.AIRFLOW_CONFIG, conf.AIRFLOW_CONFIG+'.orig')
        with open(conf.AIRFLOW_CONFIG, 'w') as fp:
            for s in ['mesos', 'kerberos', 'celery', 'smtp', 'email', 'dask', 'ldap']:
                conf.conf.remove_section(s)

            conf.conf.add_section('cwl')
            conf.set('cwl', 'tmp_folder', os.path.join(AIRFLOW_HOME, 'tmp'))

            conf.set('core', 'logging_level', 'WARNING')
            conf.set('webserver', 'dag_default_view', 'graph')
            conf.set('webserver', 'dag_orientation', 'TB')
            conf.set('webserver', 'web_server_worker_timeout', '120')
            conf.set('scheduler', 'job_heartbeat_sec', '20')
            conf.set('scheduler', 'scheduler_heartbeat_sec', '20')
            conf.set('scheduler', 'min_file_process_interval', '30')
            conf.conf.write(fp)

    startup_scripts = ['com.datirium.airflow-scheduler.plist', 'com.datirium.airflow-webserver.plist']
    if platform == "darwin":
        _sys_dir = os.path.expanduser('~/Library/LaunchAgents')
        for scripts in startup_scripts:
            with open(os.path.join(system_folder, 'macosx', scripts), 'r') as s:
                data = s.read()
                # OS X
            dst = os.path.join(_sys_dir, scripts)

            if os.path.exists(dst):
                with open(dst + '.new', 'w') as w:
                    w.write(data.format(AIRFLOW_HOME=AIRFLOW_HOME))
            else:
                with open(dst, 'w') as w:
                    w.write(data.format(AIRFLOW_HOME=AIRFLOW_HOME))

    # if platform == "linux" or platform == "linux2":
    # linux
    # elif platform == "win32":
    # Windows...

    # TODO: tmp, dags do not exist ???