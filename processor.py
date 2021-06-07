import bpm.processing as proc
import spacy
import os

if __name__ == '__main__':
    nlp = spacy.load("en_core_web_sm")
    if os.path.isdir('project.nlp'):
        nlp.from_disk('project.nlp')
    else:
        custom_stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]
        for w in custom_stopwords:
            nlp.vocab[w].is_stop = True

    year_str = ["1999","1998","1997","2001","2007"]

    for ys in year_str:
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/01.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/02.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/03.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/04.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/05.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/06.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/07.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/08.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/09.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/10.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/11.tgz")
        proc.process_archieve(nlp,"data/nyt_corpus/data/" + ys + "/12.tgz")
