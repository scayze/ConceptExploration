import numpy as np
from sklearn.decomposition import PCA
import pickle
import os

embedding_vocab = None
embedding_data = None


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

def load_embeddings(filepath):
    embeddings= {}

    print("load file")
    with open(filepath, 'r', encoding="utf-8") as f:
        next(f) #Skip header row
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


#Potentially do TFIDF reweighting when encountering new word
def get_embedding(term):
    embedding_term = term.replace(" ","_")
    if embedding_term in embedding_vocab:
        #print("Return value for: " + term)    
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
            #print("Return mean for: " + term)    
            return np.stack(sub_word_embeddings).mean(axis=0) 
    #If everything fails, return default position
    #print("Return default for: " + term)    
    return np.array([0.0,0.0]) #Maybe choose a specific color instead of middle.


