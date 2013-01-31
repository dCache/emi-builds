#
# EMI dCache server spec v 1.1 
#

Summary: dCache Server
Vendor: dcache.org
Name: dcache-server
Version: 2.2.1
Release: 1
BuildArch: noarch

Source0: emi.dcache.server-%{version}.src.tar.gz
BuildRoot: %{_builddir}/%{name}-root
Obsoletes: dCacheConfigure
Provides: dCachePostInstallConfigurationScripts
Provides: dcache-server
BuildRequires: maven
BuildRequires: java-1.6.0-openjdk-devel 

Requires: nfs-utils
Requires(pre): shadow-utils
Requires(post): chkconfig
Requires(preun): chkconfig
# This is for /sbin/service
Requires(preun): initscripts

License: Distributable
Group: Applications/System
%description
The software provided with this package, dCache, is a distributed mass storage system.

This package contains the server components.

%prep
%setup -q
%build
echo "CurrentDir"
pwd
%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

mvn -B -am -pl modules/fhs package -Dmaven.repo.local=%{_topdir}/.m2/localRepository -Dfhs.outputDirectory=%{buildroot} -DskipTests
mv %{buildroot}/dcache-fhs-%{version}/* %{buildroot}
rm -rf %{buildroot}/dcache-fhs-%{version}
mkdir -p %{buildroot}/etc/rc.d/init.d/
mkdir -p %{buildroot}/etc/bash_completion.d/
cp ./pkgs/rpm/dcache-server.init %{buildroot}/etc/rc.d/init.d/dcache-server
cp ./pkgs/rpm/dcache.bash-completion %{buildroot}/etc/bash_completion.d/dcache

%clean
rm -rf %{buildroot}

# defining FHS paths
%define share_dir /usr/share/dcache
%define lib_dir /var/lib/dcache

%define poolmanager_conf %{lib_dir}/config/poolmanager.conf
%define poolmanager_conf_installsave  %{poolmanager_conf}.%{version}.%{release}.installsave
%define poolmanager_conf_rpmsave %{poolmanager_conf}.rpmsave

%define billing_dir %{lib_dir}/billing

%define restore_state_script /tmp/dCache-restore-state


%pretrans
# save existing PoolManager.conf
if [ -f %{poolmanager_conf} ]
then
   cp %{poolmanager_conf} %{poolmanager_conf_installsave}
   echo "Backing up existing PoolManager.conf"
fi


%posttrans
if [ ! -f %{poolmanager_conf} ] && [ -f %{poolmanager_conf_installsave} ] && [ -f %{poolmanager_conf_rpmsave} ]
then
  diff -q %{poolmanager_conf_installsave} %{poolmanager_conf_rpmsave}
  if [  $? -eq 0 ]
  then
     echo "Restoring original PoolManager.conf"
     cp %{poolmanager_conf_installsave} %{poolmanager_conf}
  fi
  rm -f %{poolmanager_conf_installsave}
fi


%pre
if [ -d /opt/d-cache/classes ]; then
   echo "Can't update package in /opt (/opt/d-cache/classes exists)"
   exit 1
fi

/sbin/service dcache-server stop >/dev/null 2>&1

if [ -f ${RPM_INSTALL_PREFIX}/bin/dcache ]; then
   ${RPM_INSTALL_PREFIX}/bin/dcache stop
fi

if [ -f %{share_dir}/classes/gplazma.jar ]; then
   rm -f %{share_dir}/classes/gplazma.jar
fi

if [ -d %{share_dir}/classes/gplazma-libs ]; then
   rm -rf %{share_dir}/classes/gplazma-libs
fi

if [ $1 -ge 2 ]; then   # True when upgrading dCache
    stat -c "chown %u:%g %{billing_dir}" %{billing_dir} >> %{restore_state_script}
fi

if [ ! -d %{lib_dir} ]; then
    mkdir -p %{lib_dir}/credentials
fi

%post

if [ ! -d %{lib_dir}/credentials ]; then
    mkdir -p %{lib_dir}/credentials
fi

# Make sure the administrative user exists
getent group dcache >/dev/null || groupadd -r dcache

getent passwd dcache >/dev/null || \
    useradd -r -g dcache -d %{lib_dir} -s /bin/bash \
    -c "dCache administrator" dcache

# check validity of dcache user and group
if [ "`id -u dcache`" -eq 0 ]; then
    echo "The dcache system user must not have uid 0 (root).
Please fix this and reinstall this package." >&2
    exit 1
fi
if [ "`id -g dcache`" -eq 0 ]; then
    echo "The dcache system user must not have root as primary group.
Please fix this and reinstall this package." >&2
    exit 1
fi

if [ $1 -ge 2 ]; then   # True when upgrading
   if [ -f %{restore_state_script} ]; then
      . %{restore_state_script}
      rm %{restore_state_script}
   fi
fi

# ensure directory ownership
chown dcache:dcache %{lib_dir}
chown dcache:dcache %{lib_dir}/config
chown dcache:dcache %{lib_dir}/billing
chown dcache:dcache %{lib_dir}/statistics
chown dcache:dcache %{lib_dir}/credentials

# delegated proxies should not be accessible to anybody else
chmod 700 %{lib_dir}/credentials

# generate admin door server key
if [ ! -f /etc/dcache/admin/server_key ]; then
    ssh-keygen -q -b 768 -t rsa1 -f /etc/dcache/admin/server_key -N ""
    chmod 640 /etc/dcache/admin/server_key
    chgrp dcache /etc/dcache/admin/server_key
fi

# generate admin door host key
if [ ! -f /etc/dcache/admin/host_key ]; then
    ssh-keygen -q -b 1024 -t rsa1 -f /etc/dcache/admin/host_key -N ""
    chmod 640 /etc/dcache/admin/host_key
    chgrp dcache /etc/dcache/admin/host_key
fi

# generate admin door DSA host key
if [ ! -f /etc/dcache/admin/ssh_host_dsa_key ]; then
    ssh-keygen -t dsa -f /etc/dcache/admin/ssh_host_dsa_key -N ""
    chmod 640 /etc/dcache/admin/ssh_host_dsa_key
    chgrp dcache /etc/dcache/admin/ssh_host_dsa_key
fi

if [ ! -f /etc/sysconfig/rpcbin ]; then
    echo "RPCBIND_ARGS=\"-i\"" > /etc/sysconfig/rpcbin
fi

# This adds the proper /etc/rc*.d links for the script
/sbin/chkconfig --add dcache-server

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service dcache-server stop >/dev/null 2>&1
    /sbin/chkconfig --del dcache-server
fi


%files
%defattr(-,root,root)
/usr/bin/chimera-cli
/usr/bin/dcache
/usr/sbin/dcache-info-provider
/usr/share/doc/dcache
/usr/share/dcache
/usr/share/man/man8/dcache-bootloader.8.gz
/usr/share/man/man8/dcache.8.gz
/var/log/dcache

%attr(-,dcache,dcache) /var/lib/dcache/alarms
%attr(-,dcache,dcache) /var/lib/dcache/config
%attr(-,dcache,dcache) /var/lib/dcache/billing
%attr(-,dcache,dcache) /var/lib/dcache/plots
%attr(-,dcache,dcache) /var/lib/dcache/statistics
%attr(700,dcache,dcache) /var/lib/dcache/credentials

%attr(0755,root,root) /etc/rc.d/init.d/dcache-server
%attr(0755,root,root) /etc/bash_completion.d/dcache
%docdir /usr/share/doc/dcache
%config(noreplace) /etc/dcache
%config(noreplace) /var/lib/dcache



%changelog
* Thu Jan 31 2013 Christian Bernardt dCache <christian.bernardt@desy.de> 2.5.0-1
- Update spec file in accordance with upstream file
* Tue Jun 26 2012 Christian Bernardt dCache <christian.bernardt@desy.de> 2.2.2-1
- Adapting changes of current dCache build from tag 2.2.2
* Fri Mar 2 2012 Christian Bernardt dCache <christian.bernardt@desy.de> 2.1.0-1
- Prepare spec file to be compliant with EMI ETICS build process
