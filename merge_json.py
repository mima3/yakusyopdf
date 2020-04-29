"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のPDFの解析結果のJSONを結合します."""
import sys
import re
import json
import requests


def filter_data(name, path, result):
    """住所をキーとするデータを構築する."""
    with open(path, mode='r', encoding='utf8') as fp:
        json_data = json.load(fp)

    for rec in json_data:
        if not rec['address']:
            print("W\t住所が存在しないためスキップします file:{} name:{} page:{}".format(name, rec['name'], rec['page']))
            continue
        # 滋賀県などはスペースが混在している
        address = rec['address'].replace(' ', '')

        if address.find(name) != 0:
            #print("I\t住所が都道府県名から始まらないため住所に追加します  file:{} page:{} address:{}".format(name, rec['page'], address))
            address = name + address
        if not rec['name']:
            print("W\t名前が存在しないため名称にtodoを埋め込みます.手で修正してください. file:{} page:{}".format(name, rec['page']))
            rec['name'] = 'todo'
        data = {
           'name' : rec['name'],
           'postal_code' : rec['postal_code'],
           'tel' : rec['tel'],
           'first' : rec['name'],
           'revist': rec['revisit'],
           'department' : rec['department'],
           'doctor' : rec['doctor'],
           'cooperation' : rec['cooperation']
        }
        if not address in result:
            result[address] = {"items" : []}
        result[address]['items'].append(data)
    return result


def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 2:
        print("Usage #python %s [downloadフォルダのパス]" % argvs[0])
        exit()
    dst_folder = argvs[1]

    with open('{}/info.json'.format(dst_folder), mode='r', encoding='utf8') as fp:
        pdf_info = json.load(fp)

    result = {}
    for data in pdf_info["list"]:
        json_path = '{}/{}.json'.format(dst_folder, data['name'])
        filter_data(data['name'], json_path, result)

    path = '{}/all_data.json'.format(dst_folder)
    with open(path, mode='w', encoding='utf8') as fp:
        json.dump(result, fp, sort_keys=True, indent=4, ensure_ascii=False)
    print('出力先:' + path)

if __name__ == '__main__':
    main(sys.argv)
