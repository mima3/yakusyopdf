"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のPDFの解析結果に地図座標を付与します"""
import sys
import json


def call_geocoder(address, appid):
    params = {
        'appid': appid, 
        'query': address,
        'output': 'json',
        'recursive' : 'true' # trueを指定すると、指定した住所レベルでマッチしなかった場合、上位のレベルで再検索を行います。
    }
    res = requests.get('https://map.yahooapis.jp/geocode/V1/geoCoder', params=params)
    if res.status_code != 200:
        print('geoCoderの呼び出しに失敗しました. status:{} address:{}'.format(res.status_code, address))
        return {}
    json_data = json.loads(res.text)
    if not 'Feature' in json_data:
        print('geoCoderの結果にFeatureが存在しません. address:{} response:{}'.format(address, res.text))
        return {}
    if not json_data['Feature']:
        print('geoCoderの結果にFeatureが存在しません. address:{} response:{}'.format(address, res.text))
        return {}
    res = []
    for feature in json_data['Feature']:
        if not 'Geometry' in feature:
            print('geoCoderの結果にGeometryが存在しません. address:{} response:{}'.format(address, res.text))
            return {}
        if not 'Coordinates' in feature['Geometry']:
            print('geoCoderの結果にCoordinatesが存在しません. address:{} response:{}'.format(address, res.text))
            return {}
        lnglat = feature['Geometry']['Coordinates'].split(',')
        res.append({
             'lat' : lnglat[1],
             'lng' : lnglat[0],
        })
    return res

def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 3:
        print("Usage #python %s [古いJSON] [新しいJSON]" % argvs[0])
        exit()
    src_path = argvs[1]
    dst_path = argvs[2]
    with open(src_path, mode='r', encoding='utf8') as fp:
        src_address_dict = json.load(fp)

    with open(dst_path, mode='r', encoding='utf8') as fp:
        dst_address_dict = json.load(fp)
    
    for address in dst_address_dict:
        if 'coordinates' in dst_address_dict[address]:
            # 地図情報がすでに存在する場合
            continue
        if not address in src_address_dict:
            continue
        if not 'coordinates' in src_address_dict[address]:
            continue
        dst_address_dict[address]['coordinates'] = src_address_dict[address]['coordinates']
    
    with open(dst_path, mode='w', encoding='utf8') as fp:
        json.dump(dst_address_dict, fp, sort_keys=True, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    main(sys.argv)
