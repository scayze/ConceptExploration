#
# This file contains all functions related to generating and loading the word embeddings.
#

import numpy as np
from sklearn.decomposition import PCA
import pickle
import os
from annoy import AnnoyIndex
from bpm import tf_idf as tf

#TODO: Make this file a class.
embedding_vocab = None #The vocabulary of our embeddings
embedding_data = None #The data structure containing all embeddings
word2id = None

annoyNB = None
annoyVOCAB = None 

# Load the embeddings from disk if they already have been computed,
# otherwise generate them.
def initialize_embeddings():
    global embedding_data
    global embedding_vocab
    global word2id
    global annoyNB
    global annoyVOCAB

    annoyNB = AnnoyIndex(300,"angular")
    annoyNB.load("numberbatch.ann")

    annoyVOCAB = AnnoyIndex(300,"angular")
    annoyVOCAB.load("test.ann")

    filename = "2d_data_numberbatch.pck"

    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            embedding_vocab = data[0]
            embedding_data = data[1]
    else:
        print("Generating word embeddings data from scratch")
        e = load_embeddings("data/embeddings/numberbatch-en.txt")
        embedding_vocab, embedding_data = reduce_embeddings_PCA(e)
        with open(filename, 'wb') as f:
            pickle.dump([embedding_vocab,embedding_data], f)
    
    word2id = dict(zip(embedding_vocab,range(0,len(embedding_vocab))))

#This files read the Numberbatch word embeddings from file and parse them into a dictionary
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

# This function applies PCA to reduce the embeddings to 2 dimensions.
def reduce_embeddings_PCA(embeddings):
    print("Applying PCA")
    pca = PCA(n_components=2)

    # Get the data in the right format for sklearns PCA
    words =  list(embeddings.keys())
    vectors = [embeddings[word] for word in words]
    
    # Apply PCA to the data
    Y = pca.fit_transform(vectors)
    
    return words, Y

#TODO: Merge with get_embedding_vector()
#Thie function returns the 2d embedding of out input term 
def get_embedding(term):
    # Spaces are denotes as underscores in our embedding dataset
    embedding_term = term.replace(" ","_")
    # Return the embedding of the word, if it exists in the dataset
    if embedding_term in embedding_vocab:
        idx = embedding_vocab.index(embedding_term) 
        return embedding_data[idx]
    elif " " in term:
        sub_words = term.split(" ")
        sub_word_embeddings = []
        for sw in sub_words:
            if sw in embedding_vocab: 
                idx = embedding_vocab.index(sw) 
                sub_word_embeddings.append(embedding_data[idx])
        if len(sub_word_embeddings) > 0:
            #Calculate the mean of the wordembeddings
            return np.stack(sub_word_embeddings).mean(axis=0) 
    #If everything fails, return default position
    return np.array([0.0,0.0]) #Maybe choose a specific color instead of middle.

#Thie function returns the embedding of our input term
def get_embedding_vector(term):
    # Spaces are denotes as underscores in our embedding dataset
    embedding_term = term.replace(" ","_")
    # Return the embedding of the word, if it exists in the dataset
    if embedding_term in tf.word2id:
        idx = tf.word2id[embedding_term]
        return annoyNB.get_item_vector(idx)
    elif " " in term:
        sub_words = term.split(" ")
        sub_word_embeddings = []
        for sw in sub_words:
            if sw in embedding_vocab: 
                idx = embedding_vocab.index(sw)
                sub_word_embeddings.append(annoyNB.get_item_vector(idx))
        if len(sub_word_embeddings) > 0:
            #Calculate the mean of the wordembeddings
            return np.stack(sub_word_embeddings).mean(axis=0) 
    #If everything fails, return default position
    return None #Maybe choose a specific color instead of middle.

# This function finds similar terms within the vocabulary to the input term.
def find_similar(term):
    vector = get_embedding_vector(term)
    result = annoyVOCAB.get_nns_by_vector(vector, 5) #Get the 5 nearest neighbours with annoy
    print(result)
    for r in result:
        print(tf.id2word[r])
    
    return [tf.id2word[r] for r in result]
