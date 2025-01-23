# based on github scikit examples
import pandas as pd
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB

# read in questions.csv
data = pd.read_csv('questions.csv',header=0,encoding='latin-1')

# remove stopwords, punctuation, etc
# based on github tensorflow examples
data['Question'].replace('[\d][\d]+', ' num ', regex=True, inplace=True)
data['Question'].replace('[!@#*][!@#*]+', ' punct ', regex=True, inplace=True)
stopwords = set(stopwords.words('english'))
# the stop words are actually removed in the vectorizer step

x=data.Question
y=data.Category

# split the data
# added a random state for consistent shuffling
xtrain, xtest, ytrain, ytest = train_test_split(x,y, test_size=0.2, train_size=0.8, random_state=1234, shuffle=True, stratify=data['Category'])

# create the vectorizer
vectorizer = TfidfVectorizer(decode_error='replace', lowercase=True, stop_words=stopwords, max_df=0.8, ngram_range=(1,3))
# ngram range chosen based on https://dylancastillo.co/text-classification-using-python-and-scikit-learn/#train-and-evaluate-the-model

# create the naive bayes classifier
# I have not changed any of the defaults for the multinomial naive bayes because I don't believe any changes would improve performance on this task
question_model = Pipeline([('tfidf',vectorizer),('multinb',MultinomialNB())])
question_model.fit(xtrain, ytrain)