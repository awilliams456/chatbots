import nltk
import pickle
from nltk.corpus import wordnet as wn
from nltk.util import ngrams
from bs4 import BeautifulSoup

# read in the top words
with open('modifiedtopwords.txt', 'r') as f:
    top = f.read()
    top_words = nltk.word_tokenize(top)

# get most likely synset for each top word
top_synsets = {}
for word in top_words:
    lesk_string = "carnivorous plant " + word
    top_synsets[word] = nltk.wsd.lesk(lesk_string, word, 'n')


# creates xml
with open('kb.xml', 'r') as f:
    data = f.read()
Bs_data = BeautifulSoup(data, "xml")
root = Bs_data.new_tag('kb')
Bs_data.append(root)
for ts in top_synsets:
    element = Bs_data.new_tag(ts)
    # this is so cursed, but if you compare a synset to None, it throws an exception, and if you compare None to None, it does not satisfy the !=
    # so this is the only way I can figure out to limit a section of code to correctly returned 
    try:
        if top_synsets[ts] != None:
            print('somehow reached this??')
    except:
        element["synset"] = top_synsets[ts].name()
    root.append(element)

#words to avoid
bad_words = ['PayPal', 'MasterCard', 'Visa' 'Terms and Conditions','Instagram','Youtube','Facebook','Privacy Policy','in stock', 'Contact Us','Categories','Gift Certificates','browser','30-Day Guarantee','Shipping','shipping','Blog','Services','Eagle Creek','Email','Footer','Header', 'JavaScript', '$', 'cart', 'Cart','Newsletter','Order','Orders','order','Orders','email','blog', 'javascript','mistake','button', 'stock', 'Download','video','Interactive','image','gallery','Gallery','Shop','Price', 'cookies', 'Calendar', 'Gallon','Filter','Sign in','subscribe','newsletter','Subscriibe','sign in','gallon','shop','Shop','Read More','Checkout','Click','click', 'PO Box', 'California Carnivores', 'calculator','Calculator','Select options','Close to View Results','View Guide','Sale','sale', 'Out of Stock', 'Collections', 'Sort']

# read in the text and categorize the sentences according to their nouns, verbs, and most similar top word
for i in range(25):

    # read in the pickle file
    filename = "file" + str(i) + ".pickle"
    with open(filename, 'rb') as f:
        raw_text = pickle.load(f)
        raw_text = raw_text.replace('\n', ' ')
        tokens = nltk.tokenize.sent_tokenize(raw_text)

        # categorize each sentence
        previous_topic = ''
        for token in tokens:
            bad_data = False
            for b in bad_words:
                if b in token:
                    bad_data = True
            if not bad_data:
                # replacing unclear pronouns with the last topic identified
                token = token.replace('they', previous_topic)
                token = token.replace('their', previous_topic + "'s")
                token = token.replace('them', previous_topic)
                words = nltk.word_tokenize(token.lower())
                tags = nltk.pos_tag(words)
                wn_tags = []
            
                # convert to wordnet tags and take the nouns and verbs
                for t in tags:
                    if t[1][0] == 'N':
                        wn_tags.append((t[0],'n'))
                    elif t[1][0] == 'V':
                        wn_tags.append((t[0], 'v'))

                # get the most similar top word
                most_similar = ''
                similarity = 0

                for t in top_words:
                    if t in words:
                        most_similar = t
                        similarity = 1
                    else:
                        synsets = wn.synsets(t)
                        for w in wn_tags:
                            wl = nltk.wsd.lesk(words, w[0], w[1])
                            try:
                                if wl != None:
                                    print('somehow reached this???')
                            except:
                                # I realize this is incredibly cursed but it works and now I know that lesk returned something
                                # gets the top word with the highest wup similarity
                                for synset in synsets:
                                    w_sim = wn.wup_similarity(wl, synset)
                                    if w_sim > similarity:
                                        similarity = w_sim
                                        most_similar = t
                # add sentence to the xml
                if most_similar != '':
                    element = root.find(most_similar)
                    subelement = Bs_data.new_tag('s')
                    subelement.string = token
                    element.append(subelement)
                    previous_topic = most_similar

# write xml to file
with open ('kb.xml', 'w') as f:
    f.write(Bs_data.prettify())