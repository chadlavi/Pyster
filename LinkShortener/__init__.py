from flask import Flask, request, render_template, redirect, send_from_directory
from math import floor
from sqlite3 import OperationalError
import string
import sqlite3
try:
    from urllib.parse import urlparse  # Python 3
    str_encode = str.encode
except ImportError:
    from urlparse import urlparse  # Python 2
    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase
import base64

# Assuming urls.db is in your app root folder
app = Flask(__name__, static_url_path='/static/')

host='http://chdlv.pw/'

def table_check():
    create_table = """
        CREATE TABLE WEB_URL(
        ID INT PRIMARY KEY AUTOINCREMENT,
        URL TEXT NOT NULL
        );
        """
    with sqlite3.connect('/var/www/LinkShortener/LinkShortener/urls.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table)
        except OperationalError:
            pass

def getList():
    get_links = """
        select ID, URL from WEB_URL order by id desc;
        """
    with sqlite3.connect('/var/www/LinkShortener/LinkShortener/urls.db') as conn:
        cursor = conn.cursor()
        try:
            links = cursor.execute(get_links)
            Links = [dict(short=row[0],
                url=row[1]) for row in links]
            for link in Links:
                link['short'] = 'http://chdlv.pw/l/' + toBase62(link['short'])
                link['url'] = base64.urlsafe_b64decode(str(link['url']))
            return Links
        except OperationalError:
            pass

def toBase62(num, b=62):
    if b <= 0 or b > 62:
        return 0
    base = string.digits + ascii_lowercase + ascii_uppercase
    r = num % b
    res = base[r]
    q = floor(num / b)
    while q:
        r = q % b
        q = floor(q / b)
        res = base[int(r)] + res
    return res


def toBase10(num, b=62):
    base = string.digits + ascii_lowercase + ascii_uppercase
    limit = len(num)
    res = 0
    for i in range(limit):
        res = b * res + base.find(num[i])
    return res

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/shorten', methods=['GET', 'POST'])
def shorten():
    if request.method == 'POST':
        original_url = str_encode(request.form.get('url'))
        #print('original_url as input: '+original_url.decode())
        parsed = urlparse(original_url)
        #print(parsed)
        if not parsed.scheme:
            #print('no scheme')
            url = 'http://' + original_url.decode('utf-8')
        else:
            url = original_url.decode('utf-8')
        #print('url = '+url)
        with sqlite3.connect('/var/www/LinkShortener/LinkShortener/urls.db') as conn:
            cursor = conn.cursor()
            res = cursor.execute(
                'INSERT INTO WEB_URL (URL) VALUES (?)',
                [base64.urlsafe_b64encode(url)]
            )
            encoded_string = toBase62(res.lastrowid)
        return render_template('shorten.html', short_url=host + 'l/' +  encoded_string)
    return render_template('shorten.html')

@app.route('/links')
def links():
    if request.method == 'GET':
        get_links = getList()
        #get_links = dict()
        return render_template('links.html', links=get_links)

@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/i/<short_url>')
@app.route('/l/<short_url>')
def redirect_short_url(short_url):
    decoded = toBase10(short_url)
    print('decoded = '+str(decoded))
    url = ''  # fallback if no URL is found
    with sqlite3.connect('/var/www/LinkShortener/LinkShortener/urls.db') as conn:
        cursor = conn.cursor()
        res = cursor.execute('SELECT URL FROM WEB_URL WHERE ID=?', [decoded])
        try:
            short = res.fetchone()
            if short is not None:
                print('short[0] = ' + short[0])
                url = base64.urlsafe_b64decode(short[0].encode(encoding='UTF-8'))
                print('url = '+url)
        except Exception as e:
            print(e)
    print('url = '+url)
    return redirect(url)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('home.html')


if __name__ == '__main__':
    # This code checks whether database table is created or not
    #table_check()
    app.run()
