%global milestone .0rc1
# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver %{python3_pkgversion}
%else
%global pyver 2
%endif
%global pyver_bin python%{pyver}
%global pyver_sitelib %python%{pyver}_sitelib
%global pyver_install %py%{pyver}_install
%global pyver_build %py%{pyver}_build
# End of macros for py2/py3 compatibility
%global service barbican

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:    openstack-barbican
Version: 8.0.0
Release: 0.1%{?milestone}%{?dist}
Summary: OpenStack Barbican Key Manager

Group:   Applications/System
License: ASL 2.0
Url:     https://github.com/openstack/barbican
Source0: https://tarballs.openstack.org/%{service}/%{service}-%{upstream_version}.tar.gz

#
# patches_base=8.0.0.0rc1
#

# TODO: Submit PR to add these to upstream
Source1: openstack-barbican-api.service
Source2: openstack-barbican-worker.service
Source3: openstack-barbican-keystone-listener.service
Source4: gunicorn-config.py

BuildArch: noarch
BuildRequires: python%{pyver}-devel
BuildRequires: python%{pyver}-setuptools
BuildRequires: python%{pyver}-oslo-config >= 2:5.2.0
BuildRequires: python%{pyver}-oslo-messaging >= 5.29.0
BuildRequires: python%{pyver}-pbr >= 2.0.0
BuildRequires: python%{pyver}-pecan
BuildRequires: python%{pyver}-alembic
BuildRequires: python%{pyver}-pykmip
BuildRequires: python%{pyver}-oslo-policy
BuildRequires: python%{pyver}-oslo-db
BuildRequires: python%{pyver}-oslo-upgradecheck
BuildRequires: python%{pyver}-keystonemiddleware
BuildRequires: openstack-macros

Requires(pre): shadow-utils
Requires: python%{pyver}-barbican
BuildRequires: systemd
%if 0%{?rhel} && 0%{?rhel} < 8
%{?systemd_requires}
%else
%{?systemd_ordering} # does not exist on EL7
%endif

Requires: openstack-barbican-api
Requires: openstack-barbican-worker

%description -n openstack-barbican
Openstack Barbican provides a ReST API for securely storing,
provisioning and managing secrets. It is aimed at being
useful for all environments, including large ephemeral Clouds.
Clients can generate various types of secrets like symmetric
and asymmetric keys, passphrases and binary data.  This package
installs both the API and worker packages.

%package -n python%{pyver}-barbican
Summary: All python modules of Barbican
%{?python_provide:%python_provide python%{pyver}-barbican}
Requires: python%{pyver}-alembic >= 0.8.10
Requires: python%{pyver}-babel >= 2.3.4
Requires: python%{pyver}-cryptography >= 2.1
Requires: python%{pyver}-eventlet >= 0.18.2
Requires: python%{pyver}-jsonschema
Requires: python%{pyver}-keystonemiddleware >= 4.17.0
Requires: python%{pyver}-ldap3
Requires: python%{pyver}-oslo-config >= 2:5.2.0
Requires: python%{pyver}-oslo-context >= 2.19.2
Requires: python%{pyver}-oslo-db >= 4.27.0
Requires: python%{pyver}-oslo-i18n >= 3.15.3
Requires: python%{pyver}-oslo-log >= 3.36.0
Requires: python%{pyver}-oslo-messaging >= 5.29.0
Requires: python%{pyver}-oslo-middleware >= 3.31.0
Requires: python%{pyver}-oslo-policy >= 1.30.0
Requires: python%{pyver}-oslo-serialization >= 2.18.0
Requires: python%{pyver}-oslo-service >= 1.24.0
Requires: python%{pyver}-oslo-upgradecheck >= 0.1.1
Requires: python%{pyver}-oslo-utils >= 3.33.0
Requires: python%{pyver}-pbr >= 2.0.0
Requires: python%{pyver}-pecan >= 1.0.0
Requires: python%{pyver}-six >= 1.10.0
Requires: python%{pyver}-sqlalchemy >= 1.0.10
Requires: python%{pyver}-stevedore >= 1.20.0
Requires: python%{pyver}-webob >= 1.7.1
Requires: python%{pyver}-pyOpenSSL >= 17.1.0
Requires: python%{pyver}-castellan >=  0.17
Requires: python%{pyver}-oslo-versionedobjects >= 1.31.2

# Handle python2 exception
%if %{pyver} == 2
Requires: python-cffi
Requires: python-paste
Requires: python-paste-deploy >= 1.5.0
%else
Requires: python%{pyver}-cffi
Requires: python%{pyver}-paste
Requires: python%{pyver}-paste-deploy >= 1.5.0
%endif

%description -n python%{pyver}-barbican
This package contains the barbican python library.
It is required by both the API(openstack-barbican) and
worker(openstack-barbican-worker) packages.


%package -n openstack-barbican-api
Summary: Barbican Key Manager API daemon
Requires: openstack-barbican-common
Requires: python%{pyver}-gunicorn

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
Requires: python%{pyver}-barbican

%description -n openstack-barbican-keystone-listener
This package contains scripts to start a barbican keystone
listener daemon.

%package -n openstack-barbican-common
Summary: Common Files for the API and worker packages
Requires: python%{pyver}-barbican

%description -n openstack-barbican-common
This packge contains files that are common to the API and
worker packages.

%package -n python%{pyver}-barbican-tests
Summary:        Barbican tests
%{?python_provide:%python_provide python%{pyver}-barbican-tests}
Requires:       python%{pyver}-barbican = %{version}-%{release}

%description -n python%{pyver}-barbican-tests
This package contains the Barbican test files.

%prep
%setup -q -n barbican-%{upstream_version}

rm -rf barbican.egg-info

# make doc build compatible with python-oslo-sphinx RPM
sed -i 's/oslosphinx/oslo.sphinx/' doc/source/conf.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requiers_dist config
%py_req_cleanup

%build
%{pyver_build}
PYTHONPATH=. oslo-config-generator-%{pyver} --config-file=etc/oslo-config-generator/barbican.conf

%install
%{pyver_install}
mkdir -p %{buildroot}%{_sysconfdir}/barbican
mkdir -p %{buildroot}%{_sysconfdir}/barbican/vassals
mkdir -p %{buildroot}%{_localstatedir}/l{ib,og}/barbican
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_localstatedir}/run/barbican
mkdir -p %{buildroot}/%{pyver_sitelib}/barbican/model/migration/alembic_migrations/versions

install -m 644 barbican/api/app.wsgi %{buildroot}/%{pyver_sitelib}/barbican/api/app.wsgi
install -m 644 barbican/model/migration/alembic.ini %{buildroot}/%{pyver_sitelib}/barbican/model/migration/alembic.ini
install -m 644 barbican/model/migration/alembic_migrations/versions/* %{buildroot}/%{pyver_sitelib}/barbican/model/migration/alembic_migrations/versions/
install -m 644 etc/barbican/*.conf %{buildroot}%{_sysconfdir}/barbican/
install -m 644 etc/barbican/barbican.conf.sample %{buildroot}%{_sysconfdir}/barbican/barbican.conf
install -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/barbican/gunicorn-config.py
install -m 644 etc/barbican/vassals/* %{buildroot}%{_sysconfdir}/barbican/vassals/

# Move files installed under /usr/etc
mv %{buildroot}/usr/etc/barbican/* %{buildroot}%{_sysconfdir}/barbican/
rmdir %{buildroot}/usr/etc/barbican

# Modify barbican-api-paste.ini for gunicorn
echo '[server:main]' >> %{buildroot}%{_sysconfdir}/barbican/barbican-api-paste.ini
echo 'use = egg:gunicorn#main' >> %{buildroot}%{_sysconfdir}/barbican/barbican-api-paste.ini

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
%dir %attr(0750,barbican,barbican) %{_localstatedir}/log/barbican
%dir %attr(-,barbican,barbican) %{_localstatedir}/run/barbican
%attr(0755,root,root) %{_bindir}/barbican-db-manage
%{_bindir}/barbican-manage
%{_bindir}/barbican-retry
%{_bindir}/barbican-status
%{_bindir}/pkcs11-kek-rewrap
%{_bindir}/pkcs11-key-generation
# Move the logrotate file to the shared package because everything currently uses
# the /var/log/barbican-api.log file, and really a single logrotate is probably
# good in the long run anyway, so this is likely the best package for it
%config(noreplace) %{_sysconfdir}/logrotate.d/barbican-api
%dir %attr(-,barbican,barbican) %{_localstatedir}/lib/barbican

%files -n python%{pyver}-barbican
%license LICENSE
%{pyver_sitelib}/barbican
%{pyver_sitelib}/barbican-*-py?.?.egg-info
%exclude %{pyver_sitelib}/barbican/tests

%files -n python%{pyver}-barbican-tests
%license LICENSE
%{pyver_sitelib}/barbican/tests

%files -n openstack-barbican-api
%config(noreplace) %{_sysconfdir}/barbican/api_audit_map.conf
%config(noreplace) %{_sysconfdir}/barbican/barbican-api-paste.ini
%config(noreplace) %{_sysconfdir}/barbican/barbican.conf
%config(noreplace) %{_sysconfdir}/barbican/barbican-functional.conf
%config(noreplace) %{_sysconfdir}/barbican/gunicorn-config.py
%exclude %{_sysconfdir}/barbican/gunicorn-config.pyc
%exclude %{_sysconfdir}/barbican/gunicorn-config.pyo
%config(noreplace) %{_sysconfdir}/barbican/vassals/barbican-api.ini
%{_unitdir}/openstack-barbican-api.service
# FIXME: it'd be nice to have a wsgi config file sample in the package
%{_bindir}/barbican-wsgi-api

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
* Fri Mar 22 2019 RDO <dev@lists.rdoproject.org> 8.0.0-0.1.0rc1
- Update to 8.0.0.0rc1

