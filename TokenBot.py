## TokenBot
#
# extracts text from HTML, and cleans it 
# tokenizes string input into sentences/words
# TODO:
# look up list of all html tags
# test HTML filtering/list of links scraped
##

import re #regex
import spacy, en_core_web_sm #tokenizer & model
from nltk import tokenize #standard tokenize lib
#import nltk; nltk.download('punkt')
from pprint import pprint #no idea
from bs4 import BeautifulSoup #text parser
import pyximport; pyximport.install(pyimport=True)
import parser #faster HTML text parser
from SearchBot import *

#parses HTML using whitelisting to return text and list of URLs
def get_text_bs(html):
    tree = BeautifulSoup(html, 'html.parser')
    text = tree.find_all(text=True)
    
    body = tree.body
    if body is None:
        return None

    output = ''
    link_list = []

    whitelist = [
        'p',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'div',
        'table',
        'a'
    ]

    for t in text:
	    if t.parent.name in whitelist:
                if t.name == 'a':
                    link_list.append(t.attr('href'))
                    output += '{} '.format("[URL]")
                else:
                    output += '{} '.format(t)    
    
    return output, link_list

#parses HTML using blacklisting to return text and list of URLs
def get_text_selectolax(html):
    tree = parser.HTMLParser(html)

    if tree.body is None:
        return None

    link_list = []    

    for url in tree.css('a'):
        link_list.append(url.attrs["href"])
        url.text = "[URL]"
        
    blacklist = [
        'link',
        'nav',
        'script',
        'style',
        'header',
        'meta',
        'input',
        '[document]',
        'noscript',
        'head',
        'html',
        'footer'
    ]    

    for sel in blacklist:
        for tag in tree.css(sel):
            tag.decompose()    
   
    text = tree.body.text(separator=' ') #is this separator ideal??
    return text, link_list

def clean_text(src):
    #src = src.replace("\n", " ") #could interfere with paragraph parsing
    src = src.replace("[\\^]", " ")
    src = src.replace("\"", " ")
    src = src.replace("\\s+", " ")
    #src = src.strip() #redundant
    return src

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt|Pres|Sr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|me|edu|us|tech|info)"
digits = "([0-9])"
    
#python -m spacy download en_core_web_sm
#word-level
def extract_words(text):
    nlp = en_core_web_sm.load()
    return nlp(text)

#word-level, keeping code/charts together better
def extract_words2(text):
    toknz = tokenize.api.StringTokenizer()
    toknz._string = " "
    #tokenize_sents() is character-level, w/ span it becomes coordinates
    return toknz.tokenize(text)

#pretty good
def extract_sentences_regex(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text) #added
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(". ",".<stop>")
    text = text.replace("? ","?<stop>")
    text = text.replace("! ","!<stop>")
    text = text.replace("<prd>",".") #should this go here or later?
    text = text.replace("e.g.","e<prd>g<prd>") #for example
    text = text.replace("i.e.","i<prd>e<prd>") #in other words
    text = text.replace("...","<prd><prd><prd>") #ellipses
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

#very good, especially with charts/code    
def extract_sentences2(text):
    return tokenize.sent_tokenize(text)

#nearly perfect
def extract_sentences_smart(text):
    trainer = tokenize.punkt.PunktTrainer()
    trainer.INCLUDE_ALL_COLLOCS = True
    trainer.train(text)

    tokz = tokenize.PunktSentenceTokenizer(trainer.get_params())

    abbrvs = ['st', 'mrs', 'ms', 'dr', 'prof', 'capt', 'cpt', 'lt',
     'mt', 'pres', 'sr', 'inc', 'ltd', 'jr', 'sr', 'co']    
    for abb in abbrvs:
        tokz._params.abbrev_types.add(abb)   
    print(tokz._params.abbrev_types)
    """
    for decision in tokz.debug_decisions(text):
        pprint(decision)
        print('=' * 30)
    """
    return tokz.tokenize(text)


test1 = "When a child asks her mother \"Where do babies come from?\", what should one reply to her?"
test2 = "Mr. James told me that Dr. Brown is not available today. I will try again tomorrow."
test3 = """To load a model, use spacy.load() with the model name, a shortcut link or a path to the model data directory.

import spacy
nlp = spacy.load(\"en_core_web_sm\")
doc = nlp(u\"This is a sentence.\")
You can also import a model directly via its full name and then call its load() method with no arguments. This should also work for older models in previous versions of spaCy.

import spacy
import en_core_web_sm

nlp = en_core_web_sm.load()
doc = nlp(u\"This is a sentence.\")
Manual download and installation
In some cases, you might prefer downloading the data manually, for example to place it into a custom directory. You can download the model via your browser from the latest releases, or configure your own download script using the URL of the archive file. The archive consists of a model directory that contains another directory with the model data.

└── en_core_web_sm-2.0.0.tar.gz       # downloaded archive
    ├── meta.json                     # model meta data
    ├── setup.py                      # setup file for pip installation
    └── en_core_web_md                # model directory
        ├── __init__.py               # init for pip installation
        ├── meta.json                 # model meta data
        └── en_core_web_sm-2.0.0      # model data
You can place the model data directory anywhere on your local file system. To use it with spaCy, simply assign it a name by creating a shortcut link for the data directory.

book For more info and examples, check out the models documentation.

spaCy v1.x Releases
Date	Model	Version	Dep	Ent	Vec	Size	License		
2017-06-06	es_core_web_md	1.0.0	X	X	X	377 MB	CC BY-SA		
2017-04-26	fr_depvec_web_lg	1.0.0	X		X	1.33 GB	CC BY-NC		
2017-03-21	en_core_web_md	1.2.1	X	X	X	1 GB	CC BY-SA		
2017-03-21	en_depent_web_md	1.2.1	X	X		328 MB	CC BY-SA		
2017-03-17	en_core_web_sm	1.2.0	X	X	X	50 MB	CC BY-SA		
2017-03-17	en_core_web_md	1.2.0	X	X	X	1 GB	CC BY-SA		
2017-03-17	en_depent_web_md	1.2.0	X	X		328 MB	CC BY-SA		
2016-05-10	de_core_news_md	1.0.0	X	X	X	645 MB	CC BY-SA		
2016-03-08	en_vectors_glove_md	1.0.0			X	727 MB	CC BY-SA		
Issues and bug reports
To report an issue with a model, please open an issue on the spaCy issue tracker. Please note that no model is perfect. Because models are statistical, their expected behaviour will always include some errors. However, particular errors can indicate deeper issues with the training feature extraction or optimisation code. If you come across patterns in the model\'s performance that seem suspicious, please do file a report."""
testtext = test3
testURL = "https://en.wikipedia.org/wiki/Machine_learning"

tok_list = []

def test_tokenizers(text, toks):
    '''
    for tok in toks[2:]:
        sents = globals()[tok](text)
        for sent in sents:
            print(sent)  
    '''
    sents = extract_sentences_regex(text)
    for sent in sents:
        print(sent)
    sents = extract_sentences2(text)
    for sent in sents:
        print(sent)
    snts = extract_sentences_smart(text)
    for snt in snts:
        print(snt)

test_tokenizers(testtext, tok_list)        