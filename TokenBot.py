## TokenBot
#
# tokenizes string input into sentences/words
#
##

import re, spacy
from nltk import tokenize
from pprint import pprint

test1="When a child asks her mother \"Where do babies come from?\", what should one reply to her?"
test2 = "Mr. James told me that Dr. Brown is not available today. I will try again tomorrow."

testtext = test1 + test2

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt|Pres|Sr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|me|edu|us|tech|info)"
digits = "([0-9])"

def extract_sentences1(text):
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
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".") #should this go here or later?
    text = text.replace("e.g.","e<prd>g<prd>") #for example
    text = text.replace("i.e.","i<prd>e<prd>") #in other words
    text = text.replace("...","<prd><prd><prd>") #ellipses
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences
    
#python -m spacy download en_core_web_sm
def extract_sentences2(text):
    nlp = spacy.load("en_core_web_sm")
    return nlp(text)
    
def extract_sentences3(text):
    return tokenize.sent_tokenize(text)

def extract_sentences3ish(text):
    return tokenize.tokenize(text)

def extract_sentences_smart(text):
    trainer = tokenize.punkt.PunktTrainer()
    trainer.INCLUDE_ALL_COLLOCS = True
    trainer.train(text)

    tokz = tokenizer.punkt.PunktSentenceTokenizer(trainer.get_params())

    print(tokz._params.abbrev_types)
    tokz._params.abbrev_types.add('dr')

    for decision in tokenizer.debug_decisions(sentences):
        pprint(decision)
        print('=' * 30)

    return tokz.tokenize(text)

def test_tokenizers(text):
    sentences = extract_sentences1(text)
    for line in sentences:
        print(line)
    sentences = extract_sentences2(text)
    for line in sentences:
        print(line)            
    sentences = extract_sentences3(text)
    for line in sentences:
        print(line)    
    sentences = extract_sentences3ish(text)
    for line in sentences:
        print(line)            

test_tokenizers(testtext)        