#!/bin/sh

moduleName=emi.dcache.srm-probes

TAG=1.0.1

age=1

cd srm-probes
cp -r src ${moduleName}-${TAG}
tar -z -c -f ${moduleName}-${TAG}.src.tar.gz ${moduleName}-${TAG} CHANGES README setup.py

cp ${moduleName}-${TAG}.src.tar.gz /usr/src/redhat/SOURCES/${moduleName}-${TAG}.tgz

sudo rpmbuild --define '_topdir /usr/src/redhat' -ba grid-monitoring-probes-org.sam.spec

cp -r /usr/src/redhat/* .

cd RPMS/noarch

osMajorRel=$(echo `lsb_release -r | awk -F":" '{print $2}' |awk -F"." '{print $1}'` | tr -d ' ')

case "$osMajorRel" in
  5)  export osType=""
    echo "osType set to SL5"
    ;;
  6)  echo "This is SL6";
    export osType="el6.";
    ;;
  *)  echo "Unknown operating system"
    ;;
esac

rpm2cpio ${moduleName}-${TAG}-${age}.${osType}noarch.rpm| cpio -id
tar -czf ${moduleName}-${version}-${age}.${osType}noarch.tar.gz usr

