#
# $Id: dcache-server.spec.template,v 1.0 2011-11-03 11:35:02 christian Exp $
#

Summary: dCache Server
Vendor: DESY/FNAL/NDGF
Name: dcache-srmclient
Version: 2.2.4
release: 1%{?dist}
BuildArch: x86_64 

BuildRoot: %{_builddir}/%{name}-root

Source0: dcache-srmclient-%{version}.src.tar.gz

BuildRequires: maven
BuildRequires: java-1.6.0-openjdk-devel 

License: Distributable
Group: Applications/System
%description
dCache is a distributed mass storage system.

This package contains the client components.

%prep
%setup -q
%build
echo "CurrentDir"
pwd
%install
rm -rf %{buildroot}
mkdir -p %{buildroot}


mvn -B -am -pl modules/srmclient package -Dmaven.repo.local=%{_topdir}/.m2/localRepository -Dfhs.outputDiretory=%{buildroot} -DskipTests
mv %{_builddir}/%{name}-%{version}/modules/srmclient/target/srmclient-%{version}/* %{buildroot}

%clean
rm -rf %{buildroot}

%pretrans

%posttrans

%pre

%post

%preun

%files
%defattr(-,root,root)
%attr(755,root,root) /usr/bin/adler32
%attr(755,root,root) /usr/bin/srm-abort-files
%attr(755,root,root) /usr/bin/srm-abort-request
%attr(755,root,root) /usr/bin/srm-advisory-delete
%attr(755,root,root) /usr/bin/srm-bring-online
%attr(755,root,root) /usr/bin/srm-check-permissions
%attr(755,root,root) /usr/bin/srm-extend-file-lifetime
%attr(755,root,root) /usr/bin/srm-get-metadata
%attr(755,root,root) /usr/bin/srm-get-permissions
%attr(755,root,root) /usr/bin/srm-get-request-status
%attr(755,root,root) /usr/bin/srm-get-request-summary
%attr(755,root,root) /usr/bin/srm-get-request-tokens
%attr(755,root,root) /usr/bin/srm-get-space-metadata
%attr(755,root,root) /usr/bin/srm-get-space-tokens
%attr(755,root,root) /usr/bin/srm-release-files
%attr(755,root,root) /usr/bin/srm-release-space
%attr(755,root,root) /usr/bin/srm-reserve-space
%attr(755,root,root) /usr/bin/srm-set-permissions
%attr(755,root,root) /usr/bin/srm-storage-element-info
%attr(755,root,root) /usr/bin/srmcp
%attr(755,root,root) /usr/bin/srmls
%attr(755,root,root) /usr/bin/srmmkdir
%attr(755,root,root) /usr/bin/srmmv
%attr(755,root,root) /usr/bin/srmping
%attr(755,root,root) /usr/bin/srmrm
%attr(755,root,root) /usr/bin/srmrmdir
%attr(755,root,root) /usr/bin/srmstage
%attr(755,root,root) /usr/sbin/srm
%attr(755,root,root) /usr/sbin/url-copy.sh
%attr(755,root,root) /usr/share/srm
%attr(755,root,root) /usr/share/srm/lib/*.jar
%attr(755,root,root) /usr/share/srm/conf/*.map
%attr(755,root,root) /usr/share/srm/conf/*.xml

%changelog
* Thu Nov 8 2012 Christian Bernardt dCache <christian.bernardt@desy.de> 2.2.4-1
- Changing permissions for /usr/share/srm/lib
* Fri Mar 2 2012 Christian Bernardt dCache <christian.bernardt@desy.de> 2.1.0-1
- Prepare initial spec file to be compliant with EMI ETICS build process 
