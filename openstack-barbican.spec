%{!?sources_gpg: %{!?dlrn:%global sources_gpg 1} }
%global sources_gpg_sign 0x2426b928085a020d8a90d0d879ab7008d0896c8a
%global service barbican

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
# we are excluding some BRs from automatic generator
%global excluded_brs doc8 bandit pre-commit hacking flake8-import-order sphinx openstackdocstheme

Name:    openstack-barbican
Version: XXX
Release: XXX
Summary: OpenStack Barbican Key Manager

Group:   Applications/System
License: Apache-2.0
Url:     https://github.com/openstack/barbican
Source0: https://tarballs.openstack.org/%{service}/%{service}-%{upstream_version}.tar.gz

# TODO: Submit PR to add these to upstream
Source1: openstack-barbican-api.service
Source2: openstack-barbican-worker.service
Source3: openstack-barbican-keystone-listener.service
Source4: gunicorn-config.py
Source5: openstack-barbican-retry.service
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
Source101:        https://tarballs.openstack.org/%{service}/%{service}-%{upstream_version}.tar.gz.asc
Source102:        https://releases.openstack.org/_static/%{sources_gpg_sign}.txt
%endif

BuildArch: noarch

# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
BuildRequires:  /usr/bin/gpgv2
%endif
BuildRequires: python3-devel
BuildRequires: pyproject-rpm-macros
BuildRequires: openstack-macros

Requires(pre): shadow-utils
BuildRequires: systemd

%{?systemd_ordering}

Requires: openstack-barbican-api = %{version}-%{release}
Requires: openstack-barbican-worker = %{version}-%{release}

%description -n openstack-barbican
Openstack Barbican provides a ReST API for securely storing,
provisioning and managing secrets. It is aimed at being
useful for all environments, including large ephemeral Clouds.
Clients can generate various types of secrets like symmetric
and asymmetric keys, passphrases and binary data.  This package
installs both the API and worker packages.

%package -n python3-barbican
Summary: All python modules of Barbican
%description -n python3-barbican
This package contains the barbican python library.
It is required by both the API(openstack-barbican) and
worker(openstack-barbican-worker) packages.


%package -n openstack-barbican-api
Summary: Barbican Key Manager API daemon
Requires: openstack-barbican-common = %{version}-%{release}
Requires: python3-gunicorn

%description -n openstack-barbican-api
This package contains scripts to start a barbican api instance.


%package -n openstack-barbican-worker
Summary: Barbican Key Manager worker daemon
Requires: openstack-barbican-common = %{version}-%{release}

%description -n openstack-barbican-worker
This package contains scripts to start a barbican worker
on a worker node.


%package -n openstack-barbican-keystone-listener
Summary: Barbican Keystone Listener daemon
Requires: python3-barbican = %{version}-%{release}

%description -n openstack-barbican-keystone-listener
This package contains scripts to start a barbican keystone
listener daemon.


%package -n openstack-barbican-retry
Summary: Barbican Retry daemon
Requires: python3-barbican = %{version}-%{release}

%description -n openstack-barbican-retry
This package contains scripts to start a barbican retry
daemon.


%package -n openstack-barbican-common
Summary: Common Files for the API and worker packages
Requires: python3-barbican = %{version}-%{release}

%description -n openstack-barbican-common
This packge contains files that are common to the API and
worker packages.


%package -n python3-barbican-tests
Summary:        Barbican tests
Requires:       python3-barbican = %{version}-%{release}

%description -n python3-barbican-tests
This package contains the Barbican test files.

%prep
# Required for tarball sources verification
%if 0%{?sources_gpg} == 1
%{gpgverify}  --keyring=%{SOURCE102} --signature=%{SOURCE101} --data=%{SOURCE0}
%endif
%setup -q -n barbican-%{upstream_version}


# make doc build compatible with python-oslo-sphinx RPM
sed -i 's/oslosphinx/oslo.sphinx/' doc/source/conf.py

sed -i /^[[:space:]]*-c{env:.*_CONSTRAINTS_FILE.*/d tox.ini
sed -i "s/^deps = -c{env:.*_CONSTRAINTS_FILE.*/deps =/" tox.ini
sed -i /^minversion.*/d tox.ini
sed -i /^requires.*virtualenv.*/d tox.ini

rm -f barbican/tests/test_hacking.py

# Exclude some bad-known BRs
for pkg in %{excluded_brs}; do
  for reqfile in doc/requirements.txt test-requirements.txt; do
    if [ -f $reqfile ]; then
      sed -i /^${pkg}.*/d $reqfile
    fi
  done
done

%generate_buildrequires
%pyproject_buildrequires -t -e %{default_toxenv}

%build
%pyproject_wheel

%install
%pyproject_install
# Generate config file
PYTHONPATH="%{buildroot}/%{python3_sitelib}" oslo-config-generator-3 --config-file=etc/oslo-config-generator/barbican.conf

mkdir -p %{buildroot}%{_sysconfdir}/barbican
mkdir -p %{buildroot}%{_sysconfdir}/barbican/vassals
mkdir -p %{buildroot}%{_localstatedir}/l{ib,og}/barbican
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_localstatedir}/run/barbican
mkdir -p %{buildroot}/%{python3_sitelib}/barbican/model/migration/alembic_migrations/versions

install -m 644 barbican/api/app.wsgi %{buildroot}/%{python3_sitelib}/barbican/api/app.wsgi
install -m 644 barbican/model/migration/alembic.ini %{buildroot}/%{python3_sitelib}/barbican/model/migration/alembic.ini
install -m 644 barbican/model/migration/alembic_migrations/versions/* %{buildroot}/%{python3_sitelib}/barbican/model/migration/alembic_migrations/versions/
install -m 640 etc/barbican/*.conf %{buildroot}%{_sysconfdir}/barbican/
install -m 640 etc/barbican/barbican.conf.sample %{buildroot}%{_sysconfdir}/barbican/barbican.conf
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
install -p -D -m 644 %{SOURCE5} %{buildroot}%{_unitdir}/openstack-barbican-retry.service

# install log rotation
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -m644 etc/logrotate.d/barbican-api %{buildroot}%{_sysconfdir}/logrotate.d/barbican-api


%pre -n openstack-barbican-common
# Add the 'barbican' user
getent group barbican >/dev/null || groupadd -r barbican
getent passwd barbican >/dev/null || \
    useradd -r -g barbican -d %{_localstatedir}/lib/barbican -s /sbin/nologin \
    -c "Barbican Key Manager user account." barbican
# Needed for thales hsm
getent group nfast >/dev/null || groupadd --force --gid 42481 nfast
getent passwd nfast >/dev/null || \
    useradd -r -g nfast -M -s /sbin/nologin \
    -c "Thales HSM user account." --uid 42481 \
    --gid 42481 nfast && \
    usermod --append --groups nfast barbican
exit 0

%check
%tox -e %{default_toxenv}

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
%config(noreplace) %attr(0640, root, %{service}) %{_sysconfdir}/barbican/barbican.conf
# Move the logrotate file to the shared package because everything currently uses
# the /var/log/barbican-api.log file, and really a single logrotate is probably
# good in the long run anyway, so this is likely the best package for it
%config(noreplace) %{_sysconfdir}/logrotate.d/barbican-api
%dir %attr(-,barbican,barbican) %{_localstatedir}/lib/barbican

%files -n python3-barbican
%license LICENSE
%{python3_sitelib}/barbican
%{python3_sitelib}/barbican*.dist-info
%exclude %{python3_sitelib}/barbican/tests

%files -n python3-barbican-tests
%license LICENSE
%{python3_sitelib}/barbican/tests

%files -n openstack-barbican-api
%config(noreplace) %attr(0640, root, %{service}) %{_sysconfdir}/barbican/api_audit_map.conf
%config(noreplace) %{_sysconfdir}/barbican/barbican-api-paste.ini
%config(noreplace) %attr(0640, root, %{service}) %{_sysconfdir}/barbican/barbican-functional.conf
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

%files -n openstack-barbican-retry
%attr(0755,root,root) %{_bindir}/barbican-retry
%{_unitdir}/openstack-barbican-retry.service

%post -n openstack-barbican-common
# update old installations
if [ $1 == 2 ] ; then
chown root:barbican %{_sysconfdir}/barbican/barbican.conf
chmod 640 %{_sysconfdir}/barbican/barbican.conf
fi

%post -n openstack-barbican-api
# update old installations
if [ $1 == 2 ] ; then
chown root:barbican %{_sysconfdir}/barbican/api_audit_map.conf
chmod 640 %{_sysconfdir}/barbican/api_audit_map.conf
chown root:barbican %{_sysconfdir}/barbican/barbican-functional.conf
chmod 640 %{_sysconfdir}/barbican/barbican-functional.conf
fi
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

%post -n openstack-barbican-retry
# ensure that init system recognizes the service
%systemd_post openstack-barbican-retry.service
/bin/systemctl daemon-reload

%preun -n openstack-barbican-api
%systemd_preun openstack-barbican-api.service

%preun -n openstack-barbican-worker
%systemd_preun openstack-barbican-worker.service

%preun -n openstack-barbican-keystone-listener
%systemd_preun openstack-barbican-keystone-listener.service

%preun -n openstack-barbican-retry
%systemd_preun openstack-barbican-retry.service

%postun -n openstack-barbican-api
%systemd_postun_with_restart openstack-barbican-api.service

%postun -n openstack-barbican-worker
%systemd_postun_with_restart openstack-barbican-worker.service

%postun -n openstack-barbican-keystone-listener
%systemd_postun_with_restart openstack-barbican-keystone-listener.service

%postun -n openstack-barbican-retry
%systemd_postun_with_restart openstack-barbican-retry.service

%changelog
