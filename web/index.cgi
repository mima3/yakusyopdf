#! C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python37_64\python.exe
# coding: utf-8
from bottle import run
# import ConfigParser
import configparser  #python3
import sys


conf = configparser.ConfigParser()
conf.read("./application.ini")
try:
  i = 0
  path = conf.get('system', 'path' + str(i))
  while path != "":
    i = i + 1
    sys.path.append(path)
    path = conf.get('system', 'path' + str(i))
except configparser.NoOptionError as e:
  pass

from application import app, setup
setup(conf)
run(app, server='cgi')
