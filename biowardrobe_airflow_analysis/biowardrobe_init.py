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
import sys

from .biowardrobe import Settings


def generate_biowardrobe_workflow():
    _template = u"""#!/usr/bin/env python3
from airflow import DAG
from biowardrobe_airflow_analysis.biowardrobe_workflows import create_biowardrobe_workflow
dag = create_biowardrobe_workflow("{}")
"""
    _settings = Settings.Settings()
    _settings.cursor.execute("select etype, workflow from experimenttype")
    for (etype, workflow) in _settings.cursor.fetchall():
        _filename = os.path.abspath(os.path.basename(os.path.splitext(workflow)[0])+'.py')
        _data = _template.format(workflow)
        with open(_filename, 'w') as generated_workflow_stream:
            generated_workflow_stream.write(_data)


# if __name__ == "__main__":
generate_biowardrobe_workflow()
