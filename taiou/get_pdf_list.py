"""各日付の各都道府県の検査陽性者の状況のPDFを取得する."""
import json
import datetime
import os
import csv
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import camelot

def pdf_to_csv(url, csv_path):
    # 確認中の列だけ離れているため別のテーブルとして取得されてしまう.そのため小細工をしている
    tables = camelot.read_pdf(url)
    if len(tables) != 2:
        print('予期せぬテーブル数が取得されました',url, tables)
        raise
    if len(tables[0].df.index) != 51 or len(tables[1].df.index) != 50:
        print('予期せぬ行数が取得されました',url, len(tables[0].df.index), len(tables[1].df.index))
        raise
    ix2 = 0
    with open(csv_path, 'w', encoding='utf16', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        for ix in range(len(tables[0].df.index)):
            rec = []
            for col in range(len(tables[0].df.columns)):
                rec.append(tables[0].df.loc[ix][col])
            if ix != 1:
                rec.append(tables[1].df.loc[ix2][0])
                ix2 += 1
            writer.writerow(rec)


def html_table_to_csv(soup, title, csv_path):
    tables = soup.select('table')
    for table in tables:
        if not title in table.text:
            continue
        # 対象のテーブルを発見した
        with open(csv_path, 'w', encoding='utf16', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            records = table.select('tr')
            for record in records:
                rec = []
                columns = record.select('td')
                for column in columns:
                    rec.append(column.text)
                writer.writerow(rec)
            return True
    return False

def get_history_link(url):
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    result = get_links(url, '新型コロナウイルス感染症の現在の状況と厚生労働省の対応について', soup)
    for link in result:
        if not '令和' in link['title']:
            # 日付が含まれていない場合は次の兄弟要素のテキストも取得する
            link['title'] = link['title'] + str(link['elem'].next_sibling)
    return result

def get_links(url, title, soup):
    result = []
    elem_links = soup.select('a')
    for link in elem_links:
        if title in link.text:
            result.append({
                'url':link.attrs['href'],
                'title': link.text,
                'elem' : link
            })
    return result

def main():
    """メイン処理"""
    # 「新型コロナウイルス感染症に関する報道発表資料（発生状況、国内の患者発生、海外の状況、その他）」
    # からリンクを取得
    target_url = 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000121431_00086.html'
    url_parsed = urlparse(target_url)
    base_url = url_parsed.scheme + "://" + url_parsed.netloc
    
    reports = get_history_link(target_url)
    for report in reports:
        print(report['title'])
        res = requests.get(report['url'])
        res.encoding = res.apparent_encoding
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        csv_path = report['title'] + ".csv"
        if html_table_to_csv(soup, '都道府県', csv_path):
            print('\tHTMLに中にテーブルを見つけました')
            continue
        statues = get_links(report['url'], '各都道府県の検査陽性者の状況', soup)
        if statues:
            print('\tHTMLに中に各都道府県の検査陽性者の状況のPDFを見つけました',base_url + statues[0]['url'])
            # PDF中の表を取る
            pdf_to_csv(base_url + statues[0]['url'], csv_path)

    #with open('{}/info.json'.format(dst_folder), mode='w', encoding='utf8') as fp:
    #    json.dump(result, fp, sort_keys=True, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
