from bs4 import BeautifulSoup
import requests
from pprint import pprint

geno_par = {
    "DWG": "https://www.dwg-online.de/angebote/aktuelle-wohnungsangebote",
    "BWB": "https://www.bwb-eg.de/wohnungssuche",
    "DUEBS": "https://www.duebs.de/mietangebote",
    "WOGEDO": "https://www.wogedo.de/wohnen/aktuelle-angebote/",
    "SWD": "https://www.swd-duesseldorf.de/service/wohnungsangebot/wohnungssuche/wohnungssuche.html?FORM_SUBMIT=&regionid=0&rooms=0&area=0&flatfilter_submit=Suchen"
}

def html_text(url):
    try: 
        html = requests.get(url)
        print(html)
    except:
        print(f'Cant get url for {geno_name}')

    return html.text



def dwg_scraper():    
    soup = BeautifulSoup(html_text(geno_par['DWG']), 'html.parser')

    # Find all attributes we need
    list_item = soup.find_all("div", {"class": "immobilie-list-item"})
    list_image = [x.find_all('a')[0] for x in list_item]
    url_partial = [x.attrs['href'] for x in list_image]

    # Attach on each url the root-url
    url = ['https://www.dwg-online.de'+x for x in url_partial]

    return url


def bwb_scraper():
    # Find the number of result pages first
    soup = BeautifulSoup(html_text(geno_par['BWB']), 'html.parser')
    pagination = soup.find("nav", {"class": "pagination"})
    page_count = len(pagination.find_all('a')) + 1 # +1 because active page is not scraped

    html_text_appended = ''
    for n in range(1, page_count+1, 1):
        html_text_appended += html_text(geno_par["BWB"]+f'/page/{n}')

    soup = BeautifulSoup(html_text_appended, 'html.parser')
    departements = soup.find_all('div', {'class': 'section-wohnung container'})

    departements_expose = [x.find('a', {'class': 'expose-button'}) for x in departements]
    url = [x.attrs['href'] for x in departements_expose]
    
    return url





def wogedo_scaper():
    soup = BeautifulSoup(html_text(geno_par['WOGEDO']), 'html.parser')
    departements = soup.find_all("article", {"class": "wg-offer-articles__items flat wg-bg--white"})
    url = ["https://www.wogedo.de"+x.find('a', href=True)['href'] for x in departements]

    return url


def swd_scraper():
    soup = BeautifulSoup(html_text(geno_par['SWD']), 'html.parser')
    departements = soup.find_all('div', {'class': ['layout_overview block even', 'layout_overview block first even', 'layout_overview block last even', 
                                                    'layout_overview block odd', 'layout_overview block first odd', 'layout_overview block last odd']})
    url = ["https://www.swd-duesseldorf.de/"+x.find('a', href=True)['href'] for x in departements]

    return url
