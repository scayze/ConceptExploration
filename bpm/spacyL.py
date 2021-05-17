import spacy
import pandas as pd
import regex as re
from nltk.corpus import stopwords
from spacy.lang.en.stop_words import STOP_WORDS
import bpm 

nlp = spacy.load("en_core_web_sm", disable=['parser', 'ner'])
#nlp.initialize()


stops = STOP_WORDS
count=0

def normalize(text):
    global count
    sentences = text.split(".")
    for i in range(0,len(sentences)):
        doc = nlp(sentences[i])
        sentences[i] = ""
        for token in doc:
            if token in stops: continue
            sentences[i] += " " + token.lemma_.lower()
        
        #sentences[i] = re.sub(r"[#@<>-_,;()\[\]{}=+-'\"]", ' ', sentences[i])
        sentences[i] = re.sub(r"[^a-zA-Z]+", ' ', sentences[i])


    count += 1
    print(count)
    return ".".join(sentences)

def create_dataframe(interval):  
    df = pd.read_csv("scripts/data/articles1.csv")[["time","sentences"]]
    df["sentences"] = bpm.tools.parallelize_on_rows(df["sentences"],normalize)
    df.to_csv("scripts/data/lemmatest.csv")
    return df

if __name__ == '__main__':
    create_dataframe(12)

