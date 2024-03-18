#!/usr/bin/env python

#
#  Addbib takes an ADS bibtex entry and adds it to the ms.bib file.
#  Makes the shortcut FirstAuthor + 2digit year + b-z for more than one author/year combo.
#  Checks for collisions by exact match for title (Not as rigorus as it could be) 
#  Assumes there's a \n at the end of each line, otherwise appends:  for 'value' in the key value pairs, this might be a hassle.
#
#  Bibitem minimally mocks up the bibtex item.  
#     Stores author, year, journal, eprint number, shortcut info, lines from the original.
#  scrubnew takes a list of lines and generates two dicts of bibitems
#  scrubhtml, scrubfile first prepares lines from either html or a file
#
#  authordict is a dict by first author that contains every record for the author.
#

import pdb
import os
import glob
import shutil
def scrubhtml(url, new_item=False):
    """Pulls down url and returns (bibitems, authordict) from scrubnew"""

    bib_template = "http://adsabs.harvard.edu/cgi-bin/nph-bib_query?bibcode=%s&data_type=BIBTEX&db_key=AST&nocookieset=1"
    if url.startswith("http"):
        if re.match('.*bib_query.*',url):
            url_to_use = url
        else:
            match= re.match('http://adsabs.harvard.edu/abs/(.*)',url)
            if match is not None:
                url_to_use = bib_template%match.group(1)

    else:
        url_to_use = bib_templateb%url

    response = urllib.request.urlopen(url_to_use)
    html = response.read().decode()

    a,b= scrubnew(html.split('\n'),new_item)
    return a,b

def scrubfile(filename = 'newbib.bib', new_item=False):
    #if it exists, we need to be at the beginning to read it.
    #if it doesnt, we need to create it
    if os.path.exists(filename):
        fptr = open(filename,'r+')
    else:
        fptr = open(filename,'a+')
    lines=fptr.readlines()
    fptr.close()
    return scrubnew(lines,new_item)

def scrubnew(lines, new_item):
    biblines = []
    bibitems = {}
    authordict={}
    taking = False
    for line in lines:
        if line == '':
            continue
        #Might not be the best sanitation...
        if line.count('\n') == 0:
            line += '\n'
        if line[0] == '@':
            taking = True
        if taking:
            biblines.append(line)
        if line[0]=='}':
            taking = False
            bi =  bibitem( biblines,new_item=new_item )
            bibitems[bi.Shortcut] = bi
            authordict.setdefault(bi.FirstAuthor,{})
            authordict[bi.FirstAuthor].setdefault(bi.year,[])
            authordict[bi.FirstAuthor][bi.year].append(bi)
            biblines=[]
    return bibitems,authordict

import re
#author_year = re.compile(r'(.*{)([^\d]*)(\d\d)(.*),') 
author_year = re.compile(r'(.*{)([^\d]*)(\d*),')
no_year     = re.compile(r'(.*{)([^\d]*)[\d]*[abcd],')
author_year_shortcut = re.compile(r'([^\d]*)(\d\d)(.*)')
generic_short = re.compile(r'(.*){(.*),')
def sanitize_year(string):
    S1 = string.lstrip('{')
    S2 = S1.rstrip('}')
    return S2
def fullyear(twoyear):
    if int(twoyear[0]) < 2:
        return '20'+twoyear
    else:
        return '19'+twoyear

whitespace = re.compile(r'.*\S.*')
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
    print(string)
    special = ''
    count = 0
    full = ''
    n=1
    for c in string:
        if c == '}':
            count -= 1
            print('..',special,'..')
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

def sanitize_author(author):
    S1 = munch_n_deep(author,1)
    if S1 is None:
        S2 = author.lstrip('{')
        S3 = S2.strip()
        count = S3.count(',')
        if count > 0:
            index = S3.index(',')
        else:
            index = S3.index('}')

        S1 = S3[:index]
    FirstAuthor = munch_special(S1)
    return FirstAuthor
tmp_shortcut_counter = 0

class bibitem():
    def printer(self):
        for line in self.lines:
            print(line, end=' ')
    def __str__(self):
        return "BIB "+self.Shortcut
        #return str(self.lines)
    def __init__(self,lines,new_item=False,debug=0):
        global tmp_shortcut_counter

        #
        # If we've already sanitized the shortcut, pull out the info we want.
        #
        if not new_item:
            match = author_year.match(lines[0])
            if match is not None:
                self.Shortcut_FirstAuthor = match.group(2)
                self.Shortcut_NameYear = fullyear( match.group(3))
                self.Shortcut_Multiple = ''
                if len(match.groups()) > 3:
                    self.Shortcut_Multiple = match.group(4)
                self.Shortcut = self.Shortcut_FirstAuthor+self.Shortcut_NameYear[2:]+self.Shortcut_Multiple
                if debug > 0:
                    print(self.Shortcut)
            else:
                no_year_shortcut = no_year.match(lines[0])
                #print(no_year_shortcut.groups())
                #pdb.set_trace()
                self.Shortcut = no_year_shortcut.group(1)

        self.lines = lines
        self.things={}
        line=0
        while line < len(lines) - 2:
            line += 1

            this_line = lines[line]

            #Make sure that the 'line' contains all the braces.
            #keep catting until it does.
            while this_line.count('{') != this_line.count('}'):
                if debug>0:
                    print(line, lines[line][:-1])
                this_line += lines[line+1]
                line += 1
            #pair = this_line.split('=')
            #if len(pair) != 2:
            #    continue
            index = this_line.index('=')
            pair = this_line[:index], this_line[index+1:]
            if debug > 0:
                print('pair:',line,pair)
            key = pair[0].strip()
            value = pair[1].lstrip()
            value = value[:-2]
            self.things[key]=value

        self.year = self.things['year'].strip()
        self.FirstAuthor = sanitize_author(self.things['author'])
        if  new_item:
            self.Shortcut_FirstAuthor = self.FirstAuthor
            self.Shortcut_NameYear = sanitize_year(self.things['year'])
            self.Shortcut_Multiple = ''
            match = generic_short.match(lines[0])
            if match is None:
                print("Potential error on new bib item", lines[0])
                self.Shortcut = "TEMP_SHORTCUT_NAME"+tmp_shortcut_counter 
                tmp_shortcut_counter += 1
            self.Shortcut = match.group(2)
            #self.set_shortcut('')

        #ADS has some dumb things in their bibtex, like arxiv references.
        #Make it better.
        #acutally doesn't work.
        #self.scrub_journal() 
        

    def scrub_journal(self):
        """An attempt to automatically fix arxiv articles. Doesn't work."""
        if 'journal' in self.things:
            if self.things['journal'] == '{ArXiv e-prints}':
                """pre 2007"""
                #print self.things['journal'], "eprint post 2007", self.things['year'], self.things['eprint']
                self.things['journal'] = '{cock}'
            elif self.things['journal'] == '{ArXiv Astrophysics e-prints}':
                print(self.things['journal'], "eprint pre 2007", self.things['year'], self.things['eprint'])
                self.things['journal'] = '{cock}'



    def set_shortcut(self,multiple):
        self.Shortcut_Multiple=multiple
        self.Shortcut = self.Shortcut_FirstAuthor+self.Shortcut_NameYear[2:]+self.Shortcut_Multiple
        match = generic_short.match(self.lines[0])
        self.lines[0] = "%s{%s,\n"%(match.group(1), self.Shortcut)


import string
def InsertFourDigitYear(bib):
    match = author_year_shortcut.match(bib.Shortcut)
    if match is not None:
        Shortcut_FirstAuthor = match.group(1)
        Shortcut_NameYear = fullyear( match.group(2))
        Shortcut_Multiple = ''
        if len(match.groups()) > 2:
            Shortcut_Multiple = match.group(3)
        output= Shortcut_FirstAuthor+Shortcut_NameYear+Shortcut_Multiple
    else:
        output=bib.Shortcut
    return output


import urllib.request, urllib.error, urllib.parse
import sys
from optparse import OptionParser
if __name__ == '__main__':
    
#
    default_input_file = "%s/Downloads/export-bibtex.bib"%os.environ['HOME']
    parser = OptionParser("addbib.py -o <output=ms.bib> -i <input=~/Downloads/export-bibtex.bib>; url given prescedence.")
    #parser.add_option("-o", "--outfile", dest="outfile", action = "store", default = "main.bib")
    parser.add_option("-o", "--outfile", dest="outfile", action = "store", default = "m2.bib")
    parser.add_option("-i", "--infile", dest="infile", action = "store", default = default_input_file)
    parser.add_option("-t", "--test", dest="test", action = "store_true", default = False)
    parser.add_option("-l", "--lookup", dest="lookup", action = "store", default = None)
    parser.add_option("-c", "--clean", dest="clean", action="store", default=False)

    (options, args) = parser.parse_args()
    print(options)


    #
    #scrub the input file.
    #move it to old_bibs
    #

    #not doing a look up, much and parse.
    if os.path.exists(options.infile) == False:
        print("Please provide a filename with -i.")
        print("We default to looking for %s"%options.infile)
        sys.exit(1)
    newbib, newauthors = scrubfile(options.infile,new_item=True)

    if options.clean == True or options.clean == 'True':
        print(options.clean)

        if not os.path.exists("old_bibs"):
            os.mkdir("old_bibs")
        n_bibs = len(glob.glob("old_bibs/*"))
        to_this = "old_bibs/export-bibtex.bib.%d"%n_bibs
        shutil.move(options.infile,to_this)
        print("Move file to %s"%to_this)

    #
    # Scrub the output file.
    #
    if not options.test and not options.lookup:
        oldbib, authors = scrubfile(options.outfile,new_item=False)
    if options.lookup is not None:
        tomatch  = re.compile(r'.*%s.*'%options.lookup)
        sorted_bibs = list(newbib.values())
        sorted_bibs.sort(key=InsertFourDigitYear)
        for bib in sorted_bibs:
            match = tomatch.match( bib.Shortcut )
            if match is not None:
                bib.printer()

    if  not options.lookup:

        allnew=[]

        alphabet = dict(list(zip(list(range(26)),string.ascii_lowercase)))
        alphabet[0]='' #For the first one, it gets no distinction.
        for newb in list(newbib.values()):
            print("=========== Adding Title =========== ")
            newb.printer()
            AuthorYearMultiple = 0
            KeepBib = True
            if newb.FirstAuthor in authors:
                if newb.year in authors[newb.FirstAuthor]:
                    AuthorYearList = authors[newb.FirstAuthor][newb.year]
                    AuthorYearMultiple = len(AuthorYearList)
                    for otherbib in AuthorYearList:
                        OtherTitle = otherbib.things['title']
                        if newb.things['title'] == OtherTitle:
                            print("=========== Already Have Title ===========")
                            otherbib.printer()
                            KeepBib = False

            if KeepBib:
                print('NS',newb.Shortcut)
                newb.set_shortcut( alphabet[AuthorYearMultiple] )
                print('NP',newb.Shortcut)
                authors.setdefault(newb.FirstAuthor,{})
                authors[newb.FirstAuthor].setdefault(newb.year,[])
                authors[newb.FirstAuthor][newb.year].append(newb)
                oldbib[newb.Shortcut] = newb
                allnew.append(newb.Shortcut)
                print("=========== Success! \citet{%s} \citep{%s} =========== "%(newb.Shortcut, newb.Shortcut))
    
        fresh_full_bib = open(options.outfile,'w')
        sorted_bibs = list(oldbib.values())
        #pdb.set_trace()
        def just_key(bib):
            return bib.Shortcut
        sorted_bibs.sort(key=just_key)
        for i in sorted_bibs:
            for L in i.lines:
                fresh_full_bib.write(L)
            fresh_full_bib.write("\n")
        fresh_full_bib.close()
        if len(allnew) > 0:
            print("==== New Things! ===")
            for i in allnew:
                print(i)
        else:
            print("=== You have them all already ===")
    
#end
