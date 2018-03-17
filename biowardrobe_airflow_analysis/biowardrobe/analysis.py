#!/usr/bin/env python3
"""RNA-Seq SE(dUTP)/PE(dUTP), ChIP-Seq SE/PE script produces jobs for four workflows"""

import os
import datetime
import sys
from json import dumps, loads
from collections import OrderedDict
import logging
import decimal

from .utils import biowardrobe_settings, remove_not_set_inputs
from .constants import (STAR_INDICES,
                        BOWTIE_INDICES,
                        CHR_LENGTH_GENERIC_TSV,
                        ANNOTATIONS,
                        ANNOTATION_GENERIC_TSV)

_logger = logging.getLogger(__name__)


def get_biowardrobe_data(cursor, biowardrobe_uid):
    """Generate and export job file to a specific folder"""
    _settings = biowardrobe_settings(cursor)

    _sql = f"""select 
        e.etype, e.workflow, e.template, e.upload_rules, 

        g.db, g.findex, g.annotation, g.annottable, g.genome, g.gsize as genome_size, 

        l.uid, l.forcerun, l.url, l.params, l.deleted, 
        COALESCE(l.trim5,0) as clip_5p_end, COALESCE(l.trim3,0) as clip_3p_end,
        COALESCE(fragmentsizeexp,0) as exp_fragment_size, COALESCE(fragmentsizeforceuse,0) as force_fragment_size,
        COALESCE(l.rmdup,0) as remove_duplicates,
        COALESCE(control,0) as control, COALESCE(control_id,'') as control_id,

        COALESCE(a.properties,0) as broad_peak,

        COALESCE(w.email,'') as email
        
        from labdata l
        inner join (experimenttype e,genome g ) ON (e.id=experimenttype_id and g.id=genome_id)
        LEFT JOIN (antibody a) ON (l.antibody_id=a.id)
        LEFT JOIN (worker w) ON (l.worker_id=w.id)

        where l.uid='{biowardrobe_uid}' """
    #  COALESCE(egroup_id, '') <> '' and COALESCE(name4browser, '') <> ''

    _logger.debug(f"SQL: {_sql}")

    cursor.execute(_sql)
    row = cursor.fetchone()
    if not row:
        return None

    def norm_path(path):
        return os.path.abspath(os.path.normpath(os.path.normcase(path)))

    kwargs = row
    kwargs.update({
        "pair": ('pair' in row['etype']),
        "dUTP": ('dUTP' in row['etype']),
        "forcerun": (int(row['forcerun']) == 1),
        "spike": ('spike' in row['genome']),
        "force_fragment_size": (int(row['force_fragment_size']) == 1),
        "broad_peak": (int(row['broad_peak']) == 2),
        "remove_duplicates": (int(row['remove_duplicates']) == 1),
        "params": row['params'] if row['params'] else '{}',
        "raw_data": norm_path("/".join((_settings['wardrobe'], _settings['preliminary']))),
        "upload": norm_path("/".join((_settings['wardrobe'], _settings['upload']))),
        "indices": norm_path("/".join((_settings['wardrobe'], _settings['indices']))),
        "threads": _settings['maxthreads'],
        "experimentsdb": _settings['experimentsdb']
    })
    kwargs.update({
        # TODO: move extension into database
        "fastq_file_upstream": norm_path("/".join((kwargs["raw_data"], kwargs["uid"], kwargs["uid"] + '.fastq.bz2'))),
        "fastq_file_downstream": norm_path("/".join((kwargs["raw_data"], kwargs["uid"], kwargs["uid"] + '_2.fastq.bz2'))),
        "star_indices_folder": norm_path("/".join((kwargs["indices"], STAR_INDICES, kwargs["findex"]))),
        "bowtie_indices_folder": norm_path("/".join((kwargs["indices"], BOWTIE_INDICES, kwargs["findex"]))),
        "bowtie_indices_folder_ribo": norm_path("/".join((kwargs["indices"], BOWTIE_INDICES, kwargs["findex"] + "_ribo"))),
        "chrom_length": norm_path("/".join((kwargs["indices"], BOWTIE_INDICES, kwargs["findex"], CHR_LENGTH_GENERIC_TSV))),
        "annotation_input_file": norm_path("/".join((kwargs["indices"], ANNOTATIONS, kwargs["findex"],
                                                     ANNOTATION_GENERIC_TSV))),
        "exclude_chr": "control" if kwargs["spike"] else "",
        "output_folder": norm_path("/".join((kwargs["raw_data"], kwargs["uid"]))),
        "control_file": norm_path("/".join((kwargs["raw_data"], kwargs["control_id"], kwargs["control_id"] + '.bam')))
        if kwargs['control_id'] else None
    })

    #### Uncomment
    # if not os.path.isfile(kwargs["fastq_file_upstream"]) or (
    #             kwargs['pair'] and not os.path.isfile(kwargs["fastq_file_downstream"])):
    #     raise BiowFileNotFoundException(kwargs["uid"])

    kwargs = {key: (value if not isinstance(value, decimal.Decimal) else int(value)) for key, value in kwargs.items()}

    filled_job_object = remove_not_set_inputs(loads(kwargs['template'].
                                                    replace('\n', ' ').format(**kwargs).
                                                    replace("'True'", 'true').replace("'False'", 'false').
                                                    replace('"True"', 'true').replace('"False"', 'false')))
    filled_job = OrderedDict(sorted(filled_job_object.items()))

    kwargs['job'] = filled_job

    _logger.info("Result: \n{}".format(dumps(kwargs, indent=4)))
    return kwargs

