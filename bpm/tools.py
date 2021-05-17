from multiprocessing import  Pool
from functools import partial
import pandas as pd
import vaex as vx
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

def parallelize_on_rows(data, func, num_of_processes=4):
    return parallelize(data, partial(run_on_subset, func), num_of_processes)

def group_dataframe_vx(df,interval):
    df = df.groupby(
        by=vx.BinnerTime(df.date, resolution=str(interval)+'M'),
        agg={
            'textdata': 'sum'
        }
    )
    df.export_csv("lolalasdlasdla.csv")
    return df

def group_dataframe_pd(df,interval,date_from = "",date_to = ""):
    df = df.groupby(pd.Grouper(freq=str(interval) + "M"))
    df = df['data'].apply(lambda x: ''.join(x))
    if date_from != "" and date_to != "":
        start_date = pd.to_datetime(date_from)
        end_date = pd.to_datetime(date_to)
        df.index=pd.to_datetime(df.index)
        df = df.loc[start_date:end_date]
        #df = df.between_time(date_from,date_to)
        #df = df.loc[(df['time'] > pd.to_datetime(date_from)) & (df['time'] <= pd.to_datetime(date_to))]
    df.to_csv("dategroupselect.csv")
    return pd.DataFrame(df)

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))