import urllib
from urllib import request
from urllib import parse
from urllib.parse import urlsplit, urlunsplit
from urllib import robotparser
from bs4 import BeautifulSoup
import nltk
import pickle
import threading
import math

# Starter URLs
URL1 = 'https://www.californiacarnivores.com/apps/help-center'
URL2 = 'https://predatoryplants.com/blogs/plant-care'
URL3 = 'https://www.growcarnivorousplants.com/carnivorous-plant-care/'

# words to avoid in urls to avoid getting useless social media and login pages
donotvisit = ['pinterest','youtube','facebook','instagram','login','logout','authentication','podcast','spotify', 'feedburner', 'javascript']
# base forms of the starter urls, just hardcoding these since we know what they'll be
baseurls = ['https://www.californiacarnivores.com/', 'https://predatoryplants.com/','https://www.growcarnivorousplants.com/']

# list of urls that we use for the knowledge base and their text from beautifulsoup
url_list = []
text_list = []

def web_crawl(starter):
    # create the local object so none of the threads access each other's variables
    local = threading.local()
    # set the search list to the starter url to kickstart crawling
    local.search_list = [starter]

    # loops through and finds 25 urls
    while len(local.search_list) > 0 and len(url_list) < 25:

        # checks a url if it appears to be a valid url and it is not already in the list of accepted urls
        # not really worrying about getting stuck in a loop because we only need 25 urls
        if local.search_list[0][:8] in ["https://", "http://"] and local.search_list[0] not in url_list:

            # parse out the base of the url
            local.slash_count = 0
            local.url = ""
            for local.i in local.search_list[0]:
                if local.slash_count < 3:
                    local.url = local.url + local.i
                    if local.i == "/":
                        local.slash_count += 1

            # read the robots.txt file to check that we can crawl on the webpage
            local.parser = robotparser.RobotFileParser()
            local.parser.set_url(parse.urljoin(local.url, 'robots.txt'))
            try:
                local.parser.read()
            except:
                print()
            else:
                # get the text if permitted
                if local.parser.can_fetch('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',local.search_list[0]):

                    # opens the page and reads the data
                    with request.urlopen(local.search_list[0]) as f:
                        try:
                            local.raw = f.read().decode('utf8')
                        except:
                            print()
                        else:

                            # checks if the current url will be added to the knowledge base
                            if len(url_list) < 21 or local.url not in baseurls:
                                # the first 20 urls can be from the original website
                                # the last five should be from at least one other website so we can see that we're crawling to new sites

                                # get the text from within main tags
                                local.soup = BeautifulSoup(local.raw)
                                if local.soup.find('main'):
                                    local.text = local.soup.find('main').get_text()
                                else:
                                    local.text = local.soup.get_text()

                                # gets all of the links to more webpages
                                for local.link in local.soup.find_all('a'):
                                    local.ref = local.link.get('href')
                                    if local.ref != None:
                                        # checks that it's not already in the search list so we don't duplicate a bunch of work
                                        if local.ref not in local.search_list:

                                            # checks that the link doesn't go to a social media or a login page
                                            local.bad_link = False
                                            for local.d in donotvisit:
                                                if local.d in local.ref:
                                                    local.bad_link = True
                                            
                                            # adds the link to the search list if it looks useful
                                            if local.bad_link == False:
                                                local.search_list.append(local.ref)
                                
                                # check the length of the text
                                # add the text to the text list and the url to the url list if it looks like it's an actual informational page
                                if len(local.text) > 350:
                                    text_list.append(local.text)
                                    url_list.append(local.search_list[0])
                                    print(starter, local.search_list[0])

        # pops the url that was just visited off the search list
        local.search_list.pop(0)

def pickle_text():
    # loops through the URL text off each page and pickles it
    for i in range(len(text_list)):
        filename = "file" + str(i) + ".pickle"
        with open(filename, 'wb') as f:
            pickle.dump(text_list[i], f)

def file_cleanup():
    # cleans text from pickle files and gets tf
    tf_dicts = []
    idf_dict = {}
    vocab = []
    for i in range(len(text_list)):
        filename = "file" + str(i) + ".pickle"
        with open(filename, 'rb') as f:
            raw_text = pickle.load(f)
            raw_text = raw_text.replace('\n', ' ')
            tokens = nltk.tokenize.word_tokenize(raw_text)
            tokens = [t.lower() for t in tokens if t.isalpha() and t not in nltk.corpus.stopwords.words('english')]
            lemmatizer = nltk.stem.WordNetLemmatizer()
            lemmas = [lemmatizer.lemmatize(t) for t in tokens]
            tf_dict = {}
            idf_list = []
            for lemma in lemmas:
                if lemma in tf_dict:
                    tf_dict[lemma] += 1
                else:
                    tf_dict[lemma] = 1
                if lemma not in vocab:
                    vocab.append(lemma)
                if lemma not in idf_list:
                    idf_list.append(lemma)
            for tf in tf_dict.keys():
                tf_dict[tf] = tf_dict[tf] / len(lemmas)
            tf_dicts.append(tf_dict)
            for idf in idf_list:
                if idf in idf_dict:
                    idf_dict[idf] += 1
                else:
                    idf_dict[idf] = 1
            for idf in idf_dict.keys():
                idf_dict[idf] = math.log(25/idf_dict[idf])
    return tf_dicts, idf_dict

def get_important_terms(tf_dicts, idf_dict):
    # identify the words with the highest tf-idf across all documents
    top_words = []
    for tf_dict in tf_dicts:
        for tf in tf_dict.keys():
            tf_dict[tf] = tf_dict[tf] * idf_dict[tf]
        top = sorted(tf_dict.items(), key=lambda x:x[1], reverse=True)[:40]
        for t in top:
            top_words.append(t)
    top_result = sorted(top_words, key=lambda x:x[1], reverse=True)[:200]
    return top_result

t1 = threading.Thread(target=web_crawl, name='t1', args=(URL1,))
t2 = threading.Thread(target=web_crawl, name='t2', args=(URL2,))
t3 = threading.Thread(target=web_crawl, name='t3', args=(URL3,))
t1.start()
t2.start()
t3.start()
t1.join()
t2.join()
t3.join()

pickle_text()
tf_dicts, idf_dict = file_cleanup()
top_result= get_important_terms(tf_dicts, idf_dict)
topwords = []
for t in top_result:
    if t[0] not in topwords:
        topwords.append(t[0])
top_forty = topwords[:40]
topstring = ''
for t in range(40):
    topstring = topstring + ' ' + top_forty[t]

# output most common words to a file
f = open("topwords.txt","w")
f.write(topstring)
f.close()
# afterward I manually create a modifiedtopwords.txt to limit this list to the top 10-15 terms that I believe are most important