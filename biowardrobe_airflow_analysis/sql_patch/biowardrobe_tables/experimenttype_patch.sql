
# RNA-Seq
UPDATE `ems`.`experimenttype` SET
  workflow='rnaseq-se.cwl',
  template='{{
    "fastq_file": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "star_indices_folder": {{"class": "Directory", "location": "{star_indices_folder}"}},
    "bowtie_indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder_ribo}"}},
    "chrom_length_file": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "exclude_chr": "{exclude_chr}",
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
      "upload_bigwig",
      "upload_get_stat",
      "upload_rpkm",
      "upload_folder_size",
      "delete_files"
  ]'
WHERE etype='RNA-Seq';

# RNA-Seq pair
UPDATE `ems`.`experimenttype` SET
  workflow='rnaseq-pe.cwl',
  template='{{
    "fastq_file_upstream": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "fastq_file_downstream": {{"class": "File", "location": "{fastq_file_downstream}", "format": "http://edamontology.org/format_1930"}},
    "star_indices_folder": {{"class": "Directory", "location": "{star_indices_folder}"}},
    "bowtie_indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder_ribo}"}},
    "chrom_length_file": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "exclude_chr": "{exclude_chr}",
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
      "upload_bigwig",
      "upload_get_stat",
      "upload_rpkm",
      "upload_folder_size",
      "delete_files"
  ]'
WHERE etype='RNA-Seq pair';

# RNA-Seq dUTP
UPDATE `ems`.`experimenttype` SET
  workflow='rnaseq-se-dutp.cwl',
  template='{{
    "fastq_file": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "star_indices_folder": {{"class": "Directory", "location": "{star_indices_folder}"}},
    "bowtie_indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder_ribo}"}},
    "chrom_length_file": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "exclude_chr": "{exclude_chr}",
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
      "upload_bigwig_upstream",
      "upload_bigwig_downstream",
      "upload_get_stat",
      "upload_rpkm",
      "upload_folder_size",
      "delete_files"
  ]'
WHERE etype='RNA-Seq dUTP';

insert IGNORE into `ems`.`experimenttype` SELECT NULL, 'RNA-Seq dUTP Mitochondrial', '', '', '';

# RNA-Seq single dUTP Mitochondrial
UPDATE `ems`.`experimenttype` SET
  workflow='rnaseq-se-dutp-mitochondrial.cwl',
  template='{{
    "fastq_file": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "star_indices_folder": {{"class": "Directory", "location": "{star_indices_folder}"}},
    "star_indices_folder_mitochondrial": {{"class": "Directory", "location": "{star_indices_folder}-mitochondrial"}},
    "bowtie_indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder_ribo}"}},
    "chrom_length_file": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "exclude_chr": "{exclude_chr}",
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
      "upload_bigwig_upstream",
      "upload_bigwig_downstream",
      "upload_get_stat",
      "upload_rpkm",
      "upload_folder_size",
      "delete_files"
  ]'
WHERE etype='RNA-Seq dUTP Mitochondrial';

insert IGNORE into `ems`.`experimenttype` SELECT NULL, 'RNA-Seq dUTP pair Mitochondrial', '', '', '';

# RNA-Seq dUTP pair Mitochondrial
UPDATE `ems`.`experimenttype` SET
  workflow='rnaseq-pe-dutp-mitochondrial.cwl',
    template='{{
    "fastq_file_upstream": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "fastq_file_downstream": {{"class": "File", "location": "{fastq_file_downstream}", "format": "http://edamontology.org/format_1930"}},
    "star_indices_folder": {{"class": "Directory", "location": "{star_indices_folder}"}},
    "star_indices_folder_mitochondrial": {{"class": "Directory", "location": "{star_indices_folder}-mitochondrial"}},
    "bowtie_indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder_ribo}"}},
    "chrom_length_file": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "exclude_chr": "{exclude_chr}",
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',

  upload_rules='[
      "upload_bigwig_upstream",
      "upload_bigwig_downstream",
      "upload_get_stat",
      "upload_rpkm",
      "upload_folder_size",
      "delete_files"
  ]'
WHERE etype='RNA-Seq dUTP pair Mitochondrial';

# RNA-Seq dUTP pair
UPDATE `ems`.`experimenttype` SET
  workflow='rnaseq-pe-dutp.cwl',
  template='{{
    "fastq_file_upstream": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "fastq_file_downstream": {{"class": "File", "location": "{fastq_file_downstream}", "format": "http://edamontology.org/format_1930"}},
    "star_indices_folder": {{"class": "Directory", "location": "{star_indices_folder}"}},
    "bowtie_indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder_ribo}"}},
    "chrom_length_file": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "exclude_chr": "{exclude_chr}",
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
      "upload_bigwig_upstream",
      "upload_bigwig_downstream",
      "upload_get_stat",
      "upload_rpkm",
      "upload_folder_size",
      "delete_files"
  ]'
WHERE etype='RNA-Seq dUTP pair';

# DNA-Seq
UPDATE `ems`.`experimenttype` SET
  workflow='chipseq-se.cwl',
  template='{{
    "fastq_file": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder}"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "remove_duplicates": "{remove_duplicates}",
    "control_file": {{"class": "File", "location": "{control_file}", "format": "http://edamontology.org/format_2572"}},
    "exp_fragment_size": {exp_fragment_size},
    "force_fragment_size": "{force_fragment_size}",
    "broad_peak": "{broad_peak}",
    "chrom_length": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "genome_size": "{genome_size}",
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
    "upload_macs2_fragment_stat",
    "upload_iaintersect_result",
    "upload_get_stat",
    "upload_atdp",
    "upload_bigwig",
    "upload_folder_size",
    "delete_files"
  ]'
WHERE etype='DNA-Seq';

# DNA-Seq pair
UPDATE `ems`.`experimenttype` SET
  workflow='chipseq-pe.cwl',
  template='{{
    "fastq_file_upstream": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "fastq_file_downstream": {{"class": "File", "location": "{fastq_file_downstream}", "format": "http://edamontology.org/format_1930"}},
    "indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder}"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "remove_duplicates": "{remove_duplicates}",
    "control_file": {{"class": "File", "location": "{control_file}", "format": "http://edamontology.org/format_2572"}},
    "exp_fragment_size": {exp_fragment_size},
    "force_fragment_size": "{force_fragment_size}",
    "broad_peak": "{broad_peak}",
    "chrom_length": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "genome_size": "{genome_size}",
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
    "upload_macs2_fragment_stat",
    "upload_iaintersect_result",
    "upload_get_stat",
    "upload_atdp",
    "upload_bigwig",
    "upload_folder_size",
    "delete_files"
  ]'
WHERE etype='DNA-Seq pair';



insert IGNORE into `ems`.`experimenttype` SELECT NULL, 'DNA-Seq Trim Galore', '', '', '';

# DNA-Seq
UPDATE `ems`.`experimenttype` SET
  workflow='trim-chipseq-se.cwl',
  template='{{
    "fastq_file": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder}"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "remove_duplicates": "{remove_duplicates}",
    "control_file": {{"class": "File", "location": "{control_file}", "format": "http://edamontology.org/format_2572"}},
    "exp_fragment_size": {exp_fragment_size},
    "force_fragment_size": "{force_fragment_size}",
    "broad_peak": "{broad_peak}",
    "chrom_length": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "genome_size": "{genome_size}",
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
    "upload_macs2_fragment_stat",
    "upload_iaintersect_result",
    "upload_get_stat",
    "upload_atdp",
    "upload_bigwig",
    "upload_folder_size",
    "delete_files"
  ]'
WHERE etype='DNA-Seq Trim Galore';

insert IGNORE into `ems`.`experimenttype` SELECT NULL, 'DNA-Seq pair Trim Galore', '', '', '';

# DNA-Seq
UPDATE `ems`.`experimenttype` SET
  workflow='trim-chipseq-pe.cwl',
  template='{{
    "fastq_file_upstream": {{"class": "File", "location": "{fastq_file_upstream}", "format": "http://edamontology.org/format_1930"}},
    "fastq_file_downstream": {{"class": "File", "location": "{fastq_file_downstream}", "format": "http://edamontology.org/format_1930"}},
    "indices_folder": {{"class": "Directory", "location": "{bowtie_indices_folder}"}},
    "annotation_file": {{"class": "File", "location": "{annotation_input_file}", "format": "http://edamontology.org/format_3475"}},
    "clip_3p_end": {clip_3p_end},
    "clip_5p_end": {clip_5p_end},
    "threads": {threads},
    "remove_duplicates": "{remove_duplicates}",
    "control_file": {{"class": "File", "location": "{control_file}", "format": "http://edamontology.org/format_2572"}},
    "exp_fragment_size": {exp_fragment_size},
    "force_fragment_size": "{force_fragment_size}",
    "broad_peak": "{broad_peak}",
    "chrom_length": {{"class": "File", "location": "{chrom_length}", "format": "http://edamontology.org/format_2330"}},
    "genome_size": "{genome_size}",
    "output_folder": "{output_folder}",
    "uid": "{uid}"
  }}',
  upload_rules='[
    "upload_macs2_fragment_stat",
    "upload_iaintersect_result",
    "upload_get_stat",
    "upload_atdp",
    "upload_bigwig",
    "upload_folder_size",
    "delete_files"
  ]'
WHERE etype='DNA-Seq pair Trim Galore';
