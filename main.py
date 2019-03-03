from flask import Flask, abort
from flask_mongoalchemy import MongoAlchemy

app = Flask(__name__)
#app.config['DEBUG'] = True
app.config['MONGOALCHEMY_DATABASE'] = 'icdcodes'
db = MongoAlchemy(app)

class ICDCode(db.Document):
    '''
    Represents an ICD Code
      code: [A-Z][0-9]{2}.[0-9] code
      synonyms: list of appropriate synonyms
    '''
    code = db.StringField(max_length=10)
    synonyms = db.ListField(db.StringField(max_length=256))

class RangedSite(db.Document):
    '''
    Represents a range where an ICD code may be
      site: the url of the site
      start: starting ICDCode
      end: ending ICDcode
    '''
    site = db.StringField(max_length=64)
    start = db.StringField(max_length=3)
    end = db.StringField(max_length=3)

