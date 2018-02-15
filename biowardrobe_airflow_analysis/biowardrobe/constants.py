from .db_uploader import (upload_macs2_fragment_stat,
                          upload_iaintersect_result,
                          upload_get_stat,
                          upload_atdp,
                          upload_bigwig,
                          upload_bigwig_upstream,
                          upload_bigwig_downstream,
                          upload_rpkm,
                          upload_dateanalyzed,
                          upload_folder_size,
                          delete_files)


LIBSTATUS = {
    "START_DOWNLOAD":    0,     # Start downloading
    "FAIL_DOWNLOAD":     2000,  # Downloading error
    "SUCCESS_DOWNLOAD":  2,     # Downloading succeed
    "JOB_CREATED":       1010,  # Job file is created
    "RESTART_DOWNLOAD":  1000,  # Restart downloading
    "DOWNLOADING":       1,     # Downloading
    "START_PROCESS":     10,    # Start processing
    "FAIL_PROCESS":      2010,  # Processing failed
    "SUCCESS_PROCESS":   12,    # Processing succeed
    "PROCESSING":        11     # Processing
}


biowardrobe_connection_id = "biowardrobe"
BOWTIE_INDICES = "bowtie"
STAR_INDICES = "STAR"
ANNOTATIONS = "annotations"
CHR_LENGTH_GENERIC_TSV = "chrNameLength.txt"
ANNOTATION_GENERIC_TSV = "refgene.tsv"


# For both paired-end and single end
CHIP_SEQ_UPLOAD = {
    '{}_fragment_stat.tsv': upload_macs2_fragment_stat,
    '{}_macs_peaks_iaintersect.tsv': upload_iaintersect_result,
    '{}.stat': upload_get_stat,
    '{}_atdp.tsv': upload_atdp,
    '{}.bigWig': upload_bigwig,
    'set_dateanalyzed': upload_dateanalyzed,
    'upload_folder_size': upload_folder_size,
    '{}*.fastq': delete_files
}

# For both SE and PE (not dUTP)
RNA_SEQ_UPLOAD = {
    '{}.bigWig': upload_bigwig,
    '{}.stat': upload_get_stat,
    '{}.isoforms.csv': upload_rpkm,
    'set_dateanalyzed': upload_dateanalyzed,
    'upload_folder_size': upload_folder_size,
    '{}*.fastq': delete_files
}

# For both SE and PE (dUTP)
RNA_SEQ_DUTP_UPLOAD = {
    '{}_upstream.bigWig': upload_bigwig_upstream,
    '{}_downstream.bigWig': upload_bigwig_downstream,
    '{}.stat': upload_get_stat,
    '{}.isoforms.csv': upload_rpkm,
    'set_dateanalyzed': upload_dateanalyzed,
    'upload_folder_size': upload_folder_size,
    '{}*.fastq': delete_files
}

CHIP_SEQ_GEN_BIGWIG_UPLOAD = {'{}.bigWig': upload_bigwig}

# Upload functions for each experiment type
EXP_TYPE_UPLOAD = {
    "RNA-Seq":           RNA_SEQ_UPLOAD,
    "RNA-Seq dUTP":      RNA_SEQ_DUTP_UPLOAD,
    "RNA-Seq pair":      RNA_SEQ_UPLOAD,
    "RNA-Seq dUTP pair": RNA_SEQ_DUTP_UPLOAD,
    "RNA-Seq dUTP Mitochondrial": RNA_SEQ_DUTP_UPLOAD,
    "DNA-Seq":           CHIP_SEQ_UPLOAD,
    "DNA-Seq pair":      CHIP_SEQ_UPLOAD
}
