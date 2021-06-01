import numpy as np
from MulticoreTSNE import MulticoreTSNE as TSNE #from sklearn.manifold import TSNE 
from sklearn.decomposition import PCA
import pickle

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

#Potentially do TFIDF reweighting when encountering new word
def get_embedding(data,vocab,term):
    embedding_term = term.replace(" ","_")
    if embedding_term in vocab:
        print("Return value for: " + term)    
        idx = vocab.index(embedding_term) 
        return data[idx]
    elif " " in term:
        sub_words = term.split(" ")
        sub_word_embeddings = []
        for sw in sub_words:
            if sw in vocab: 
                idx = vocab.index(sw) 
                sub_word_embeddings.append(data[idx])
        if len(sub_word_embeddings) > 0:
            #Calculate the mean of the wordembeddings
            print("Return mean for: " + term)    
            return np.stack(sub_word_embeddings).mean(axis=0) 
    #If everything fails, return default position
    print("Return default for: " + term)    
    return np.array([0.0,0.0]) #Maybe choose a specific color instead of middle.


def generate_embeddings():
    e = load_embeddings("data/glove/numberbatch-en.txt")
    words, Y = reduce_embeddings_PCA(e)


    with open('2d_data_numberbatch.pck', 'wb') as f:
        pickle.dump([words,Y], f)