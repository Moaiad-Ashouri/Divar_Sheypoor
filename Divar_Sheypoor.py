from bs4 import BeautifulSoup
import requests
from six.moves.urllib import parse
import sqlite3
from datetime import datetime
import time
import http.cookiejar as cookielib
import mechanize


### You can find how to create a Discord Webhook in the following link:
### https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
Discord_Webhook = ""


### After adding your filters in Divar and Sheypoor websites copy the url and paste it bellow
Divar_URL = ""
Sheypoor_URL = ""

### SQLite Database Function
def add_result_to_database(url):
    try:
        sqliteConnection = sqlite3.connect('SQLiteDB.db')
        cursor = sqliteConnection.cursor()
        cursor.execute("""SELECT result_url FROM Results WHERE result_url=? """,(url,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO Results (result_url) VALUES (?)",(url,))
            send_url_to_discord(url)
            print(url)
            sqliteConnection.commit()
    except sqlite3.Error as error:
        data = {"content": error}
        response = requests.post(Discord_Webhook, json=data)
        print("Error while connecting to sqlite", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()


### Discord Send Url Function
def send_url_to_discord(url):
    if Discord_Webhook:
        now = datetime.now()
        result_url = {"content": url}
        dash_spacing = {"content": f"------------{now}"}
        response = requests.post(Discord_Webhook, json=result_url)
        time.sleep(2)
        response = requests.post(Discord_Webhook, json=dash_spacing)
        time.sleep(2)


QUEUE = []
def parse_list_page(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    links = soup.select('link[rel="next"]')
    if links:
        next_link = links[0].attrs['href']
        next_link = next_link
        QUEUE.append(
            (parse_list_page, next_link)
        )
    if not soup.select('link[rel="prev"]'):
        url = Divar_URL
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")
    links = soup.select('div.browse-post-list section.post-card-item a')
    for link in links:
        product_url = link.attrs['href']
        result = parse.urlparse(url)
        base_url = parse.urlunparse(
            (result.scheme, result.netloc, "", "", "", "")
        )
        product_url = parse.urljoin(base_url, product_url)
        QUEUE.append(
            (parse_detail_page, product_url)
            )


def parse_detail_page(url):
    add_result_to_database(url)


def Sheypoor():
    if Sheypoor_URL:
        cj = cookielib.CookieJar()
        br = mechanize.Browser()
        br.set_cookiejar(cj)
        class_name = "list"
        br.open(Sheypoor_URL)
        html_bytes = br.response().read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('article')
        for link in links:
            if link.get('class') != None:
                if class_name in link.get('class'):
                    url = link.get('data-href')
                    add_result_to_database(url)


def Divar():
    if Divar_URL:
        QUEUE.append(
            (parse_list_page, Divar_URL)
        )
        while len(QUEUE):
            call_back, url = QUEUE.pop(0)
            call_back(url)



while True:
    Divar()
    Sheypoor()
    print(datetime.now())
    time.sleep(3600)
