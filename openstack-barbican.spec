%global service barbican

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:    openstack-barbican
Version: XXX
Release: XXX
Summary: OpenStack Barbican Key Manager

Group:   Applications/System
License: ASL 2.0
Url:     https://github.com/openstack/barbican
Source0: https://tarballs.openstack.org/%{service}/%{service}-%{upstream_version}.tar.gz

# TODO: Submit PR to add these to upstream
Source1: openstack-barbican-api.service
Source2: openstack-barbican-worker.service
Source3: openstack-barbican-keystone-listener.service
Source4: gunicorn-config.py

BuildArch: noarch
BuildRequires: crudini
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-oslo-config > 2:3.7.0
BuildRequires: python-oslo-messaging >= 4.0.0
BuildRequires: python-pbr >= 1.6

Requires(pre): shadow-utils
Requires: python-barbican
Requires(post): systemd
Requires(preun): systemd
Requires(preun): systemd
BuildRequires: systemd

Requires: openstack-barbican-api
Requires: openstack-barbican-worker

%description -n openstack-barbican
Openstack Barbican provides a ReST API for securely storing,
provisioning and managing secrets. It is aimed at being
useful for all environments, including large ephemeral Clouds.
Clients can generate various types of secrets like symmetric
and asymmetric keys, passphrases and binary data.  This package
installs both the API and worker packages.

%package -n python-barbican
Summary: All python modules of Barbican
Requires: python-alembic >= 0.8.4
Requires: python-babel >= 2.3.4
Requires: python-cffi
Requires: python-crypto >= 2.6
Requires: python-cryptography >= 1.0
Requires: python-eventlet >= 0.18.2
Requires: python-iso8601
Requires: python-jsonschema
Requires: python-keystonemiddleware >= 4.0.0
Requires: python-kombu
Requires: python-ldap3
Requires: python-netaddr
Requires: python-oslo-concurrency >= 3.5.0
Requires: python-oslo-config >= 2:3.14.0
Requires: python-oslo-context >= 2.9.0
Requires: python-oslo-i18n >= 2.1.0
Requires: python-oslo-log >= 1.14.0
Requires: python-oslo-messaging >= 5.2.0
Requires: python-oslo-middleware >= 3.0.0
Requires: python-oslo-policy >= 1.9.0
Requires: python-oslo-serialization >= 1.10.0
Requires: python-oslo-service >= 1.10.0
Requires: python-oslo-utils >= 3.16.0
Requires: python-paste
Requires: python-paste-deploy >= 1.5.0
Requires: python-pbr >= 1.6
Requires: python-pecan >= 1.0.0
Requires: python-pycadf >= 1.1.0
Requires: python-six >= 1.9.0
Requires: python-sqlalchemy >= 1.0.10
Requires: python-stevedore >= 1.16.0
Requires: python-webob >= 1.2.3

%description -n python-barbican
This package contains the barbican python library.
It is required by both the API(openstack-barbican) and
worker(openstack-barbican-worker) packages.


%package -n openstack-barbican-api
Summary: Barbican Key Manager API daemon
Requires: openstack-barbican-common
Requires: python-gunicorn

%description -n openstack-barbican-api
This package contains scripts to start a barbican api instance.


%package -n openstack-barbican-worker
Summary: Barbican Key Manager worker daemon
Requires: openstack-barbican-common

%description -n openstack-barbican-worker
This package contains scripts to start a barbican worker
on a worker node.


%package -n openstack-barbican-keystone-listener
Summary: Barbican Keystone Listener daemon
Requires: python-barbican

%description -n openstack-barbican-keystone-listener
This package contains scripts to start a barbican keystone
listener daemon.

%package -n openstack-barbican-common
Summary: Common Files for the API and worker packages
Requires: python-barbican

%description -n openstack-barbican-common
This packge contains files that are common to the API and
worker packages.

%package -n python-barbican-tests
Summary:        Barbican tests
Requires:       python-barbican = %{version}-%{release}

%description -n python-barbican-tests
This package contains the Barbican test files.

%prep
%setup -q -n barbican-%{upstream_version}

rm -rf barbican.egg-info

# make doc build compatible with python-oslo-sphinx RPM
sed -i 's/oslosphinx/oslo.sphinx/' doc/source/conf.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requiers_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_sysconfdir}/barbican
mkdir -p %{buildroot}%{_sysconfdir}/barbican/vassals
mkdir -p %{buildroot}%{_localstatedir}/l{ib,og}/barbican
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_localstatedir}/run/barbican
mkdir -p %{buildroot}/%{python2_sitelib}/barbican/model/migration/alembic_migrations/versions

install -m 644 barbican/api/app.wsgi %{buildroot}/%{python2_sitelib}/barbican/api/app.wsgi
install -m 644 barbican/model/migration/alembic.ini %{buildroot}/%{python2_sitelib}/barbican/model/migration/alembic.ini
install -m 644 barbican/model/migration/alembic_migrations/versions/* %{buildroot}/%{python2_sitelib}/barbican/model/migration/alembic_migrations/versions/
install -m 644 etc/barbican/*.{json,ini,conf} %{buildroot}%{_sysconfdir}/barbican/
install -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/barbican/gunicorn-config.py
install -m 644 etc/barbican/vassals/* %{buildroot}%{_sysconfdir}/barbican/vassals/

# Use crudini to modify barbican-api-paste.ini for gunicorn
crudini --set %{buildroot}%{_sysconfdir}/barbican/barbican-api-paste.ini server:main use egg:gunicorn#main

# Remove the bash script since its more dev focused
rm -f %{buildroot}%{_bindir}/barbican.sh

# systemd services
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/openstack-barbican-api.service
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-barbican-worker.service
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_unitdir}/openstack-barbican-keystone-listener.service

# install log rotation
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m644 etc/logrotate.d/barbican-api %{buildroot}%{_sysconfdir}/logrotate.d/barbican-api


%pre -n openstack-barbican-common
# Add the 'barbican' user
getent group barbican >/dev/null || groupadd -r barbican
getent passwd barbican >/dev/null || \
    useradd -r -g barbican -d %{_localstatedir}/lib/barbican -s /sbin/nologin \
    -c "Barbican Key Manager user account." barbican
exit 0

%files -n openstack-barbican
%license LICENSE

%files -n openstack-barbican-common
%dir %attr(0775,root,barbican) %{_sysconfdir}/barbican
%dir %attr(-,barbican,barbican) %{_localstatedir}/log/barbican
%dir %attr(-,barbican,barbican) %{_localstatedir}/run/barbican
%attr(0755,root,root) %{_bindir}/barbican-db-manage
%{_bindir}/barbican-manage
%{_bindir}/barbican-retry
%{_bindir}/pkcs11-kek-rewrap
%{_bindir}/pkcs11-key-generation
# Move the logrotate file to the shared package because everything currently uses
# the /var/log/barbican-api.log file, and really a single logrotate is probably
# good in the long run anyway, so this is likely the best package for it
%config(noreplace) %{_sysconfdir}/logrotate.d/barbican-api
%dir %attr(-,barbican,barbican) %{_localstatedir}/lib/barbican

%files -n python-barbican
%license LICENSE
%{python2_sitelib}/barbican
%{python2_sitelib}/barbican-*-py?.?.egg-info
%exclude %{python2_sitelib}/barbican/tests

%files -n python-barbican-tests
%license LICENSE
%{python2_sitelib}/barbican/tests

%files -n openstack-barbican-api
%config(noreplace) %{_sysconfdir}/barbican/api_audit_map.conf
%config(noreplace) %{_sysconfdir}/barbican/barbican-api-paste.ini
%config(noreplace) %{_sysconfdir}/barbican/barbican.conf
%config(noreplace) %{_sysconfdir}/barbican/barbican-functional.conf
%config(noreplace) %{_sysconfdir}/barbican/gunicorn-config.py
%exclude %{_sysconfdir}/barbican/gunicorn-config.pyc
%exclude %{_sysconfdir}/barbican/gunicorn-config.pyo
%config(noreplace) %{_sysconfdir}/barbican/policy.json
%config(noreplace) %{_sysconfdir}/barbican/vassals/barbican-api.ini
%{_unitdir}/openstack-barbican-api.service

%files -n openstack-barbican-worker
%defattr(-,root,root)
%attr(0755,root,root) %{_bindir}/barbican-worker
%{_unitdir}/openstack-barbican-worker.service

%files -n openstack-barbican-keystone-listener
%attr(0755,root,root) %{_bindir}/barbican-keystone-listener
%{_unitdir}/openstack-barbican-keystone-listener.service

%post -n openstack-barbican-api
# ensure that init system recognizes the service
%systemd_post openstack-barbican-api.service
/bin/systemctl daemon-reload

%post -n openstack-barbican-worker
# ensure that init system recognizes the service
%systemd_post openstack-barbican-worker.service
/bin/systemctl daemon-reload

%post -n openstack-barbican-keystone-listener
# ensure that init system recognizes the service
%systemd_post openstack-barbican-keystone-listener.service
/bin/systemctl daemon-reload

%preun -n openstack-barbican-api
%systemd_preun openstack-barbican-api.service

%preun -n openstack-barbican-worker
%systemd_preun openstack-barbican-worker.service

%preun -n openstack-barbican-keystone-listener
%systemd_preun openstack-barbican-keystone-listener.service

%postun -n openstack-barbican-api
%systemd_postun_with_restart openstack-barbican-api.service

%postun -n openstack-barbican-worker
%systemd_postun_with_restart openstack-barbican-worker.service

%postun -n openstack-barbican-keystone-listener
%systemd_postun_with_restart openstack-barbican-keystone-listender.service


%changelog
# REMOVEME: error caused by commit http://git.openstack.org/cgit/openstack/barbican/commit/?id=8e1846fafff2adb991237352faa5871085ed9b5d
