import sys
import json
import camelot
import csv
import copy
import mojimoji
from tqdm import tqdm


class AnalyzePdf:
    log = []
    target_path = ''
    page = 0
    rule = {}

    def info(self, s):
        self.log.append({
             "kind" : "info",
             "path" : self.target_path,
             "page" : self.page,
             "message" : s
        })

    def warn(self, s):
        self.log.append({
             "kind" : "warn",
             "path" : self.target_path,
             "page" : self.page,
             "message" : s
        })

    def _check_empty_line(self, df, ix):
        """指定の行が空行か確認する"""
        result = True
        for k in self.rule['columns']:
           col_ix = self.rule['columns'][k]['index']
           if df.loc[ix][col_ix]:
               result = False
               break
        return result
    
    def _parse_df(self, df):
        ret = []
        if len(df.columns.values) < len(self.rule['columns']):
            self.warn("列数の少ないデータフレームが取得されたためスキップします df.columns.values:{}".format(str(df.columns.values)))
            return ret

        for ix in df.index.values:
            rec = {}
            # タイトル行をスキップする処理
            offset = 0
            if self.page == 1:
                offset = self.rule['first_page_offset']
            else:
                offset = self.rule['other_page_offset']
            if ix < offset:
                continue
            if self._check_empty_line(df, ix):
                self.info("空行のため処理をスキップします:{}".format(ix))
                continue
            for k in self.rule['columns']:
               col_ix = self.rule['columns'][k]['index']
               v = df.loc[ix][col_ix]
               chk_error = ""
               if 'chk_func' in self.rule['columns'][k]:
                   chk_method = getattr(self, self.rule['columns'][k]['chk_func'])
                   chk_error = chk_method(v)
                   if chk_error:
                       self.warn("{} index:{} col:{} value:{}".format(chk_error, ix, col_ix, v))

               if 'cnv_func' in self.rule['columns'][k] and not chk_error:
                   cnv_method = getattr(self, self.rule['columns'][k]['cnv_func'])
                   v = cnv_method(v)
               rec[k] = v

            ret.append(rec)
        return ret

    def _parse_page(self):
        ret = []
        tables = camelot.read_pdf(
            self.target_path,
            pages=str(self.page),
            line_scale = self.rule['line_scale'],
            layout_kwargs={'char_margin': self.rule['char_margin']}
        )

        if len(tables) == 0:
            return ret
        for table in tables:
            if table.parsing_report['accuracy'] <= self.rule['accuracy']:
                self.warn("解析対象のテーブルではありません accurasy:{}/{}".format(table.parsing_report['accuracy'], self.rule['accuracy']))
                continue
            ret.extend(self._parse_df(table.df))
        return ret


    def parse_pdf(self, path, rule):
        self.target_path = path
        self.rule = rule
        self.page = 0
        self.log = []
        ret = []
        handler=camelot.handlers.PDFHandler(path)
        pages = handler._get_pages(path, pages="all")
        for self.page in tqdm(pages):
           page_ret = self._parse_page()
           ret.extend(page_ret)
        return ret


    def conv_oneline(self, s):
        s = s.replace('\n', '')
        s = s.replace('\r', '')
        return s

    def chk_required(self, s):
        if not s.strip():
            return "値が存在しません."
        return ""

    def conv_number(self, s):
        s = self.conv_oneline(s)
        s = mojimoji.zen_to_han(s)
        s = s.strip()
        s = s.replace('〒', '')
        s = s.replace('-', '')
        s = s.replace('ー', '')
        s = s.replace('―', '')
        s = s.replace('‐', '')
        s = s.replace('－', '')
        s = s.replace('−', '')
        s = s.replace('ｰ', '')
        s = s.replace('(', '')
        s = s.replace(')', '')
        return s

    def conv_postal_code(self, s):
        s = self.conv_number(s)
        return s[0:3] + "-" + s[3:]

    def chk_postal_code(self, s):
        s = self.conv_number(s)
        if not s.isdigit() or len(s) != 7:
            return "郵便番号の形式ではありません"
        return ""

if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)
    if argc != 2:
        print("Usage #python %s [downloadフォルダのパス]" % argvs[0])
        exit()
    dst_folder = argvs[1]
    with open( '{}/info.json'.format(dst_folder), mode='r', encoding='utf8') as fp:
        pdf_info = json.load(fp)

    pdf = AnalyzePdf()
    default_rule = {
       "first_page_offset" : 2,
       "other_page_offset" : 2,
       "char_margin" : 0.5,          # 2つの文字がこのマージンよりも接近している場合、それらは同じ行の一部と見なされます。
       "accuracy" : 95.0,
       "line_scale": 15,             # 大きいほど小さい線を検出するが、大きすぎると文字を線と見なしてしまう。
       "columns" : {
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
               "cnv_func" : "conv_oneline"
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
    #
    rules = {}
    rules['茨城県'] = copy.deepcopy(default_rule)
    rules['茨城県']['other_page_offset'] = 0
    rules['宮崎県'] = copy.deepcopy(default_rule)
    rules['宮崎県']['other_page_offset'] = 0
    rules['京都府'] = copy.deepcopy(default_rule)
    rules['京都府']['other_page_offset'] = 0
    rules['鹿児島県'] = copy.deepcopy(default_rule)
    rules['鹿児島県']['other_page_offset'] = 0
    rules['千葉県'] = copy.deepcopy(default_rule)
    rules['千葉県']['other_page_offset'] = 0
    rules['富山県'] = copy.deepcopy(default_rule)
    rules['富山県']['other_page_offset'] = 0
    rules['香川県'] = copy.deepcopy(default_rule)
    rules['香川県']['other_page_offset'] = 0
    rules['佐賀県'] = copy.deepcopy(default_rule)
    rules['佐賀県']['other_page_offset'] = 0
    rules['長崎県'] = copy.deepcopy(default_rule)
    rules['長崎県']['other_page_offset'] = 0
    
    #
    rules['愛知県'] = copy.deepcopy(default_rule)
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
    rules['東京都'] = copy.deepcopy(default_rule)
    rules['東京都']['first_page_offset'] = 3
    #
    rules['福岡県'] = copy.deepcopy(default_rule)
    rules['福岡県']['first_page_offset'] = 3
    rules['福岡県']['other_page_offset'] = 0
    #
    rules['奈良県'] = copy.deepcopy(default_rule)
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
    rules['三重県'] = copy.deepcopy(default_rule)
    rules['三重県']['accuracy'] = 90.0
    rules['徳島県'] = copy.deepcopy(default_rule)
    rules['徳島県']['accuracy'] = 90.0
    #
    # URLとTELが結合するため調整が必要
    #rules['和歌山県'] = copy.deepcopy(default_rule)
    #rules['和歌山県']['other_page_offset'] = 0
    #rules['和歌山県']['char_margin'] = 0.05
    #rules['広島県'] = copy.deepcopy(default_rule)
    #rules['広島県']['char_margin'] = 0.25    
    #
    rules['山梨県'] = copy.deepcopy(default_rule)
    rules['山梨県']['other_page_offset'] = 0
    rules['山梨県']['line_scale'] = 30
    rules['山梨県']['char_margin'] = 0.25
    #
    rules['神奈川県'] = copy.deepcopy(default_rule)
    rules['神奈川県']['accuracy'] = 90.0
    rules['神奈川県']['char_margin'] = 0.25
    #
    rules['新潟県'] = copy.deepcopy(default_rule)
    rules['新潟県']['char_margin'] = 0.25
    #
    rules['長野県'] = copy.deepcopy(default_rule)
    rules['長野県']['char_margin'] = 0.25

    for data in pdf_info["list"]:
        print(data['local'])
        result = []
        rule = default_rule
        if data['name'] in rules:
            rule = rules[data['name']]
        result = pdf.parse_pdf(data['local'], rule) 
        with open('{}/{}.json'.format(dst_folder, data['name']), mode='w', encoding='utf8') as fp:
            json.dump(result, fp, sort_keys = True, indent = 4, ensure_ascii=False)

        with open('{}/{}.csv'.format(dst_folder, data['name']), 'w', encoding='utf16', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for r in result:
                writer.writerow([r['name'], r['postal_code'], r['address'], r['tel'], r['url'], r['first'], r['revisit'], r['department'], r['doctor'], r['cooperation']])

        with open('{}/{}_log.json'.format(dst_folder, data['name']), mode='w', encoding='utf8') as fp:
            json.dump(pdf.log, fp, sort_keys = True, indent = 4, ensure_ascii=False)
