import math
import os
import os.path
from .. import github_archives_index as indexer

# select random data from datasource, make a smaller sample for testing

DS_ORIGIN_DIR = ""
DS_SAMPLE_DIR = ""
MAX_SAMPLE_SIZE_IN_MB = 50000
MAX_SAMPLE_COUNT = math.inf

# since the origin datasource is too large, we need to use index file to get the samples
# list the repositories with MAX_SAMPLE_COUNT

indexes = indexer.read_index_from_file(DS_ORIGIN_DIR)

print(indexes)
