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

from functools import lru_cache


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
