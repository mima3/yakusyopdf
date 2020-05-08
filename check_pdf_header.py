"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のページから対応医療機関リストのPDFをヘッダを調べる."""
import sys
import json
import camelot
from pathlib import Path


def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 2:
        print("Usage #python %s [info.jsonのパス]" % argvs[0])
        exit()


    info_json_path = argvs[1]
    dst_folder = str(Path(info_json_path).resolve().parents[0])
    with open(info_json_path, mode='r', encoding='utf8') as fp:
        pdf_info = json.load(fp)

    for data in pdf_info["list"]:
        path = data['local']
        handler = camelot.handlers.PDFHandler(path)
        pages = handler._get_pages(path, pages="all")
        pages_param = '1'
        if len(pages) > 1:
            pages_param = '1,2'
        tables = camelot.read_pdf(
          path,
          pages = pages_param,
          line_scale = 30,
          copy_text=['v'],
          layout_kwargs = {
            'char_margin': 0.25
          }
        )
        match_row_cnt = 0    # 0
        if len(tables) == 2:
            if len(tables[0].df.columns.values) == len(tables[1].df.columns.values):
                for ix in tables[0].df.index.values:
                    if ix >= len(tables[1].df.index.values):
                        break
                    is_match_row = True
                    for col in tables[0].df.columns.values:
                        if tables[0].df.loc[ix][col] != tables[1].df.loc[ix][col]:
                            is_match_row = False
                            break
                    if not is_match_row:
                        break
                    match_row_cnt += 1
            else:
                print(data['name'], '1page目と2page目で列数が異なります', tables[0].df.columns.values) ,len(tables[1].df.columns.values)
        else:
            print(data['name'], '予期せぬテーブル数が取得されました')
        
        print(data['name'], 'ページ数:', len(pages), '列数:', len(tables[0].df.columns.values), '1ページ目と2ページ目の一致行', match_row_cnt)


if __name__ == '__main__':
    main(sys.argv)
