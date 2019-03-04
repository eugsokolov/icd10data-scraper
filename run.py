from main import app
from scraper import load, get

@app.route('/load', methods=['POST'])
def setter():
    final = load()
    if not final:
        abort(404)
    return final

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

