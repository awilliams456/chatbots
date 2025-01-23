# identify the plant in question
# use multinomialNB to pick the question category

#imports and defining the word net lemmatizer object
import nltk
from nltk.util import ngrams
from bs4 import BeautifulSoup
from nltk.corpus import wordnet as wn
import random
import numpy as np
from numpy.linalg import norm
lemmatizer = nltk.stem.WordNetLemmatizer()

import pandas as pd

# read in the csv
data = pd.read_csv('plantInfo-clean.csv', header = 0, encoding='latin-1')

Bs_data = BeautifulSoup(data, "xml")
root = Bs_data.find('kb')

# create xml base for user file
with open('users.xml', 'r') as x:
    udata = x.read()

user_data = BeautifulSoup(udata, "xml")
uroot = user_data.find('users')

def get_main_topic(token, previous_topic):
    # parse the user input to identify the main arguments
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
            syn = root.find(t)
            if syn.has_attr("synset"):
                for w in wn_tags:
                    wl = nltk.wsd.lesk(words, w[0], w[1])
                    try:
                        if wl != None:
                            print('somehow reached this???')
                    except:
                        # I realize this is incredibly cursed but it works and now I know that lesk returned something
                        # gets the top word with the highest wup similarity
                        if syn.get("synset") != None:
                            w_sim = wn.wup_similarity(wl, wn.synset(syn.get("synset")))
                            if w_sim > similarity:
                                similarity = w_sim
                                most_similar = t

    if similarity < 0.5 and previous_topic != '':
        most_similar = previous_topic
    return most_similar


def get_response(topic, token):
    if user.find('s'):
        last_sentence = user.find('s')
    else:
        last_sentence = ''

    # get sentences
    stags = root.find(topic).find_all('s')
    sentences = []
    for stag in stags:
        sentences.append(stag.get_text())

    # get likes
    ltags = root.find(topic).find_all('l')
    likes = []
    for ltag in ltags:
        likes.append(ltag.get_text())
    likes = [lemmatizer.lemmatize(l) for l in likes]

    # get dislikes
    dtags = root.find(topic).find_all('d')
    dislikes = []
    for dtag in dtags:
        dislikes.append(dtag.get_text())
    dislikes = [lemmatizer.lemmatize(d) for d in dislikes]

    #get input matrix
    lower = token.lower()
    t_vocab = nltk.word_tokenize(lower)
    t_lemmas = [lemmatizer.lemmatize(word) for word in t_vocab]
    t_matrix = []
    all_lemmas = []
    for lemma in t_lemmas:
        if lemma not in all_lemmas:
            all_lemmas.append(lemma)
            t_matrix.append(1)
        else:
            t_matrix[all_lemmas.index(lemma)] += 1
    
    #get most similar sentence
    max_similarity = 0
    most_similar = ''

    #get matrix for each sentence and calculate cosine similarity
    for sentence in sentences:
        if sentence not in last_sentence:
            kb_lower = sentence.lower()
            kb_vocab = nltk.word_tokenize(kb_lower)
            kb_lemmas = [lemmatizer.lemmatize(word) for word in kb_vocab]
            kb_matrix = [0 for m in t_matrix]
            for lemma in kb_lemmas:
                if lemma not in all_lemmas:
                    all_lemmas.append(lemma)
                    occurrences = 1
                    if lemma in likes:
                        occurrences += 1
                    if lemma in dislikes:
                        occurrences -=1
                    kb_matrix.append(occurrences)
                    t_matrix.append(0)
                else:
                    kb_matrix[all_lemmas.index(lemma)] += 1

            ia = np.array(t_matrix)
            ka = np.array(kb_matrix)
            cosine = np.dot(ia, ka)/(norm(ia)*norm(ka))
            if cosine > max_similarity:
                max_similarity = cosine
                most_similar = sentence
    
    # determine whether to use the sentence or a random output
    if max_similarity < 0.01:
        count = random.randrange(0, len(rand_sentences))
        response = rand_sentences[count]
    else:
        response = most_similar
    
    #set the last sentence to the response
    if user.find('s'):
        user.find('s').string = response
    else:
        stag = user_data.new_tag('s')
        stag.string = response
        user.append(stag)

    return response

# Start the introductions
print("Hi, I'm a chatbot that knows about kitchen gardening. What's your name? I'd like to make a profile for you so I can remember our conversations.")
username = ''

while username == '':
    name = input()
    tokens = nltk.word_tokenize(name)
    if len(tokens) < 3:
        username = name
    elif len(tokens) == 3:
        username = tokens[2]
    elif len(tokens) >= 4:
        ngrams = list(ngrams(tokens, 4))
        for n in ngrams:
            if (n[0] == 'My' or n[0] == 'my') and n[1] == 'name' and n[2] == 'is':
                username = n[3]
            elif (n[0] == 'It' or n[0] == 'it') and n[1] == 'is':
                username = n[2]
            elif (n[0] == "It" or n[0] == "it") and n[1] == "'s":
                username = n[2]
    else:
        print("Please enter a name for me to use.")


# either adds a new user or finds the existing user
if user_data.find(username):
    user = user_data.find(username)
else:
    user = user_data.new_tag(username)
    uroot.append(user)

print('Hi',username,"! What would you like to talk about today? You can end our conversation at any time by telling me \"Goodbye\"")
usertext = input()
previous_topic = ''
while usertext != "Goodbye" and usertext != "goodbye":
    # decision tree for continuing the conversation
    if usertext == '':
        print("I see that you didn't say anything. Please tell me \"Goodbye\" if you'd like to end our conversation!")
    elif " like " in usertext:
        words = nltk.word_tokenize(usertext)
        like = user_data.new_tag('l')
        like.string = words[words.index('like') + 1]
        user.append(like)
        print("I see, you like " + like.get_text() + ". I'll talk more about that in the future.")
    elif " dislike " in usertext:
        words = nltk.word_tokenize(usertext)
        dislike = user_data.new_tag('d')
        dislike.string = words[words.index('dislike') + 1]
        user.append(dislike)
        print("I see, you dislike " + dislike.get_text() + ". I'll talk less about that in the future.")
    else:
        previous_topic = get_main_topic(usertext, previous_topic)
        print(get_response(previous_topic, usertext))
    usertext = input()

print("It was good to talk to you! I'll save the details of our conversation so that we can continue later. Goodbye!")
file = open("users.xml","w")
file.write(user_data.prettify())
file.close()