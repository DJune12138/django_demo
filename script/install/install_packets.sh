#!/usr/bin/sh

cd `dirname $0` && SCRIPT_PATH=$(pwd)

yum -y install gcc python-devel mysql-devel sqlite-devel MySQL-python freetype-devel openssh-clients python-sqlite python-setuptools libxml2* libjpeg libjpeg-devel uwsgi-plugin-python2 || exit 1

easy_install='easy_install -i http://mirrors.aliyun.com/pypi/simple'

$easy_install twisted==13.1.0
$easy_install pymongo==2.8.1
$easy_install python-memcached==1.58
$easy_install sqlparse==0.2.1
$easy_install tornado==4.4.1
$easy_install uwsgi==2.0.17
$easy_install pycrypto

DjangoPack='Django-1.6.7.tar.gz'
if [[ -e "$DjangoPack" ]];then
    tar xf $DjangoPack && cd Django-1.6.7
    python setup.py install
    cd .. && rm -rf Django-1.6.7
fi

ImageingPack="Imaging-1.1.7.tar.gz"
if [[ -e "$ImageingPack" ]];then
    tar xf $ImageingPack && cd Imaging-1.1.7
    if uname -a | grep x86_64;then
        sed -i "s#^FREETYPE_ROOT.*#FREETYPE_ROOT=\'/usr/lib64\'#" setup.py 
    fi
    python setup.py build
    python setup.py install
    cd .. && rm -rf Imaging-1.1.7
fi