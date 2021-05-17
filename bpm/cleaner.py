import re
import nltk
import pandas
from pandas import DataFrame
from nltk.corpus import stopwords

def clean_file(filepath):
    df = pandas.read_csv(filepath)
    df['cleaned_content']=df['sentences'].apply(lambda x: clean_text(x))
    df.to_csv(filepath)

def clean_text(text): #clean text
    clean_text = re.sub('[^A-Za-z.]', ' ', text.lower()) #remove non-alphabets
    #tokenized_text = nltk.word_tokenize(text) #tokenize
    #clean_text = [
    #     word for word in tokenized_text
    #     if word not in stopwords.words("english")
    #]
    return clean_text
