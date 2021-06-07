from multiprocessing import  Pool
from functools import partial
import pandas as pd
import numpy as np


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


def group_dataframe_pd(df,interval,date_from,date_to):
    if date_from != "" and date_to != "":
        #df.index=pd.to_datetime(df.index)
        #df.sort_index()
        #print(df.head(2))
        df = df[(pd.to_datetime(df.index) >= date_from) & (pd.to_datetime(df.index) <= date_to)]
        #df = df.loc[date_from:date_to]
    df = df.groupby(pd.Grouper(freq=str(interval) + "M"))
    df = df['textdata'].agg(sum)
    return pd.DataFrame(df)

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

