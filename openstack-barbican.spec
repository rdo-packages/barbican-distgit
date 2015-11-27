%global release_name liberty
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:    openstack-barbican
Version: 1.0.0
Release: 1%{?dist}
Summary: OpenStack Barbican Key Manager

License: ASL 2.0
Url:     https://github.com/openstack/barbican
Source0: https://launchpad.net/barbican/%{release_name}/%{version}/+download/barbican-%{upstream_version}.tar.gz

# TODO: Submit PR to add these to upstream
Source1: openstack-barbican-api.service
Source2: openstack-barbican-worker.service
Source3: openstack-barbican-keystone-listener.service
Source4: gunicorn-config.py

BuildArch: noarch
BuildRequires: crudini
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-oslo-config
BuildRequires: python-oslo-messaging
BuildRequires: python-pbr

Requires(pre): shadow-utils
Requires: python-gunicorn
Requires: python-barbican
%if 0%{?el6}
Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
%else
Requires(post): systemd
Requires(preun): systemd
Requires(preun): systemd
BuildRequires: systemd
%endif

%description -n openstack-barbican
Openstack Barbican provides a ReST API for securely storing,
provisioning and managing secrets. It is aimed at being
useful for all environments, including large ephemeral Clouds.
Clients can generate various types of secrets like symmetric
and asymmetric keys, passphrases and binary data.


%package -n python-barbican
Summary: All python modules of Barbican
Requires: python-alembic
Requires: python-babel
Requires: python-crypto
Requires: python-cryptography
Requires: python-eventlet
Requires: python-iso8601
Requires: python-jsonschema
Requires: python-kombu

%if 0%{?fedora} >= 23
Requires: python-ldap3
%endif

Requires: python-netaddr
Requires: python-oslo-config
Requires: python-oslo-messaging
Requires: python-oslo-policy
Requires: python-paste
Requires: python-paste-deploy
Requires: python-pbr
Requires: python-pecan
Requires: python-six
Requires: python-sqlalchemy
Requires: python-stevedore
Requires: python-webob

%description -n python-barbican
This package contains the barbican python library.
It is required by both the API(openstack-barbican) and
worker(openstack-barbican-worker) packages.


%package -n openstack-barbican-api
Summary: Barbican Key Manager API daemon
Requires: python-barbican

%description -n openstack-barbican-api
This package contains scripts to start a barbican api instance.


%package -n openstack-barbican-worker
Summary: Barbican Key Manager worker daemon
Requires: python-barbican
# Todo for now we rely on the -api package because of a shared config file
Requires: openstack-barbican-api

%description -n openstack-barbican-worker
This package contains scripts to start a barbican worker
on a worker node.


%package -n openstack-barbican-keystone-listener
Summary: Barbican Keystone Listener daemon
Requires: python-barbican

%description -n openstack-barbican-keystone-listener
This package contains scripts to start a barbican keystone
listener daemon.


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
PBR_VERSION=%{version}%{?version_milestone} %{__python2} setup.py install --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_sysconfdir}/barbican
mkdir -p %{buildroot}%{_sysconfdir}/barbican/vassals
mkdir -p %{buildroot}%{_localstatedir}/l{ib,og}/barbican
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}/run/barbican


install -m 644 etc/barbican/*.{json,ini,conf} %{buildroot}%{_sysconfdir}/barbican/
install -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/barbican/gunicorn-config.py
install -m 644 etc/barbican/vassals/* %{buildroot}%{_sysconfdir}/barbican/vassals/

# Use crudini to modify barbican-api-paste.ini for gunicorn
crudini --set %{buildroot}%{_sysconfdir}/barbican/barbican-api-paste.ini server:main use egg:gunicorn#main

# Remove the bash script since its more dev focused
rm -f %{buildroot}%{_bindir}/barbican.sh

%if 0%{?el6}
# upstart services
mkdir -p %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-api.conf %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-worker.conf %{buildroot}%{_sysconfdir}/init
install -m 644 etc/init/barbican-keystone-listener.conf %{buildroot}%{_sysconfdir}/init
%else
# systemd services
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/openstack-barbican-api.service
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-barbican-worker.service
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_unitdir}/openstack-barbican-keystone-listener.service
%endif

# install log rotation
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m644 etc/logrotate.d/barbican-api %{buildroot}%{_sysconfdir}/logrotate.d/barbican-api


%pre
# Add the 'barbican' user
getent group barbican >/dev/null || groupadd -r barbican
getent passwd barbican >/dev/null || \
    useradd -r -g barbican -d %{_localstatedir}/lib/barbican -s /sbin/nologin \
    -c "Barbican Key Manager user account." barbican
exit 0


%files -n openstack-barbican
%doc LICENSE
%dir %attr(0775,root,barbican) %{_sysconfdir}/barbican
%dir %attr(-,barbican,barbican) %{_localstatedir}/log/barbican
%dir %attr(-,barbican,barbican) /run/barbican
%attr(0755,root,root) %{_bindir}/barbican-db-manage
# Move the logrotate file to the shared package because everything currently uses
# the /var/log/barbican-api.log file, and really a single logrotate is probably
# good in the long run anyway, so this is likely the best package for it
%config(noreplace) %{_sysconfdir}/logrotate.d/barbican-api

%files -n python-barbican
%doc LICENSE
%defattr(-,barbican,barbican)
%{_bindir}/barbican-retry
%{_bindir}/pkcs11-kek-rewrap
%{python2_sitelib}/barbican
%{python2_sitelib}/barbican-*-py?.?.egg-info
%dir %attr(-,barbican,barbican) %{_localstatedir}/lib/barbican

%files -n openstack-barbican-api
%config(noreplace) %{_sysconfdir}/barbican/barbican-api-paste.ini
%config(noreplace) %{_sysconfdir}/barbican/barbican.conf
%config(noreplace) %{_sysconfdir}/barbican/barbican-functional.conf
%config(noreplace) %{_sysconfdir}/barbican/gunicorn-config.py
%exclude %{_sysconfdir}/barbican/gunicorn-config.pyc
%exclude %{_sysconfdir}/barbican/gunicorn-config.pyo
%config(noreplace) %{_sysconfdir}/barbican/policy.json
%config(noreplace) %{_sysconfdir}/barbican/vassals/barbican-api.ini
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-api.conf
%else
%{_unitdir}/openstack-barbican-api.service
%endif

%files -n openstack-barbican-worker
%doc LICENSE
%defattr(-,root,root)
%dir %attr(0775,root,barbican) %{_sysconfdir}/barbican
%dir %attr(-,barbican,barbican) %{_localstatedir}/log/barbican
%attr(0755,root,root) %{_bindir}/barbican-worker
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-worker.conf
%else
%{_unitdir}/openstack-barbican-worker.service
%endif

%files -n openstack-barbican-keystone-listener
%doc LICENSE
%attr(0755,root,root) %{_bindir}/barbican-keystone-listener
%if 0%{?el6}
%config(noreplace) %{_sysconfdir}/init/barbican-keystone-listener.conf
%else
%{_unitdir}/openstack-barbican-keystone-listener.service
%endif

%post -n openstack-barbican-api
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
%systemd_post openstack-barbican-api.service
/bin/systemctl daemon-reload
%endif

%post -n openstack-barbican-worker
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
%systemd_post openstack-barbican-worker.service
/bin/systemctl daemon-reload
%endif

%post -n openstack-barbican-keystone-listener
# ensure that init system recognizes the service
%if 0%{?el6}
/sbin/initctl reload-configuration
%else
%systemd_post openstack-barbican-keystone-listener.service
/bin/systemctl daemon-reload
%endif

%preun -n openstack-barbican-api
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-api >/dev/null 2>&1 || :
fi
%else
%systemd_preun openstack-barbican-api.service
%endif

%preun -n openstack-barbican-worker
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-worker >/dev/null 2>&1 || :
fi
%else
%systemd_preun openstack-barbican-worker.service
%endif

%preun -n openstack-barbican-keystone-listener
%if 0%{?el6}
if [ $1 -eq 0 ] ; then
    # This is package removal, not upgrade
    /sbin/stop barbican-keystone-listener >/dev/null 2>&1 || :
fi
%else
%systemd_preun openstack-barbican-keystone-listener.service
%endif

%if 0%{?rhel} != 6
%postun -n openstack-barbican-api
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-api.service

%postun -n openstack-barbican-worker
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-worker.service

%postun -n openstack-barbican-keystone-listener
# Restarting on EL6 is left as a task to the admin
%systemd_postun_with_restart openstack-barbican-keystone-listender.service
%endif


%changelog
* Fri Nov 27 2015 Haïkel Guémar <hguemar@fedoraproject.org> - 1.0.0-1
- Initial release

