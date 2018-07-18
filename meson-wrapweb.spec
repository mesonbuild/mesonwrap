%global __python %{__python3}
%{?python_enable_dependency_generator}

Name:          meson-wrapweb
Version:       0.0.5
Release:       1%{?dist}
Summary:       Web service providing downloadable Wraps

License:       ASL 2.0
URL:           https://github.com/mesonbuild/wrapweb
Source0:       %{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:     noarch
BuildRequires: python3-devel
BuildRequires: python3-setuptools
Requires:      nginx
Requires:      uwsgi
Requires:      uwsgi-plugin-python3

%description
%{summary}.

%prep
%autosetup -n wrapweb-%{version}

%build
%py3_build

%install
%py3_install

mkdir -p %{buildroot}%{_datadir}/%{name}/
mkdir -p %{buildroot}%{_sharedstatedir}/%{name}/
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/
mkdir -p %{buildroot}%{_sysconfdir}/uwsgi.d/
mkdir -p %{buildroot}%{_sysconfdir}/nginx/conf.d/

cp -a wrapweb/static %{buildroot}%{_datadir}/%{name}/
install -Dpm 0644 files/wrapdb.cfg %{buildroot}%{_sysconfdir}/%{name}/wrapdb.cfg
install -Dpm 0644 files/wrapdb.conf %{buildroot}%{_sysconfdir}/nginx/conf.d/%{name}.conf
install -Dpm 0644 files/wrapdb.ini %{buildroot}%{_sysconfdir}/uwsgi.d/%{name}.ini

%files
%license COPYING
%doc README.md
%{_bindir}/mesonwrap
%{python3_sitelib}/mesonwrap-*.egg-info/
%{python3_sitelib}/mesonwrap/
%{python3_sitelib}/wrapweb/
%{_datadir}/%{name}/
%dir %{_sysconfdir}/%{name}/
%config(noreplace) %{_sysconfdir}/%{name}/wrapdb.cfg
%ghost %{_sysconfdir}/%{name}/wrapdb.key
%config(noreplace) %{_sysconfdir}/nginx/conf.d/%{name}.conf
%config(noreplace) %attr(-,uwsgi,uwsgi)%{_sysconfdir}/uwsgi.d/%{name}.ini
%dir %{_sharedstatedir}/%{name}
%ghost %{_sharedstatedir}/%{name}/wrapdb.sqlite

%changelog
