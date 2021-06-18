from multiprocessing import  Pool
from functools import partial
import pandas as pd
import numpy as np
import editdistance

def parallelize(data, func, num_of_processes=4):
    data_split = np.array_split(data, num_of_processes)
    pool = Pool(num_of_processes)
    data = pd.concat(pool.map(func, data_split))
    pool.close()
    pool.join()
    return data

def run_on_subset(func, data_subset):
    return data_subset.apply(func)

# Enables parallel execution of a function on each row of a dataframe
def parallelize_on_rows(data, func, num_of_processes=4):
    return parallelize(data, partial(run_on_subset, func), num_of_processes)

# From https://stackoverflow.com/questions/49207275/finding-the-top-n-values-in-a-row-of-a-scipy-sparse-matrix
def top_n_idx_sparse(matrix, n):
    '''Return index of top n values in each row of a sparse matrix'''
    top_n_idx = []
    for le, ri in zip(matrix.indptr[:-1], matrix.indptr[1:]):
        n_row_pick = min(n, ri - le)
        top_n_idx.append(matrix.indices[le + np.argpartition(matrix.data[le:ri], -n_row_pick)[-n_row_pick:]])
    return top_n_idx

def group_dataframe_pd(df,interval,origin):
    grouped_df = df.groupby(pd.Grouper(freq=str(interval) + "MS", label="left", origin=origin))
    df = grouped_df['textdata'].agg(textdata="sum")
    df["document_count"] = grouped_df['textdata'].agg(document_count="count")
    # HACK: to get the group-by values back to time origin because APPAREntlY fucking pd.Grouper.origin is buggeeededddd
    if interval == 1:
        df.index = df.index.map(lambda x: pd.to_datetime(x).replace(day=1))
    else:
        df.index = df.index.map(lambda x: pd.to_datetime(x).replace(day=1,month=1))
    
    return pd.DataFrame(df)

def get_topn_filtered(matrix,names,term,count):
    no_duplicates = False
    topn_idx = []
    duplicates = []

    while no_duplicates == False:
        no_duplicates = True
        new_count = count + len(duplicates)
        topn_idx = np.argpartition(matrix, -new_count)[-new_count:]

        for i in range(0,topn_idx.size):
            #Filter the searhterm itself if it exists in the results
            if names[topn_idx[i]] == term:
                if term not in duplicates: 
                    duplicates.append(term)
                    no_duplicates = False
                    break
            #Filter similar words with editdistance < 5
            for j in range(i+1,topn_idx.size):
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
# This is required for slicing the DataFrame by a Timestamp (df.loc[a:b])
def make_index_unique(df):
    dt = pd.to_datetime(df.index)
    delta = pd.to_timedelta(df.groupby(dt).cumcount(), unit='ns')
    df.index = (dt + delta.values)
    df = df.sort_index()


# Splits an array a into n pieces with (if possible) equal length.
def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

