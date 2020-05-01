"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のPDFの解析結果に地図座標を付与します"""
import sys
import hospital_db


def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 3:
        print("Usage #python %s [JSONのパス] [SQLiteのDB]" % argvs[0])
        exit()
    src_path = argvs[1]
    db_path = argvs[2]
    db = hospital_db.HospitalDb()
    db.connect(db_path)
    db.import_json(src_path)
    #print(db.get_hospital(35.182245, 136.496509))

if __name__ == '__main__':
    main(sys.argv)
