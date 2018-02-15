#!/usr/bin/env python3

import os
import logging
from cwl_airflow_parser.cwldag import CWLDAG

from biowardrobe_cwl_workflows import available

from .operators.biowardrobejobreader import BioWardrobeJobReader
from .operators.biowardrobejobdone import BioWardrobeJobDone

_logger = logging.getLogger(__name__)


def create_biowardrobe_workflow(workflow):
    _workflow_file = available(workflow=workflow)

    dag = CWLDAG(cwl_workflow=_workflow_file)
    dag.create()
    dag.add(BioWardrobeJobReader(dag=dag), to='top')  # task_id="CWLJobReader",
    dag.add(BioWardrobeJobDone(dag=dag), to='bottom')  # reader_task_id="CWLJobReader")

    return dag
