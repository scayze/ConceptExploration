import re
import nltk
import pandas
import numpy as np
from MulticoreTSNE import MulticoreTSNE as TSNE #from sklearn.manifold import TSNE 
from sklearn.decomposition import PCA
from pandas import DataFrame
from nltk.corpus import stopwords
import matplotlib.pyplot as plt
import pickle

def load_embeddings(filepath):
    embeddings= {}

    print("load file")
    with open(filepath, 'r', encoding="utf-8") as f:
        for line in f:
            tokens = line.split(" ")
            word = tokens[0]
            vector = np.asarray(tokens[1:], "float32")
            embeddings[word] = vector

    return embeddings

def reduce_embeddings_PCA(embeddings):
    print("init PCA")
    pca = PCA(n_components=2)

    print("get word data in proper format")
    words =  list(embeddings.keys())

    print("get value data in proper format")
    vectors = [embeddings[word] for word in words]
    
    print("transform that shit")
    Y = pca.fit_transform(vectors)
    
    return words, Y

def reduce_embeddings_TSNE(embeddings):
    print("init TSNE")
    tsne = TSNE(n_jobs=4,n_components=2)

    print("get word data in proper format")
    words =  list(embeddings.keys())

    print("get value data in proper format")
    vectors = [embeddings[word] for word in words]
    array = np.array(vectors)

    print("transform that shit")
    Y = tsne.fit_transform(array)
    
    return words, Y


e = load_embeddings("data/glove/glove.6B.300d.txt")
words, Y = reduce_embeddings_PCA(e)
print(Y)
print(Y[5])



with open('2d_data.pk', 'wb') as f:
    pickle.dump([words,Y], f)