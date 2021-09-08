#%%
import pandas as pd
import os
import time

import scipy
from scipy.sparse.csr import csr_matrix
import bpm.tf_idf as tf
from sklearn import preprocessing as skp
import scipy
import numpy as np
from collections import Counter
tf.initialize_idf()
#%%


def generate_concodrance_files():
    path = 'data/nyt_corpus/data/'
    for root, dirs, files in os.walk(path):
        for f in files:
            if not f.endswith('.pck_sparse'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file
            print(p)
            df = pd.read_pickle(p)
            del df["url"]
            df.to_pickle(p)

generate_concodrance_files()

#%%
df = pd.read_pickle("all_data.pck")
#%%

df = pd.read_pickle('data/nyt_corpus/data/2000/01.pck')


def to_ids(wordlist):
    # Create a list of indices from the feature names
    return [tf.word2id[word] for word in wordlist if word in tf.word2id] 

#Apply the function to the dataframe, and save it to disk.
df2 = df["textdata"].apply(to_ids)
print(df2)
df2.to_pickle("data/nyt_corpus/data/2000/01.aaa")


#%%

def calculate_tf_idf_scores_counter(df):
    c = Counter()
    df["textdata"].apply(lambda x: c.update(x))

    tfs = np.zeros(tf.idf.size)
    for word_id in c.keys():
        tfs[word_id] = c[word_id]
    tfidf = skp.normalize([np.multiply(tfs,tf.idf)])[0]
    return tf.id2word, tfidf

start = time.time()
df = pd.read_pickle('data/nyt_corpus/data/2000/01.pck')
end = time.time()
print(end-start)

start = time.time()
df_sparse = pd.read_pickle('data/nyt_corpus/data/2000/01.pck_sparse')
end = time.time()
print(end-start)

start = time.time()
df = pd.read_pickle('data/nyt_corpus/data/2000/01.aaa')
end = time.time()
print(end-start)

print("Time stack+sum")
start = time.time()
#mat = df_sparse["textdata"].agg('sum')
bm = scipy.sparse.vstack(df_sparse["textdata"])
b = bm.sum(axis=0)
csr_b = csr_matrix(b)
end = time.time()
print(end-start)
print(type(csr_b))
print(csr_b)

print("Time agg")
start = time.time()
mat = df_sparse["textdata"].agg('sum')
end = time.time()
print(end-start)
print(type(mat))
print(mat)

#%%
print("time counter 2")

a = tf.calculate_tf_idf_scores([mat])
df = df.reset_index().set_index("date")

start = time.time()
a = calculate_tf_idf_scores_counter(df)
end = time.time()
print(end-start)



#print(df["textdata"])


