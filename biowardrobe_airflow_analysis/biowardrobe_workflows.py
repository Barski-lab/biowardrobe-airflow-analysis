#!/usr/bin/env python3

import os
import logging
# from functools import lru_cache
from cwl_airflow_parser.cwldag import CWLDAG

from .operators.biowardrobejobreader import BioWardrobeJobReader
from .operators.cwljobfinalize import CWLJobFinalize

_logger = logging.getLogger(__name__)
# _logger.info("VARS: {0} {1} {2}".format(__name__,__package__,__file__))


def available_workflows(workflow=None):
    workflows_folder = os.path.dirname(os.path.abspath(__file__))+"/biowardrobe_workflows/workflows"

    all_workflows = {}
    for root, dirs, files in os.walk(workflows_folder):
        all_workflows.update(
            {filename: os.path.join(root, filename)
             for filename in files
             if os.path.splitext(filename)[1] == '.cwl'
             and (filename not in all_workflows
                  or os.path.getctime(os.path.join(root, filename)) <
                  os.path.getctime(all_workflows[filename]))
             }
        )
    _logger.debug("all_workflows: {0}".format(all_workflows))

    if workflow and workflow not in all_workflows:
        raise Exception("Can't find workflow %s" % workflow)

    return all_workflows[workflow] if workflow else all_workflows


# @lru_cache(maxsize=256)
def create_biowardrobe_workflow(workflow):
    _workflow_file = available_workflows(workflow=workflow)

    dag = CWLDAG(cwl_workflow=_workflow_file)
    dag.create()
    dag.add(BioWardrobeJobReader(dag=dag), to='top')  # task_id="CWLJobReader",
    dag.add(CWLJobFinalize(dag=dag), to='bottom')  # reader_task_id="CWLJobReader")

    return dag
