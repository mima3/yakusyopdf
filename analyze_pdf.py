"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のページから対応医療機関リストのPDFを解析する."""
import sys
import re
import json
import csv
import copy
import mojimoji
import analyze_pdf_table
import cv2
import numpy as np


CHECK_POSTAL_CODE = r'[0-9]{3}-[0-9]{4}'
CHECK_TEL_CODE = r'0[0-9]{1}-[0-9]{4}-[0-9]{4}|0[0-9]{2}-[0-9]{3}-[0-9]{4}|0[0-9]{3}-[0-9]{2}-[0-9]{4}|0[0-9]{4}-[0-9]{1}-[0-9]{4}'
DEFAULT_RULE = {
    "first_page_offset" : 2,      
    "other_page_offset" : 0,      # 2ページ目にもヘッダがある場合が多いが、頻繁にレイアウト変わるので警告でチェックすることにする
    "char_margin" : 0.25,         # 2つの文字がこのマージンよりも接近している場合、それらは同じ行の一部と見なされます。
    "accuracy" : 90.0,
    "line_scale": 30,             # 大きいほど小さい線を検出するが、大きすぎると文字を線と見なしてしまう。
    "image_proc" : None,
    "columns" : {
        "no" : {
            "index" : 0,
        },
        "name" : {
            "index" : 1,
            "chk_func" : "chk_required",
            "cnv_func" : "conv_oneline"
        },
        "postal_code" : {
            "index" : 2,
            "chk_func" : "chk_postal_code",
            "cnv_func" : "conv_postal_code"
        },
        "address" : {
            "index" : 3,
            "chk_func" : "chk_required",
            "cnv_func" : "conv_oneline"
        },
        "tel": {
            "index" : 4,
            "chk_func" : "chk_required"
        },
        "url": {
            "index" : 5,
            "cnv_func" : "conv_url"
        },
        "first": {
            "index" : 6,
        },
        "revisit": {
            "index" : 7,
        },
        "department": {
            "index" : 8,
        },
        "doctor": {
            "index" : 9,
        },
        "cooperation" : {
            "index" : 10
        }
    }
}


def fix_name(rec, log):
    """nameの修正処理"""
    if rec['no']:
        # 北海道などは名前が長すぎて項番の列と合体してしまっている
        # 改行で区切ってもっとも長いものを名前として決定する
        names = rec['no'].split('\n')
        target_name = names[0]
        no = names[len(names)-1]
        for name in names:
            if len(target_name) < len(name):
                no = target_name
                target_name = name
        if not target_name.isdigit():
            # 名前が項番ではないこと
            rec['name'] = target_name
            log(
                "nameが空のためnoから値を取得しました. no:{}->{}, {}".format(
                    rec['no'],
                    no,
                    rec['name']
                )
            )
            rec['no'] = no
    if rec['postal_code'] and not rec['name']:
        # 郵便番号に混在しているか確認
        # ※郵便番号に表記の揺れがあったらあきらめる
        postal_code = rec['postal_code']
        m = re.search(CHECK_POSTAL_CODE, postal_code)
        if m and analyze_pdf_table.AnalyzePdfTable.conv_postal_code(postal_code) != "":
            rec['name'] = postal_code[0:m.span()[0]]
            rec['postal_code'] = m.group()
            log(
                "nameが空のためpostal_codeから値を取得しました. postal_code:{}->{}, {}".format(
                    postal_code,
                    rec['name'],
                    rec['postal_code']
                )
            )

def fix_postal_code(rec, log):
    """postal_codeの修正処理"""
    if rec['name']:
        # 施設名に混在しているか確認
        # ※郵便番号に表記の揺れがあったらあきらめる
        name = rec['name']
        m = re.search(CHECK_POSTAL_CODE, name)
        if m:
            rec['name'] = name[0:m.span()[0]]
            rec['postal_code'] = name[m.span()[0]:]
            log(
                "postal_codeが空のためnameから値を取得しました. name:{}->{}, {}".format(
                    name,
                    rec['name'],
                    rec['postal_code']
                )
            )

def fix_tel(rec, log):
    """電話番号の修正処理"""
    if rec['url']:
        # urlに混在している場合
        url = rec['url']
        m = re.match(r'[\d-]+', url)
        if m:
            rec['tel'] = m.group()
            rec['url'] = url[m.span()[1]:]
            log("telが空のためurlから値を取得しました. url:{}->{}, {}".format(url, rec['tel'], rec['url']))
    if rec['address']:
        # addressに混在している場合
        # ※電話番号に表記の揺れがあったらあきらめる
        address = rec['address']
        m = re.search(CHECK_TEL_CODE, address)
        if m:
            rec['address'] = address[0:m.span()[0]]
            rec['tel'] = m.group()
            log(
                "telが空のためaddressから値を取得しました. address:{}->{}, {}".format(
                    address,
                    rec['address'],
                    rec['tel']
                )
            )


def fix_address(rec, log):
    if rec['postal_code']:
        # 郵便番号の列にaddressに混在している場合
        # ※郵便番号に表記の揺れがあったらあきらめる
        postal_code = rec['postal_code']
        m = re.search(CHECK_POSTAL_CODE, postal_code)
        if m :
            rec['postal_code'] = m.group()
            rec['address'] = postal_code[m.span()[1]:]
            log(
                "postal_codeが空のためaddressから値を取得しました. postal_code:{}->{}, {}".format(
                    postal_code,
                    rec['postal_code'],
                    rec['address']
                )
            )

    if rec['tel']:
        # 電話番号はある場合
        tel = mojimoji.zen_to_han(rec['tel'])
        m = re.search(CHECK_TEL_CODE, tel)
        if m and m.span()[0] != 0:
            rec['address'] = mojimoji.han_to_zen(tel[0:m.span()[0]])
            rec['tel'] = m.group()
            log(
                "addressが空のためtelから値を取得しました. tel:{}->{}, {}".format(
                    tel,
                    rec['address'],
                    rec['tel']
                )
            )

def fix_record(rec, log):
    """１行ごとにデータが上手く取得できなかった場合に修正する"""
    if not rec['name']:
        fix_name(rec, log)

    if not rec['postal_code']:
        fix_postal_code(rec, log)

    if not rec['address']:
        fix_address(rec, log)

    if not rec['tel']:
        # 電話番号がない場合
        fix_tel(rec, log)
    else:
        # 電話番号ある場合
        tel = mojimoji.zen_to_han(rec['tel'])
        if not rec['url']:
            # URLと結合していないか確認する。メールアドレスの場合もあるのであくまで暫定対応になる.
            ix = rec['tel'].find('http')
            if ix != -1:
                rec['tel'] = tel[:ix-1]
                rec['url'] = analyze_pdf_table.AnalyzePdfTable.conv_url(tel[ix:])
                log(
                    "telにhttpを検出したためurlにコピーします. tel:{}->{}, {}".format(
                        tel,
                        rec['tel'],
                        rec['url']
                    )
                )

    return rec

def copy_record(rec_list, src_ix, dst_ix):
    """レコードのコピー処理"""
    for k in rec_list[dst_ix]:
        if not rec_list[dst_ix][k]:
            rec_list[dst_ix][k] = rec_list[src_ix][k]

def image_proc_remove_dotline(threshold):
    """画像中の点線を直線に直す"""
    #el = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    el = np.zeros((5,5), np.uint8)
    el[2, :] =1    
    threshold = cv2.dilate(threshold, el, iterations=1)
    threshold = cv2.erode(threshold, el, iterations=1)
    return threshold

def setup_rule():
    """ルールの設定"""
    rules = {}
    rules['茨城県'] = copy.deepcopy(DEFAULT_RULE)
    rules['茨城県']['other_page_offset'] = 0
    rules['宮崎県'] = copy.deepcopy(DEFAULT_RULE)
    rules['宮崎県']['other_page_offset'] = 0
    rules['京都府'] = copy.deepcopy(DEFAULT_RULE)
    rules['京都府']['other_page_offset'] = 0
    rules['鹿児島県'] = copy.deepcopy(DEFAULT_RULE)
    rules['鹿児島県']['other_page_offset'] = 0
    rules['富山県'] = copy.deepcopy(DEFAULT_RULE)
    rules['富山県']['other_page_offset'] = 0
    rules['香川県'] = copy.deepcopy(DEFAULT_RULE)
    rules['香川県']['other_page_offset'] = 0
    rules['佐賀県'] = copy.deepcopy(DEFAULT_RULE)
    rules['佐賀県']['other_page_offset'] = 0
    rules['長崎県'] = copy.deepcopy(DEFAULT_RULE)
    rules['長崎県']['other_page_offset'] = 0
    rules['和歌山県'] = copy.deepcopy(DEFAULT_RULE)
    rules['和歌山県']['other_page_offset'] = 0
    rules['福岡県'] = copy.deepcopy(DEFAULT_RULE)
    rules['福岡県']['other_page_offset'] = 0

    #
    rules['愛知県'] = copy.deepcopy(DEFAULT_RULE)
    rules['愛知県']['other_page_offset'] = 0
    rules['愛知県']['columns']['name']['index'] = 3
    rules['愛知県']['columns']['postal_code']['index'] = 4
    rules['愛知県']['columns']['address']['index'] = 5
    rules['愛知県']['columns']['tel']['index'] = 6
    rules['愛知県']['columns']['url']['index'] = 7
    rules['愛知県']['columns']['first']['index'] = 9
    rules['愛知県']['columns']['revisit']['index'] = 8
    rules['愛知県']['columns']['department']['index'] = 12
    rules['愛知県']['columns']['doctor']['index'] = 13
    rules['愛知県']['columns']['cooperation']['index'] = 14
    #
    rules['東京都'] = copy.deepcopy(DEFAULT_RULE)
    rules['東京都']['first_page_offset'] = 3
    #
    rules['奈良県'] = copy.deepcopy(DEFAULT_RULE)
    rules['奈良県']['other_page_offset'] = 0
    rules['奈良県']['columns']['name']['index'] = 2
    rules['奈良県']['columns']['postal_code']['index'] = 3
    rules['奈良県']['columns']['address']['index'] = 4
    rules['奈良県']['columns']['tel']['index'] = 5
    rules['奈良県']['columns']['url']['index'] = 6
    rules['奈良県']['columns']['first']['index'] = 7
    rules['奈良県']['columns']['revisit']['index'] = 8
    rules['奈良県']['columns']['department']['index'] = 9
    rules['奈良県']['columns']['doctor']['index'] = 10
    rules['奈良県']['columns']['cooperation']['index'] = 11
    #
    rules['兵庫県'] = copy.deepcopy(DEFAULT_RULE)
    rules['兵庫県']['image_proc'] = image_proc_remove_dotline
    #
    rules['山梨県'] = copy.deepcopy(DEFAULT_RULE)
    rules['山梨県']['columns']['first']['index'] = 6
    rules['山梨県']['columns']['revisit']['index'] = 7
    rules['山梨県']['columns']['department']['index'] = 10
    rules['山梨県']['columns']['doctor']['index'] = 11
    rules['山梨県']['columns']['cooperation']['index'] = 12
    return rules
    
def fix_result_list(result):
    """PDFの取得結果の一覧を修正する.
    ・名称が空の行がある場合、ページの区切りによって前後のどちらかの行から欠損しているデータを取得する
    """
    last_validated_ix = 0
    for ix in range(len(result)):
        if ix == 0:
            continue
        if result[ix]['name']:
            last_validated_ix = ix
            continue
        next_validated_ix = ix
        for tmp_ix in range(ix, len(result)):
            if result[tmp_ix]['name']:
                next_validated_ix = tmp_ix
                break
        if result[ix]['page'] != result[next_validated_ix]['page']:
            # 現在の名称が空で次に改ページがある場合は次の行からデータを取得する
            copy_record(result, next_validated_ix, ix)
        elif result[ix]['page'] != result[last_validated_ix]['page']:
            # 現在の名称が空で現在行で改ページがある場合は前の行からデータを取得する
            copy_record(result, last_validated_ix, ix)
        else:
            # 修正ができなかった場合
            print(
                "名前のないレコードの復旧はできませんでした 最後の有効行のname:{} page:{} 行:{}".format(
                    result[last_validated_ix]['name'],
                    result[ix]['page'],
                    result[ix]['index']
                )
            )
    return result

def output_result(result, dst_folder, name):
    """解析結果をJSONとCSVに保存"""
    json_path = '{}/{}.json'.format(dst_folder, name)
    with open(json_path, mode='w', encoding='utf8') as fp:
        json.dump(result, fp, sort_keys=True, indent=4, ensure_ascii=False)

    csv_path = '{}/{}.csv'.format(dst_folder, name)
    with open(csv_path, 'w', encoding='utf16', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        for r in result:
            writer.writerow([
                r['name'],
                r['postal_code'],
                r['address'],
                r['tel'],
                r['url'],
                r['first'],
                r['revisit'],
                r['department'],
                r['doctor'],
                r['cooperation']
            ])


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

    pdf = analyze_pdf_table.AnalyzePdfTable()
    #
    rules = setup_rule()

    for data in pdf_info["list"]:
        print(data['local'])
        result = []
        rule = DEFAULT_RULE
        if data['name'] in rules:
            rule = rules[data['name']]
        result = pdf.parse_pdf(data['local'], rule, fix_record)

        # 解析結果のログだけは出力しておく
        log_path = '{}/{}_log.json'.format(dst_folder, data['name'])
        with open(log_path, mode='w', encoding='utf8') as fp:
            json.dump(pdf.log, fp, sort_keys=True, indent=4, ensure_ascii=False)

        # PDFの取得結果の一覧を修正する
        result = fix_result_list(result)

        # ファイルに保存
        output_result(result, dst_folder, data['name'])


if __name__ == '__main__':
    main(sys.argv)
