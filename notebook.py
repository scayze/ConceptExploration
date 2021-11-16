#%%
import pandas as pd
import os
import time
from pandas.io import pickle

import scipy
from scipy.sparse.csr import csr_matrix
import bpm.tf_idf as tf
from sklearn import preprocessing as skp
import scipy
import numpy as np
import bpm.word_embeddings as we
from collections import Counter
import numpy as np
from annoy import AnnoyIndex
import pickle

#%%
tf.initialize_idf()
#%%
def load_embeddings(filepath):
    embeddings= {}

    print("Loading embeddings from file")
    with open(filepath, 'r', encoding="utf-8") as f:
        next(f) #Skip header row
        for line in f:
            tokens = line.split(" ")
            word = tokens[0]
            vector = np.asarray(tokens[1:], "float32")
            embeddings[word] = vector

    return embeddings

embeddings = load_embeddings("data/embeddings/numberbatch-en.txt")
embedding_vocab =  list(embeddings.keys())
embedding_data = [embeddings[word] for word in embedding_vocab]
word2id = dict(zip(embedding_vocab,range(0,len(embedding_vocab))))

with open("quicksave.pck", 'wb') as f:
    pickle.dump([embedding_vocab,embedding_data,word2id], f)

#%%
with open("quicksave.pck", 'rb') as f:
    data = pickle.load(f)
    embedding_vocab = data[0]
    embedding_data = data[1]
    word2id = data[2]
#%%
f = 300
t = AnnoyIndex(f, 'angular')
t.on_disk_build("numberbatch.ann")

for i in range(0,len(embedding_vocab)):
    t.add_item(i,embedding_data[i])


#%%
t.build(30)

#%%
def get_embedding(term):
    # Spaces are denotes as underscores in our embedding dataset
    embedding_term = term.replace(" ","_")
    # Return the embedding of the word, if it exists in the dataset
    if embedding_term in word2id:
        idx = word2id[embedding_term]
        return embedding_data[idx]
    elif " " in term:
        sub_words = term.split(" ")
        sub_word_embeddings = []
        for sw in sub_words:
            if sw in word2id: 
                idx = word2id[sw]
                sub_word_embeddings.append(embedding_data[idx])
        if len(sub_word_embeddings) > 0:
            #Calculate the mean of the wordembeddings
            return np.stack(sub_word_embeddings).mean(axis=0) 
    #If everything fails, return default position
    return None #Maybe choose a specific color instead of middle.

#%%
f = 300
t = AnnoyIndex(f, 'angular')
t.on_disk_build("test.ann")

for i in range(0,len(tf.id2word)):
    vector = get_embedding(tf.id2word[i])
    if vector is not None:
        t.add_item(i,vector)


#%%
t.build(30)

#%%

t = AnnoyIndex(300,"angular")
t.load("test.ann")

vector = get_embedding("genital")#keys.index("global_warming")
result = t.get_nns_by_vector(vector, 5)
print(result)
for r in result:
    print(tf.id2word[r])


# %%
