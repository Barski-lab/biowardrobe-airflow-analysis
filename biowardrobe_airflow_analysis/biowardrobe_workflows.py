#!/usr/bin/env python3

import logging
from cwl_airflow_parser.cwldag import CWLDAG
from datetime import timedelta

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
        'pool': 'biowardrobe_basic_analysis',
        'retries': 10,
        'retry_exponential_backoff': True,
        'retry_delay': timedelta(minutes=60),
        'max_retry_delay': timedelta(minutes=60 * 24)
    },
        cwl_workflow=_workflow_file)
    dag.create()
    dag.add(BioWardrobeJobDispatcher(dag=dag), to='top')
    dag.add(BioWardrobeJobGatherer(dag=dag), to='bottom')

    return dag
