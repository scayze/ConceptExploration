from numpy import vectorize
import spacy
import textacy
from textacy import extract
from spacy.tokens import DocBin
import textacy.representations.matrix_utils as matrix_utils
from functools import partial

vectorizer = None


def extract_terms(doc):
    return extract.terms(  
        doc,
        ngs=lambda doc: extract.ngrams(
            doc,
            n=[1,2],
            filter_nums=True,
            filter_punct=True,
            filter_stops=True,
        ),
        ents=partial(
            extract.entities,
            include_types=["PERSON","ORG","NORP","FAC","GPE","LOC","PRODUCT","EVENT"]
        )
    )

def generate_idf(nlp,docs):
    global vectorizer
    #corpus = textacy.Corpus(nlp,data =docs)
    vectorizer = textacy.representations.vectorizers.Vectorizer(
        tf_type='linear',
        idf_type='standard',
        #norm="l2",
        min_df=2,
    )

    extracted_terms = (extract_terms(doc) for doc in docs)
    vectorizer = vectorizer.fit(extracted_terms)



def get_tdidf(nlp,docs):
    global vectorizer
    corpus = textacy.Corpus(nlp,data =docs)

    extracted_terms = (extract_terms(doc) for doc in docs)
    return vectorizer.transform(extracted_terms)
