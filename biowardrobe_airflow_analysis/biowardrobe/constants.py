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
