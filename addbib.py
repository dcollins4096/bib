#!/usr/bin/env python

import pdb
import os
import glob
import shutil
import bibtexparser
import numpy as np
from optparse import OptionParser

def munch_n_deep(string,n):
    out = ''
    count = 0
    for c in string:
        if c == '}':
            count -= 1
        if count > n:
            out += c
        if c == '{':
            count += 1
        if count == n and len(out) > 0:
            return out
def munch_special(string):
    special = ''
    count = 0
    full = ''
    n=1
    for c in string:
        if c == '}':
            count -= 1
            full += special[-1]
            special = ''
            continue
        elif c == '{':
            count += 1
            continue
        elif c == ' ':
            continue
        elif c == '\'':
            continue
        if count >= n:
            special += c
        else:
            full += c
    return full

def parse_and(author):
    some = author.split(' and ')
    if some == author:
        return None
    #print("===")
    #print(author)
    tokens = some[0].split(',')
    last_name = tokens[0].rstrip(',')
    last_name = last_name.strip()
    last_name = last_name.lstrip('{')
    last_name = last_name.rstrip('}')
    return last_name


def sanitize_author(author):
    ok = parse_and(author)
    ok = munch_special(ok)
    if ok is not None:
        return ok
    S1 = munch_n_deep(author,1)
    if S1 is None:
        S2 = author.lstrip('{')
        S3 = S2.strip()
        count = S3.count(',')
        if count > 0:
            index = S3.index(',')
        else:
            index = S3.index('}')

        S1 = S3[:index].strip().rstrip('}')


    FirstAuthor = munch_special(S1)
    return FirstAuthor
def parse_file(fname):
    fptr = open(fname,'r')
    lines = fptr.readlines()
    fptr.close()

    entries=[]
    taking = False
    for line in lines:
        if line.startswith('@'):
            taking = True
            this_entry = ''
        if taking:
            this_entry += line
        if line.startswith('}'):
            taking=False
            entries.append(this_entry)
    return entries

def read(fname):
    entries = parse_file( fname )
    library={}
    for nentry,entry in enumerate(entries):
        e = bibtexparser.parse_string(entry)
        if len(e.failed_blocks) >0:
            pdb.set_trace()
            print("FAILED BLOCKS")
        ee = e.entries[0]
        author_all = ee.fields_dict['author']
        year = ee.fields_dict['year'].value
        title = ee.fields_dict['title'].value

        #print("CLOWN",author_all)
        first_author = sanitize_author(author_all.value)
        if first_author not in library:
            library[first_author]={}
        if year not in library[first_author]:
            library[first_author][year]={}
        library[first_author][year][title]=e
    return library

def write(library,fname):
    authors = sorted(list(library.keys()))
    output = ""
    for author in authors:
        years = sorted(list(library[author].keys()))
        for year in years:
            keys = [entry.entries[0].key  for entry in library[author][year].values()]
            titles = np.array([entry.entries[0].fields_dict['title'].value  for entry in library[author][year].values()])
            order = np.argsort(keys)

            for ntitle, title in enumerate(titles[order]):
                e = library[author][year][title]
                output += bibtexparser.write_string(e)
    fptr=open(fname,'w')
    fptr.write(output)
    fptr.close()

if __name__ == '__main__':
    default_input_file = "%s/Downloads/export-bibtex.bib"%os.environ['HOME']
    parser = OptionParser("addbib.py -o <output=ms.bib> -i <input=~/Downloads/export-bibtex.bib>; url given prescedence.")
    #parser.add_option("-o", "--outfile", dest="outfile", action = "store", default = "main.bib")
    parser.add_option("-o", "--outfile", dest="outfile", action = "store", default = "m2.bib")
    parser.add_option("-i", "--infile", dest="infile", action = "store", default = default_input_file)
    parser.add_option("-t", "--test", dest="test", action = "store_true", default = False)
    parser.add_option("-l", "--lookup", dest="lookup", action = "store", default = None)
    parser.add_option("-c", "--clean", dest="clean", action="store_true", default=False)

    (options, args) = parser.parse_args()
    print(options)

    #read input library
    if not os.path.exists( options.infile ) :
        print("ERROR no extant input file %s"%options.infile)
    input_library = read( options.infile )

    if options.lookup:
        pass
    else:
        if  os.path.exists( options.outfile ) :
            output_library = read(options.outfile)
        else:
            print("No extant output file %s creating"%options.outfile)
            output_library={}
        for author in input_library:
            if author not in output_library:
                output_library[author]={}
            for year in input_library[author]:
                if year not in output_library[author]:
                    output_library[author][year] = {}
                key_offset = len(output_library[author][year])
                for ntitle, title in enumerate(input_library[author][year]):
                    if title not in output_library[author][year]:
                        ee = input_library[author][year][title]
                        year = ee.entries[0].fields_dict['year'].value
                        ntotal = key_offset + ntitle
                        this_key = (author+year[2:]+' bcdefghijklmnopqrstuvwxyz'[ntotal]).strip()
                        print("NEW",this_key)
                        ee.entries[0].key=this_key
                        output_library[author][year][title]=ee
                    else:
                        ee=output_library[author][year][title]
                        key = ee.entries[0].key
                        print("Have: %s %s"%(key, title))
        write( output_library, options.outfile)
    clean = ((options.clean == True)+(options.clean == 'True'))*(options.lookup==None)
    print("CLEAN",clean, options.clean, options.lookup)
    if clean:
        if not os.path.exists("old_bibs"):
            os.mkdir("old_bibs")
        n_bibs = len(glob.glob("old_bibs/*"))
        to_this = "old_bibs/old.bib.%d"%n_bibs
        shutil.move(options.infile,to_this)















#end
