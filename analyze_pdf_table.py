"""PDFのテーブルを解析する."""
import os
from tqdm import tqdm
import camelot
import camelot_ex
import mojimoji
from camelot.utils import (
    TemporaryDirectory,
)


class AnalyzePdfTable:
    """PDF中のテーブルを指定のルールで解析する"""
    log = []
    target_path = ''
    page = 0
    rule = {}
    fixrec_func = None

    def info(self, s):
        "infoレベルのログを記録する"
        self.log.append({
            "kind" : "info",
            "path" : self.target_path,
            "page" : self.page,
            "message" : s
        })

    def warn(self, s):
        "warnレベルのログを記録する"
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

    def _parse_table(self, table):
        ret = []
        df = table.df
        if len(df.columns.values) < len(self.rule['columns']):
            self.warn(
                "列数の少ないデータフレームが取得されたためスキップします df.columns.values:{}".format(
                    str(df.columns.values)
                )
            )
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
            if self.fixrec_func:
                rec = self.fixrec_func(rec, self.info)
            rec['page'] = str(self.page)
            rec['order'] = str(table.order)
            rec['index'] = str(ix)
            ret.append(rec)
        return ret

    def _parse_page(self, handler, page):
        ret = []
        tables = self._read_pdf(
            handler,
            page,
            line_scale=self.rule['line_scale'],
            image_proc=self.rule['image_proc'],
            layout_kwargs={'char_margin': self.rule['char_margin']},
            copy_text=['v']
        )

        if not tables:
            return ret
        for table in tables:
            if table.parsing_report['accuracy'] <= self.rule['accuracy']:
                self.warn("解析対象のテーブルではありません accurasy:{}/{}".format(table.parsing_report['accuracy'], self.rule['accuracy']))
                continue
            ret.extend(self._parse_table(table))
        return ret

    def _read_pdf(self, handler, page, password=None, suppress_stdout=False, layout_kwargs={}, **kwargs):

        tables = []
        with TemporaryDirectory() as tempdir:
            handler._save_page(handler.filepath, page, tempdir)
            tmp_page = os.path.join(tempdir, "page-{0}.pdf".format(page))
            parser = camelot_ex.LatticeEx(
                **kwargs
            )
            t = parser.extract_tables(
                tmp_page,
                suppress_stdout=suppress_stdout,
                layout_kwargs=layout_kwargs
            )
            tables.extend(t)
            return tables


    def parse_pdf(self, path, rule, fixrec_func=None):
        """PDFの解析を実行する"""
        self.target_path = path
        self.rule = rule
        self.page = 0
        self.log = []
        self.fixrec_func = fixrec_func
        ret = []
        handler = camelot.handlers.PDFHandler(path)
        # 内部関数であるが下記のissueで記載されている解決方法
        # https://github.com/camelot-dev/camelot/issues/28
        pages = handler._get_pages(path, pages="all")
        for self.page in tqdm(pages):
            page_ret = self._parse_page(handler, self.page)
            ret.extend(page_ret)
        return ret

    @classmethod
    def conv_oneline(cls, s):
        """指定の文字列を1行にする"""
        s = s.replace('\n', '')
        s = s.replace('\r', '')
        return s

    @classmethod
    def conv_url(cls, s):
        """URL用の変換文字。半角に変換する"""
        s = cls.conv_oneline(s)
        return mojimoji.zen_to_han(s)

    @classmethod
    def chk_required(cls, s):
        """必須チェック。問題ない場合は空文字を返す"""
        if not s.strip():
            return "値が存在しません."
        return ""

    @classmethod
    def conv_number(cls, s):
        """数値コードチェック。郵便番号とTELで使えるか確認する。問題ない場合は空文字を返す"""
        s = cls.conv_oneline(s)
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

    @classmethod
    def conv_postal_code(cls, s):
        """NNN-NNNN形式の郵便番号に変換する。"""
        s = cls.conv_number(s)
        return s[0:3] + "-" + s[3:]

    @classmethod
    def chk_postal_code(cls, s):
        """郵便番号チェック。問題ない場合は空文字を返す"""
        s = cls.conv_number(s)
        if not s.isdigit() or len(s) != 7:
            return "郵便番号の形式ではありません"
        return ""
