%define lpylib gridmetrics
%define rpm_install_dir /usr/share/nagios/plugins/contrib/srm
%define config_dir /usr/local/nagios/etc/objects/
%define etcdir /etc/gridmon
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define pylib %{python_sitelib}/%{lpylib}


Summary: EMI SRM nagios probes
Name: emi.dcache.srm-probes
Version: 1.0.1
Release: 1%{?dist}

License: ASL 2.0
Group: Network/Monitoring
Source0: %{name}-%{version}.tgz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires: python >= 2.4
#Requires: python-GridMon >= 1.1.10
Requires: lcg-util-python
Requires: gfal-python
Requires: lcg-util
BuildArch: noarch
BuildRequires: python >= 2.4

%description
Contains the following Nagios probes:
SRM-probe packaged by dCache

%prep
%setup -q
%build

%install

%{__rm} -rf %{buildroot}
echo "Current Directory:" `pwd`
echo "Creating BUILDROOT DIR" %{buildroot}%{rpm_install_dir}
install --directory %{buildroot}%{rpm_install_dir}
install --directory %{buildroot}%{config_dir}
install --mode 755 ../setup.py %{buildroot}%{rpm_install_dir}/
install --mode 755 SRM-probe  %{buildroot}%{rpm_install_dir}/
install -d --mode 755 gridmetrics %{buildroot}%{rpm_install_dir}/gridmetrics
cp -r gridmetrics/* %{buildroot}%{rpm_install_dir}/gridmetrics/
cp ../CHANGES %{buildroot}%{rpm_install_dir}
cp ../README %{buildroot}%{rpm_install_dir}
install --directory %{buildroot}%{pylib}
install --mode 644 %{lpylib}/*.py* %{buildroot}%{pylib}
%{__python} ../setup.py install_lib -O1 --skip-build --build-dir=%{lpylib} --install-dir=%{buildroot}%{pylib}


%post

%preun
rm -rf %{rpm_install_dir}/gridmetrics

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{rpm_install_dir}/SRM-probe
%{rpm_install_dir}/setup.py*
%{rpm_install_dir}/gridmetrics
%{pylib}/*.py*


%doc %{rpm_install_dir}/README
%doc %{rpm_install_dir}/CHANGES

%changelog
* Mon Oct 6 2014 Karsten Schwank <karsten.schwank@desy.de> - 1.0.1-1
- blacklist webdav, http, https protocols from SRM-GetTURL probe
* Fri Dec 4 2012 Christian Bernardt <christian.bernardt@desy.de> - 1.0.0-1
- EMI-3 release that includes dependencies to lcg-util-python, gfal-python, lcg-util

