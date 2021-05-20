import spacy
from spacy.tokens import DocBin
import pandas as pd
import regex as re
import os
from nltk.corpus import stopwords
from spacy.lang.en.stop_words import STOP_WORDS
import tarfile
import nyt_corpus as nyt



if __name__ == '__main__':
    nlp = spacy.load("en_core_web_sm", disable=['parser'])
    nlp.from_disk('project.nlp')
    bin = DocBin().from_disk("data/nyt_corpus/data/2000/01.spacy")
    i = 0
    for doc in bin.get_docs(nlp.vocab):
        i+=1
        if i<2:
            info = ""
            lemmas = ""
            for token in doc:
                info += str(token) + " "
                lemmas += token.lemma_ + " "
            print(info)
            print(lemmas)
        #print(doc.user_data)

