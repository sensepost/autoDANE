#!/bin/bash

apt-get install msgpack-python python-twisted python-pip

pip install netifaces

git clone https://github.com/CoreSecurity/impacket.git
cd impacket
python setup.py install 
cd ..
rm -r impacket

git clone git://github.com/SpiderLabs/msfrpc.git msfrpc
cd msfrpc/python-msfrpc/
python setup.py install
cd ../..
rm -r msfrpc/

service mysql start
mysql < createdb.sql
