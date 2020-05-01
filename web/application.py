# coding=utf-8
from bottle import get, post, template, request, Bottle, response, redirect, abort
from json import dumps
import os
import json
from collections import defaultdict
import time
import cgi
import urllib
import hospital_db


app = Bottle()
db = hospital_db.HospitalDb()
info_json = None

def setup(conf):
    global app
    global db
    global info_json
    db.connect(conf.get('database', 'path'))
    info_json = conf.get('copyright', 'info_json')

@app.get('/')
def Home():
    #return 'road_mgt_db page...'
    redirect("/yakusyopdf/home.html")


@app.get('/json/get_hospital')
def get_hospital():
    ret = {}
    with open(info_json, mode='r', encoding='utf8') as fp:
        info = json.load(fp)
    try:
        lat = float(request.query.lat)
        lng = float(request.query.lng)
        ret = {
            'items' : db.get_hospital(lat, lng),
            'lastupdate': info['download_time']
        }
    except ValueError:
        ret = {
            'error' : 'パラメータが不正です'
        }
    response.content_type = 'application/json;charset=utf-8'
    return json.dumps(ret)

