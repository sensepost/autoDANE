#!/bin/bash

apt-get install -y msgpack-python python-twisted python-pip wkhtmltopdf libssl-dev libffi-dev python-dev build-essential

pip install netifaces
pip install docxtpl
pip install impacket
pip install crackmapexec

git clone git://github.com/SpiderLabs/msfrpc.git msfrpc
cd msfrpc/python-msfrpc/
python setup.py install
cd ../..
rm -r msfrpc/

wget http://download.gna.org/wkhtmltopdf/0.12/0.12.3/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
tar -xvf wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
cp -r wkhtmltox/bin/* /usr/bin/
cp -r wkhtmltox/include/* /usr/include/
cp -r wkhtmltox/lib/* /usr/lib/
cp -r wkhtmltox/share/* /usr/share/
rm -r wkhtmltox/

service postgresql start
sudo -u postgres bash -c "psql -c \"create user autodane with password 'OHZdz7CW8Lv4PCa';\""
sudo -u postgres bash -c "psql < createdb.sql"
sudo -u postgres bash -c "psql autodane < createdbstructure.sql"
sudo -u postgres bash -c "psql autodane -c \"grant all privileges on all tables in schema public to autodane\""
sudo -u postgres bash -c "psql autodane -c \"grant all privileges on all sequences in schema public to autodane\""

mkdir temp
mkdir logs
