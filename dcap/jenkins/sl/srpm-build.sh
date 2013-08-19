echo "Building package ${packaging} of ${REPOSITORY}/tags/${TAG}"
echo "Workspace at: ${WORKSPACE}"

export age=$age
git clone https://github.com/dCache/dcap.git ${WORKSPACE}/${TAG};
cd ${WORKSPACE}/${TAG};
git checkout ${TAG};

# old checkout with SVN
# svn co ${REPOSITORY}/tags/${TAG} ${WORKSPACE}/${TAG};

cd ${WORKSPACE}/${TAG}
######
# This part needs to be taken out as soon as everything is committed to the repo and in some tag and released.
######
wget -O COPYING http://www.gnu.org/licenses/gpl.txt
wget -O COPYING.LIB http://www.gnu.org/licenses/gpl.txt

cd ${WORKSPACE}
tar cjf ${WORKSPACE}/${TAG}.src.tar.gz ${TAG};
cd -

cp ${WORKSPACE}/${TAG}.src.tar.gz /usr/src/redhat/SOURCES/;

### This only works as long as dcap svn tags are in the form e.g.dcap-2.47.7 not including the age

export VERSION=`echo ${TAG} | awk -F"-" '{print $2}'`

# SL5 and SL6 spec files are the same. If this changes, this is the place to differentiate between both

wget http://www.dcache.org/downloads/emi/releases/dcap/sl5/${VERSION}/${specFileName}
sed -i "s/Version: 2.47.7/Version: ${VERSION}/" ${specFileName};

rpmbuild --define '_topdir /usr/src/redhat' -ba ${specFileName};
cd ${WORKSPACE}
cp -r /usr/src/redhat/* .
cd RPMS/x86_64

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

/bin/echo "osType= " ${osType}
rpm2cpio ${TAG}-${age}.${osType}x86_64.rpm | cpio -id;
rpm2cpio dcap-devel-${VERSION}-${age}.${osType}x86_64.rpm | cpio -id;
rpm2cpio dcap-libs-${VERSION}-${age}.${osType}x86_64.rpm | cpio -id;
rpm2cpio dcap-tunnel-gsi-${VERSION}-${age}.${osType}x86_64.rpm | cpio -id;
rpm2cpio dcap-tunnel-krb-${VERSION}-${age}.${osType}x86_64.rpm | cpio -id;
rpm2cpio dcap-tunnel-ssl-${VERSION}-${age}.${osType}x86_64.rpm | cpio -id;
rpm2cpio dcap-tunnel-telnet-${VERSION}-${age}.${osType}x86_64.rpm | cpio -id;

tar cjf ${TAG}-${age}.x86_64.tar.gz usr; 
rm -rf usr
