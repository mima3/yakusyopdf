# 目的
厚生労働省が公開している[新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/rinsyo/index_00014.html)のPDF情報をCSVやJSONに変換して、コンピュータで処理をしやすいようにします。

説明については下記を参照してください。
https://needtec.sakura.ne.jp/wod07672/2020/04/29/%e5%8e%9a%e7%94%9f%e5%8a%b4%e5%83%8d%e7%9c%81%e3%81%aepdf%e3%82%92csv%e3%82%84json%e3%81%ab%e5%a4%89%e6%8f%9b%e3%81%99%e3%82%8b/


## 依存するライブラリ
 - |beautifulsoup4
 - opencv-python
 - camelot-py
 - mojimoji
 - requests
 - tqdm

## 使用方法

```
# 新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療についてのページからPDFをダウンロードしてフォルダに保存する
python download_pdf.py

# 作成したフォルダを指定して、PDFの内容からJSONとCSVを作成する
python analyze_pdf.py 20200428

# 各都道府県ごとのJSONファイルを1つのファイルに纏めます。また、この際、キーを住所とします。
python merge_json 20200428

# YahooのジオコーダAPIを用いて住所から経度・緯度を求めて更新します。
python create_geo.py 20200428 YahooのAPPID

# ジオコーダAPIの使用量を減らすため、以前作成した経度緯度情報をインポートすることも可能です
python create_geo_by_json.py 古いall_data.json 新しいall_data.json

# データベースに保存します。
python create_hospital_db.py 20200428\all_data.json 20200428\hospital.sqlite
```

