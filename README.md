# icd10data-scraper

Load ICD codes and find appopriate synonyms for a code
data can be found at: http://icd10data.com/

Requirements:
This web app scrapes icd10data and lazily stores codes and appropriate synonyms in a local mongo db

You must run:
```
 $ pip install -r requirements.txt
```

Usage:
Run the app:
```
 $ python run.py
```

Get a code's synonyms:
```
 $ curl http://localhost:8080/code/<code>
```

Given a list of codes in codes.txt:
```
 $ for i in `cat codes.txt`; do curl http://localhost:8080/code/$i ; done
```

(WIP) Load codes into a database - optional, but will prepopulate all codes:
```
 $ curl -X POST http://localhost:8080/load
 ```
