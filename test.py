
import os
import pandas as pd
import bpm.nyt_corpus as nyt
import pandas as pd
import tarfile


path = 'data/nyt_corpus/data/'
for root, dirs, files in os.walk(path):
    for f in files:
        if not f.endswith('.pck'): continue

        file_no_extension = f[:-4]
        file_tgz = file_no_extension + ".tgz"
        file_fth = file_no_extension + ".fth"

        p = os.path.join(root, f) #Get full path between the base path and the file
        path_tgz = os.path.join(root, file_tgz)
        path_fth = os.path.join(root, file_fth)

        df = pd.read_pickle(p)
        print(p)
        #df.to_parquet(p)

        doclist = []
        with tarfile.open(path_tgz, 'r:*') as tar:
            for inner_file in tar:
                # Skip everything but the articles
                if not inner_file.name.endswith(".xml"): continue
                # Extract single document
                
                content = tar.extractfile(inner_file).read().decode('utf8')
                url, date, doc = nyt.read_nitf_file(content)
                if doc == "": continue
                doclist.append(doc)
        df["fulltext"] = doclist
        df = df.reset_index()
        df.to_feather(path_fth)
