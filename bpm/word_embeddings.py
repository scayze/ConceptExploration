#
# This file contains all functions related to generating and loading the word embeddings.
#

import numpy as np
from sklearn.decomposition import PCA
import pickle
import os

#TODO: Make this file a class.
embedding_vocab = None #The vocabulary of our embeddings
embedding_data = None #The data structure containing all embeddings

# Load the embeddings from disk if they already have been computed,
# otherwise generate them.
def initialize_embeddings():
    global embedding_data
    global embedding_vocab

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

#TODO: Potentially do TFIDF weighting of words?
#Thie function returns the embedding 
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


