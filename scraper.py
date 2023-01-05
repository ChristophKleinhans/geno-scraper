from bs4 import BeautifulSoup
import boto3
import requests
import pprint
from datetime import datetime, timedelta
import json
import logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

geno_par = {
    "DWG": "https://www.dwg-online.de/angebote/aktuelle-wohnungsangebote",
    "BWB": "https://www.bwb-eg.de/wohnungssuche",
    "WOGEDO": "https://www.wogedo.de/wohnen/aktuelle-angebote/",
    "SWD": "https://www.swd-duesseldorf.de/service/wohnungsangebot/wohnungssuche/wohnungssuche.html?FORM_SUBMIT=&regionid=0&rooms=0&area=0&flatfilter_submit=Suchen"
}

def html_text(url):
    try: 
        html = requests.get(url)
    except:
        logging.warning(f'Cant get url for {geno_name}')

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

def s3_client():
    s3 = boto3.client('s3')
    return s3

def s3_upload(s3, bucket, key, body):
    body = str(body).encode('utf-8')
    s3.put_object(Bucket=bucket, Key=key, Body=body)


if __name__ == '__main__':

    geno_scraper = {
        "DWG": dwg_scraper,
        "BWB": bwb_scraper,
        "WOGEDO": wogedo_scaper,
        "SWD": swd_scraper

    }
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.today().strftime('%Y-%m-%d')
    s3 = s3_client()

    # Get all data from yesterday
    try:
        last_timestamp_data = {
            "DWG": s3.get_object(Bucket='geno-scraper-s3', Key=f'{yesterday}/DWG.txt')['Body'].read().decode('utf-8'),
            "BWB": s3.get_object(Bucket='geno-scraper-s3', Key=f'{yesterday}/BWB.txt')['Body'].read().decode('utf-8'),
            "WOGEDO": s3.get_object(Bucket='geno-scraper-s3', Key=f'{yesterday}/WOGEDO.txt')['Body'].read().decode('utf-8'),
            "SWD": s3.get_object(Bucket='geno-scraper-s3', Key=f'{yesterday}/SWD.txt')['Body'].read().decode('utf-8')
        }
    except:
        logging.warning('loading yesterday data failed')

    # Add all new entries to the list
    new_entries = []
    
    # TODO: Having multiple scrapings each day
    # Scraping each geno and uploading to s3
    for geno_name, geno_url in geno_par.items():
        try:
            logging.info(f'Scraping {geno_name}...')
            body = geno_scraper[geno_name]()
            try:
                new_entries.append(list(set(body) - set(json.loads(last_timestamp_data[geno_name].replace("'", '"')))))
            except:
                logging.warning('No data to compare with from yesterday')
            s3_upload(s3, 'geno-scraper-s3', f'{today}/{geno_name}.txt', body)
        except:
            logging.warning(f'Error scraping {geno_name}')

    # publish data to sns per email
    result_list = sum(new_entries, [])
    message = f"Am {today} wurden folgende {len(result_list)} Einträge gefunden:\n {pprint.pformat(result_list)} "

    sns = boto3.client('sns')
    response = sns.publish(TopicArn='arn:aws:sns:eu-central-1:058970924506:geno-scraper-sns', Message=message, Subject=f'Genossenschaft Scraping am {today}')

    logging.info('the following message was published to SNS: \n' + message )

    logging.info('finished scraping')

