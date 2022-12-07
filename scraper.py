from bs4 import BeautifulSoup
import requests
from pprint import pprint

geno_par = {
    "DWG": "https://www.dwg-online.de/angebote/aktuelle-wohnungsangebote",
    "BWB": "https://www.bwb-eg.de/wohnungssuche"
}

def html_text(url):
    try: 
        html = requests.get(url)
        print(html)
    except:
        print(f'Cant get url for {geno_name}')

    return html.text



# def dwg_scraper():    
#     soup = BeautifulSoup(html_text(geno_par['DWG']), 'html.parser')

#     # Find all attributes we need
#     list_item = soup.find_all("div", {"class": "immobilie-list-item"})
#     list_image = [x.find_all('a')[0] for x in list_item]
#     url_partial = [x.attrs['href'] for x in list_image]

#     # Attach on each url the root-url
#     url = ['https://www.dwg-online.de'+x for x in url_partial]

#     return url

# Find out how many result pages we have
soup = BeautifulSoup(html_text(geno_par['BWB']), 'html.parser')
pagination = soup.find("nav", {"class": "pagination"})
page_count = len(pagination.find_all('a')) + 1 # +1 because active page is not scraped

html_text_appended = ''
for n in range(1, page_count+1, 1):
    html_text_appended += html_text(geno_par["BWB"]+f'/page/{n}')

soup = BeautifulSoup(html_text_appended, 'html.parser')

print('end')