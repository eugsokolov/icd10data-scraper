'''
Load ICD codes and find appopriate synonyms for a code
source: www.icd10data.com

Requirements:
This web app scrapes icd10data and lazily stores codes and appropriate synonyms in a local mongo db

You must run:
 $ pip install -r requirements.txt

Usage:
Run the app:
 $ python run.py

Get a code's synonyms:
 $ curl http://localhost:8080/code/<code>

Given a list of codes in codes.txt,
 $ for i in `cat codes.txt`; do curl http://localhost:8080/code/$i ; done

(WIP) Load codes into a database - optional, but will prepopulate all codes:
 $ curl -X POST http://localhost:8080/load

'''
from main import app
from icdscraper import loadCodes, get

@app.route('/load', methods=['POST'])
def setter():
    final= loadCodes()
    if not final:
        abort(404)
    return 'successfully loaded {} codes\n'.format(len(final))

@app.route('/code/<code>')
def getter(code):
    synonyms = get(code)
    if not synonyms:
        msg = 'no synonyms'
    else:
        msg = '{} synonyms: {}'.format(len(synonyms), synonyms)
    return 'for code {!r} found {}\n'.format(code, msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

