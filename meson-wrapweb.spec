%global __python %{__python3}

Name:          meson-wrapweb
Version:       0.0.1
Release:       2%{?dist}
Summary:       A web service providing downloadable Wraps

License:       ASL 2.0
URL:           https://github.com/mesonbuild/wrapweb
Source0:       https://github.com/mesonbuild/wrapweb/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:     noarch
BuildRequires: python3-devel
Requires:      python3-flask
Requires:      nginx
Requires:      uwsgi uwsgi-plugin-python3

%description
%{summary}.

%prep
%autosetup

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_datadir}/%{name}/
mkdir -p %{buildroot}%{_sysconfdir}/uwsgi.d/
mkdir -p %{buildroot}%{_sysconfdir}/nginx/conf.d/

cp -a *.py wrapweb/ %{buildroot}%{_datadir}/%{name}/
install -Dpm 0644 files/wrapdb.cfg %{buildroot}%{_sysconfdir}/%{name}.cfg
install -Dpm 0644 files/wrapdb.conf %{buildroot}%{_sysconfdir}/nginx/conf.d/%{name}.conf
install -Dpm 0644 files/wrapdb.ini %{buildroot}%{_sysconfdir}/uwsgi.d/%{name}.ini

%files
%license COPYING
%doc README.md
%config(noreplace) %{_sysconfdir}/%{name}.cfg
%config(noreplace) %{_sysconfdir}/nginx/conf.d/%{name}.conf
%attr(-,uwsgi,uwsgi)%{_datadir}/%{name}/
%config(noreplace) %attr(-,uwsgi,uwsgi)%{_sysconfdir}/uwsgi.d/%{name}.ini

%changelog
* Sun Jul 12 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> 0.0.1-2
- fix paths in confs after migration (Igor Gnatenko)

* Sun Jul 12 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com> 0.0.1-1
- Initial package
