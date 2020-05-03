# Webページ
## 目的
現在座標にもっとも近い病院の情報を取得するWebサービスです。  

https://needtec.sakura.ne.jp/yakusyopdf/

## レンタルサーバーへのデプロイ例

```
rm -rf yakusyopdf
git clone git://github.com/mima3/yakusyopdf
mkdir /home/username/www/yakusyopdf
cp -rf yakusyopdf/web/* /home/username/www/yakusyopdf
cp yakusyopdf/hospital_db.py /home/username/www/yakusyopdf/hospital_db.py

python /home/username/www/yakusyopdf/create_index_cgi.py "/home/username/local/bin/python3" "/home/username/work/yakusyopdf/application.ini" > /home/username/www/yakusyopdf/index.cgi
chmod +x  /home/username/www/yakusyopdf/index.cgi
```
