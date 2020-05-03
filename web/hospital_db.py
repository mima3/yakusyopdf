"""「新型コロナウイルス感染症の感染拡大を踏まえたオンライン診療について」のPDFの解析結果のJSONを結合します."""
import json
from peewee import *
from playhouse.sqlite_ext import *
from statistics import mean, median,variance,stdev
from datetime import date
#import logging
#logger = logging.getLogger('peewee')
#logger.setLevel(logging.DEBUG)
#logger.addHandler(logging.StreamHandler())


database_proxy = Proxy()


class Addresses(Model):
    """住所"""
    id = AutoField()
    address = CharField(null=False, index=True)

    class Meta:
        database = database_proxy

class Coordinates(Model):
    """座標情報"""
    id = AutoField()
    address_id = ForeignKeyField(Addresses, Addresses.id, related_name='address_coordinates', index=True)
    lat = DoubleField()
    lng = DoubleField()

    class Meta:
        database = database_proxy

class Hospitals(Model):
    """病院情報"""
    id = AutoField()
    address_id = ForeignKeyField(Addresses, Addresses.id, related_name='address_hospital', index=True)
    name = CharField()
    postal_code = CharField()
    tel = CharField()
    url = CharField()
    first = CharField()
    revisit = CharField()
    department = CharField()
    doctor = CharField()
    cooperation = CharField()

    class Meta:
        database = database_proxy


class HospitalDb:
    """病院用のDB操作"""
    database = None

    def connect(self, db_path):
        """SQLiteへの接続"""
        self.database = SqliteDatabase(db_path)
        database_proxy.initialize(self.database)
        self.database.create_tables([Addresses, Coordinates, Hospitals])


    def import_json(self, json_path):
        """JSONからDBを作成する"""
        address_info = {}
        with open(json_path.format(json_path), mode='r', encoding='utf8') as fp:
            address_info = json.load(fp)
        with self.database.transaction():
            for address in address_info:
                address_data = {
                    'address' : address
                }
                address_rec = Addresses.insert(address_data).execute()
                # 座標情報
                for coordinate in address_info[address]['coordinates']:
                    coordinate_data = {
                        'address_id' : address_rec.real,
                        'lat' : coordinate['lat'],
                        'lng' : coordinate['lng']
                    }
                    Coordinates.insert(coordinate_data).execute()
                # 病院情報
                for item in address_info[address]['items']:
                    item_data = {
                        'address_id' : address_rec.real,
                        'name' : item['name'],
                        'postal_code' : item['postal_code'],
                        'tel' : item['tel'],
                        'url' : item['url'],
                        'first' : item['first'],
                        'revisit' : item['revisit'],
                        'department' : item['department'],
                        'doctor' : item['doctor'],
                        'cooperation' : item['cooperation'],
                    }
                    Hospitals.insert(item_data).execute()
            self.database.commit

    def get_hospital(self, lat, lng):
        result = []
        rows = database_proxy.connection().execute("""
            select
              address_id,
              address,
              lat,
              lng,
              ABS(lat-?) + ABS(lng-?) as dist
            from coordinates 
            inner join addresses
              on addresses.id = coordinates.address_id
            order by dist asc
            limit 10;
        """,(lat, lng))
        for row in rows:
            query = Hospitals.select().where(Hospitals.address_id == row[0])
            for hospital in query:
                rec = {
                    'name' : hospital.name,
                    'postal_code' : hospital.postal_code,
                    'address': row[1],
                    'lat': row[2],
                    'lng': row[3],
                    'url' : hospital.url,
                    'tel' : hospital.tel,
                    'first' : hospital.first,
                    'revisit' : hospital.revisit,
                    'department' : hospital.department,
                    'doctor' : hospital.doctor,
                    'cooperation' : hospital.cooperation,
                }
                result.append(rec)
        return result

         
if __name__ == '__main__':
    main(sys.argv)
