"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のPDFに更新があるか確認します."""
import sys
import json
import shutil


def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 3:
        print("Usage #python %s [最新用のフォルダパス] [本日のdownloadフォルダのパス]" % argvs[0])
        exit()
    latest_folder = argvs[1]
    today_folder = argvs[2]

    with open('{}/info.json'.format(latest_folder), mode='r', encoding='utf8') as fp:
        latest_info = json.load(fp)
    with open('{}/info.json'.format(today_folder), mode='r', encoding='utf8') as fp:
        today_info = json.load(fp)

    diff_list = {
        'latest_download_time' : latest_info['download_time'],
        'today_download_time' : today_info['download_time'],
        'list' : [],
    }
    latest_info['download_time'] = today_info['download_time']
    for today_item in today_info["list"]:
        has_diff = False
        latest_item = None
        for latest_item in latest_info["list"]:
            if latest_item['name'] == today_item['name'] and latest_item['url'] != today_item['url']:
                has_diff = True
                latest_item = latest_item
                break
        if has_diff:
            print('更新の発生....', today_item['name'])
            diff_list['list'].append({
                'name' : latest_item['name'],
                'local' : latest_item['local'],
                'url' : latest_item['url'],
            })
            shutil.copy(today_item['local'], latest_item['local'])
            latest_item['url'] = today_item['url']


    with open('{}/info.json'.format(latest_folder), mode='w', encoding='utf8') as fp:
        json.dump(latest_info, fp, sort_keys=True, indent=4, ensure_ascii=False)

    with open('{}/diff_info.json'.format(latest_folder), mode='w', encoding='utf8') as fp:
        json.dump(diff_list, fp, sort_keys=True, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    main(sys.argv)
