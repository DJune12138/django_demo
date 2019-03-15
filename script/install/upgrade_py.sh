#!/bin/sh

tar -zxvf Python-2.7.10.tgz

cd Python-2.7.10

./configure && make all && make install && make clean && make distclean

/usr/local/bin/python2.7 -V

mv /usr/bin/python /usr/bin/python2.6.6

ln -s /usr/local/bin/python2.7 /usr/bin/python

python -V

sed -i 's/python/python2.6.6/g' /usr/bin/yum

cd ..

rm -rf Python-2.7.10
