echo "Building package ${packaging} of ${REPOSITORY}/tags/${TAG}"
echo "Workspace at: ${WORKSPACE}"
#### export JAVA_HOME=$javaVersion
#### rm -f /usr/bin/javac /usr/bin/java
#### ln -s $javaVersion/bin/java /usr/bin/java
#### ln -s $javaVersion/bin/javac /usr/bin/javac
export PATH=$PATH:/usr/local/bin
osMajorRel=$(echo `lsb_release -r | awk -F":" '{print $2}' |awk -F"." '{print $1}'` | tr -d ' ')

case "$osMajorRel" in
  5)  export osType=""
    echo "osType set to SL5"
    export JAVA_HOME=/usr/lib/jvm/java-1.6.0-openjdk.x86_64
    #export JAVA_HOME=/usr/lib/jvm/java-7-sun
    export M2_HOME=/usr/share/java/maven
    ;;
  6)  echo "This is SL6";
    export JAVA_HOME=/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0.x86_64/jre
    #export JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk-1.7.0.9.x86_64/jre
    export M2_HOME=/usr/share/java/maven
    ;;
  *)  echo "Unknown operating system"
    ;;
esac

java -version
javac -version
mvn -version

export age=$age
rm -rf ${WORKSPACE}/*;
svn co ${REPOSITORY}/tags/${TAG} ${WORKSPACE}/dcache-srmclient-${TAG};

cd ${WORKSPACE}
tar cjf ${WORKSPACE}/dcache-srmclient-${TAG}.src.tar.gz dcache-srmclient-${TAG};
cd -

export JAVA_OPTS="-Xmx2048m -Xms1024m -XX:PermSize=512m -XX:MaxPermSize=512m";
export MAVEN_OPTS="-Xmx2048m -Xms1024m -XX:PermSize=512m -XX:MaxPermSize=512m"; 
cp ${WORKSPACE}/dcache-srmclient-${TAG}.src.tar.gz /usr/src/redhat/SOURCES/;

case "$osMajorRel" in
  5)  wget https://raw.github.com/dCache/emi-builds/master/srmclient/sl5/2.2.4-2/dcache-srmclient.spec --no-check-certificate
    ;;
  6)  wget https://raw.github.com/dCache/emi-builds/master/srmclient/sl6/2.2.4-2/dcache-srmclient.spec --no-check-certificate
    ;;
  *)  echo "Unknown operating system"
    ;;
esac

sed -i "s/Version: 2.2.4/Version: ${TAG}/" dcache-srmclient.spec;
sed -i "s/release: 1%{?dist}/release: ${age}%{?dist}/" dcache-srmclient.spec;
rpmbuild --define '_topdir /usr/src/redhat' -ba dcache-srmclient.spec;
cp -r /usr/src/redhat/* .
cd RPMS/x86_64

case "$osMajorRel" in
  5)  rpm2cpio dcache-srmclient-${TAG}-${age}.x86_64.rpm | cpio -id;
    ;;
  6)  rpm2cpio dcache-srmclient-${TAG}-${age}.el6.x86_64.rpm | cpio -id;
    ;;
  *)  echo "Unknown operating system"
    ;;
esac

tar cjf dcache-srmclient-${TAG}-${age}.x86_64.tar.gz usr; 

if [`rpmlint dcache-srmclient-${TAG}-${age}.x86_64.rpm | grep world-writable`]
  exit 1;

rm -rf usr
