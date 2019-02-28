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
import uuid
import logging
from json import loads
from functools import lru_cache
from sqlalchemy.exc import SQLAlchemyError
from airflow import settings
from airflow.models import DagRun


_logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def biowardrobe_settings(cursor):
    cursor.execute("select * from settings")
    return {row['key']: row['value'] for row in cursor.fetchall()}


def remove_not_set_inputs(job_object):
    """Remove all input parameters from job which are not set"""
    job_object_filtered ={}
    for key, value in job_object.items():
        if complete_input(value):
            job_object_filtered[key] = value
    return job_object_filtered


def complete_input(item):
    monitor = {"found_none": False}
    recursive_check(item, monitor)
    return not monitor["found_none"]


def recursive_check(item, monitor):
    if item == 'null' or item == 'None':
        monitor["found_none"] = True
    elif isinstance(item, dict):
        dict((k, v) for k, v in item.items() if recursive_check(v, monitor))
    elif isinstance(item, list):
        list(v for v in item if recursive_check(v, monitor))


def update_status(uid, message, code, conn, cursor, optional_column="", optional_where=""):
    """Update libstatus for current uid"""
    optional_column = optional_column if optional_column.startswith(',') else ',' + optional_column
    message = str(message).replace("'", '"')
    cursor.execute(f"""update labdata set libstatustxt='{message}', 
    libstatus={code} {optional_column} where uid='{uid}' 
    {optional_where}""")
    conn.commit()


def trigger_plugins(uid, cursor):
    cursor.execute(f"""SELECT e.id FROM experimenttype e
                       INNER JOIN (labdata l) ON (e.id=l.experimenttype_id)
                       WHERE l.uid='{uid}'""")
    exp_type_id = cursor.fetchone()["id"]
    cursor.execute("SELECT id, ptype, workflow, etype_id FROM plugintype")
    all_plugins = cursor.fetchall()
    selected_plugins = [plugin for plugin in all_plugins if exp_type_id in loads(plugin["etype_id"])]
    for plugin in selected_plugins:
        try:
            dag_id = os.path.splitext(plugin['workflow'])[0].replace(".", "_dot_")
            run_id = "__".join(["trig", uid, str(uuid.uuid4())])
            payload = {'uid': uid, 'run_id': run_id}
            session = settings.Session()
            dr = DagRun(dag_id=dag_id,
                        run_id=run_id,
                        conf=payload,
                        external_trigger=True)
            session.add(dr)
            session.commit()
            session.close()
            _logger.info(f"""Trigger {plugin["ptype"]} ({dag_id}) plugin for {uid}:\nrun_id: {run_id}""")
        except SQLAlchemyError as err:
            _logger.error(f"""Failed to trigger {plugin["ptype"]} ({dag_id}) plugin for {uid}\n {err}""")