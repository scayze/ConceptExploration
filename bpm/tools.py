#
# This file contains various utility function used throughout the project
#

from multiprocessing import Pool
from functools import partial
import pandas as pd
import numpy as np
import editdistance

# The following three methods allow to apply functions to a pandas DataFrame using multiprocessing.
# Taken from https://stackoverflow.com/a/53135031/5367241
def parallelize(data, func, num_of_processes=4):
    data_split = np.array_split(data, num_of_processes)
    pool = Pool(num_of_processes)
    data = pd.concat(pool.map(func, data_split))
    pool.close()
    pool.join()
    return data

def run_on_subset(func, data_subset):
    return data_subset.apply(func)

def parallelize_on_rows(data, func, num_of_processes=4):
    return parallelize(data, partial(run_on_subset, func), num_of_processes)

# Mimics the usage of np.argpartition, but on csr_matrices. 
# Taken from https://stackoverflow.com/a/52304675/5367241
def top_n_idx_sparse(matrix, n):
    print(type(matrix))
    '''Return index of top n values in each row of a sparse matrix'''
    top_n_idx = []
    for le, ri in zip(matrix.indptr[:-1], matrix.indptr[1:]):
        n_row_pick = min(n, ri - le)
        top_n_idx.append(matrix.indices[le + np.argpartition(matrix.data[le:ri], -n_row_pick)[-n_row_pick:]])
    return top_n_idx

# This is a terribly written function which continue to filter the results of a query until
# it does not self reference its search term, and editdistances are big enough between all terms.
def get_topn_filtered(matrix,names,term,count):
    no_duplicates = False
    topn_idx = []
    duplicates = []

    while no_duplicates == False:
        no_duplicates = True
        new_count = count + len(duplicates)

        topn_idx = matrix.data.argpartition(-new_count)[-new_count:]
        topn_idx = [matrix.indices[i] for i in topn_idx]
        #np.argpartition(matrix, -new_count)[-new_count:]

        for i in range(0,len(topn_idx)):
            #Filter the searhterm itself if it exists in the results
            if names[topn_idx[i]] == term:
                if term not in duplicates: 
                    duplicates.append(term)
                    no_duplicates = False
                    break
            #Filter similar words with editdistance < 5
            for j in range(i+1,len(topn_idx)):
                nameI = names[topn_idx[i]]
                nameJ = names[topn_idx[j]]
                dist = editdistance.eval(nameI,nameJ)
                if dist < 5: 
                    longer = nameI if len(nameI) < len(nameJ) else nameJ
                    if longer not in duplicates: 
                        duplicates.append(longer)
                        no_duplicates = False
    output = []
    for i in topn_idx:
        if names[i] not in duplicates:
            output.append(i)
    return output

# This method slightly alters the DateTimeIndex of a DataFrame
# by a couple nano seconds, such that the DateTimeIndex becomes unique.
# A unique DateTimeIndex is required for slicing the DataFrame by a Timestamp (df.loc[a:b])
def make_index_unique(df):
    dt = pd.to_datetime(df.index)
    delta = pd.to_timedelta(df.groupby(dt).cumcount(), unit='ns')
    df.index = (dt + delta.values)
    df.sort_index(inplace=True)

# Recursively removes all specified keys from a dict
# Taken from https://stackoverflow.com/a/20692955/5367241
def scrub(obj, bad_key="_this_is_bad"):
    if isinstance(obj, dict):
        # the call to `list` is useless for py2 but makes
        # the code py2/py3 compatible
        for key in list(obj.keys()):
            if key == bad_key:
                del obj[key]
            else:
                scrub(obj[key], bad_key)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            if obj[i] == bad_key:
                del obj[i]
            else:
                scrub(obj[i], bad_key)

    else:
        # neither a dict nor a list, do nothing
        pass


# Splits an array a into n pieces with (if possible) equal length.
# Taken from https://stackoverflow.com/a/2135920/5367241
def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

