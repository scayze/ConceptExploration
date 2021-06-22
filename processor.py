#import bpm.processing as proc
import bpm.nyt_corpus as nyt
#import spacy
#import os
import pandas as pd

if __name__ == '__main__':
    nyt.generate_term_dfs(pd.to_datetime("1970"),pd.to_datetime("1997"))
