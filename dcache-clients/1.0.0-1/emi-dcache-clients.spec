Name:      emi-dcache-clients
Version:   1.0.0
Release:   1%{?dist}
Summary:   EMI dCache Clients meta-package
Group:     Applications/Internet
URL:       http://www.dcache.org
License:   LGPLv3
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires:  dcache-srmclient
Requires:  dcap

%description
Suite of dCache clients and APIs 

Users and applications can use this suite to access 
dCache and other storage elements.

%prep
# Nothing to do

%build
# Nothing to do

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)

%changelog
* Mon Nov 12 2012 Christian Bernardt <christian.bernardt@desy.de> - 1.0.0-1
- EMI-3 version of dcache-clients metapackage
* Mon Apr 04 2011 Christian Bernardt <christian.bernardt@desy.de> - 1.0.0-0
- First version for EMI

