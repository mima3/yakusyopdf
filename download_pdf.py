import requests
import json
import datetime
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def download(url, local_path):
    r = requests.get(url)
    r.raise_for_status()
    local_path = '{}/{}.pdf'.format(dst_folder,name)
    with open(local_path, mode='wb') as fp:
        fp.write(r.content)

dst_folder = os.getcwd() + datetime.datetime.now().strftime("/%Y%m%d%H%M%S")
if not os.path.exists(dst_folder):
    os.mkdir(dst_folder)

url = 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/rinsyo/index_00014.html'
url_parsed = urlparse(url)
base_url = url_parsed.scheme + "://" + url_parsed.netloc
r = requests.get(url)
r.encoding = r.apparent_encoding 
print(r.status_code, r.reason, r.encoding)
r.raise_for_status()
soup = BeautifulSoup(r.text, 'html.parser')
elem_ul = soup.select_one("[class='m-listLink--hCol2']")
elem_links = elem_ul.select('a')

result = {
    "download_time" : str(datetime.datetime.now()),
    "list" : []
}
for link in elem_links:
    name = link.text
    url = base_url + link.attrs['href']
    print(name, url)
    local_path = '{}/{}.pdf'.format(dst_folder,name)
    download(url, local_path)
    result["list"].append({
        "name" : name,
        "url" : url,
        "local" : local_path
    })

with open( '{}/info.json'.format(dst_folder), mode='w', encoding='utf8') as fp:
    json.dump(result, fp, sort_keys = True, indent = 4, ensure_ascii=False)

print("created {}".format(dst_folder))
