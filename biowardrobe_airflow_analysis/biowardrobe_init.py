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
from sqlparse import split

from .biowardrobe import Settings

sql_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql_patch"))
system_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "system"))

_settings = Settings.Settings()


def apply_sql_patch(file):
    experimenttype_alter = os.path.join(sql_folder, "biowardrobe_tables", file)
    for _sql in split(open(experimenttype_alter).read()):
        if not _sql:
            continue
        _settings.cursor.execute(_sql)
        _settings.conn.commit()

def generate_biowardrobe_workflow():

    _settings.cursor.execute("select * from experimenttype limit 1")

    field_names = [i[0] for i in _settings.cursor.description]
    if 'workflow' in field_names:
        apply_sql_patch("experimenttype_patch.sql")
    apply_sql_patch("experimenttype_patch.sql")

    _template = u"""#!/usr/bin/env python3
from airflow import DAG
from biowardrobe_airflow_analysis.biowardrobe_workflows import create_biowardrobe_workflow
dag = create_biowardrobe_workflow("{}")
"""
    _settings.cursor.execute("select etype, workflow from experimenttype")
    for (etype, workflow) in _settings.cursor.fetchall():
        if not workflow:
            continue
        _filename = os.path.abspath(os.path.basename(os.path.splitext(workflow)[0])+'.py')
        _data = _template.format(workflow)
        with open(_filename, 'w') as generated_workflow_stream:
            generated_workflow_stream.write(_data)

    _template = u"""#!/usr/bin/env python3
from airflow import DAG
from biowardrobe_airflow_analysis.biowardrobe.download import dag, dag_t
d = dag
dt= dag_t
"""
    with open('biowardrobe_download.py', 'w') as generated_workflow_stream:
        generated_workflow_stream.write(_template)
