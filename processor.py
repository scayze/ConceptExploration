#import bpm.processing as proc
import bpm.nyt_corpus as nyt
import bpm.tf_idf as tf
#import spacy
#import os
import pandas as pd


if __name__ == '__main__':
    tf.initialize_idf()
    nyt.generate_sparse_term_dfs(pd.to_datetime("1997"),pd.to_datetime("2008"))
    #nyt.generate_term_dfs(pd.to_datetime("1970"),pd.to_datetime("1997"))
