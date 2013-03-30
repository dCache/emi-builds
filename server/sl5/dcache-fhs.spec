Summary: dCache Server
Vendor: dCache.org
Name: dcache-server
Version: 2.2.9
Release: 1
BuildArch: noarch
Prefix: /
Packager: dCache.org <support@dcache.org>.

Obsoletes: dCacheConfigure
Provides: dCachePostInstallConfigurationScripts
Provides: dcache-server
AutoReqProv: no
BuildRequires: java-1.7.0-openjdk.x86_64
Requires(pre): shadow-utils
Requires(post): chkconfig
Requires(preun): chkconfig
# This is for /sbin/service
Requires(preun): initscripts

License: Distributable
Group: Applications/System
%description
dCache is a distributed mass storage system.

This package contains the server components.

%pre
if [ -d /opt/d-cache/classes ]; then
   echo "Can't update package in /opt (/opt/d-cache/classes exists)"
   exit 1
fi

/sbin/service dcache-server stop >/dev/null 2>&1

# Make sure the administrative user exists
getent group dcache >/dev/null || groupadd -r dcache
getent passwd dcache >/dev/null || \
    useradd -r -g dcache -d /var/lib/dcache -s /bin/bash \
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

exit 0

%post
# ensure directory ownership
chown dcache:dcache /var/lib/dcache
chown dcache:dcache /var/lib/dcache/config
chown dcache:dcache /var/lib/dcache/billing
chown dcache:dcache /var/lib/dcache/plots
chown dcache:dcache /var/lib/dcache/statistics
chown dcache:dcache /var/lib/dcache/credentials

# delegated proxies should not be accessible to anybody else
chmod 700 /var/lib/dcache/credentials

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

# generate admin door ssh2 server key
if [ ! -f /etc/dcache/admin/ssh_host_dsa_key ]; then
    ssh-keygen -q -t dsa -f /etc/dcache/admin/ssh_host_dsa_key -N ""
    chmod 640 /etc/dcache/admin/ssh_host_dsa_key
    chgrp dcache /etc/dcache/admin/ssh_host_dsa_key
fi

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
/usr/share/doc/dcache-server
/usr/share/dcache
/usr/share/man/man8/dcache-bootloader.8.gz
/usr/share/man/man8/dcache.8.gz 
/var/log/dcache
%attr(0755,root,root) /etc/rc.d/init.d/dcache-server
%attr(0755,root,root) /etc/bash_completion.d/dcache
%docdir /usr/share/doc/dcache-server
%config(noreplace) /etc/dcache
%config(noreplace) /var/lib/dcache

%changelog
* Thu Mar 28 2013 Christian Bernardt dCache <christian.bernardt@desy.de> 2.2.9-1
- Update spec file in accordance with upstream file
* Tue Jun 26 2012 Christian Bernardt dCache <christian.bernardt@desy.de> 2.2.2-1
- Adapting changes of current dCache build from tag 2.2.2
* Fri Mar 2 2012 Christian Bernardt dCache <christian.bernardt@desy.de> 2.1.0-1
- Prepare spec file to be compliant with EMI ETICS build process
