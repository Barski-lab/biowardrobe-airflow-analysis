#!/usr/bin/env python3

import os
import logging
from cwl_airflow_parser.cwldag import CWLDAG
from datetime import timedelta, datetime

from biowardrobe_cwl_workflows import available

from .operators import BioWardrobeJobDispatcher, BioWardrobeJobGatherer

_logger = logging.getLogger(__name__)


def create_biowardrobe_workflow(workflow):
    _workflow_file = available(workflow=workflow)

    dag = CWLDAG(default_args={
        'owner': 'airflow',
        'email': ['biowardrobe@biowardrobe.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 20,
        'retry_exponential_backoff': True,
        'retry_delay': timedelta(minutes=30),
        'max_retry_delay': timedelta(minutes=60 * 4)
    },
        cwl_workflow=_workflow_file)
    dag.create()
    dag.add(BioWardrobeJobDispatcher(dag=dag), to='top')
    dag.add(BioWardrobeJobGatherer(dag=dag), to='bottom')

    return dag
