%bcond_without server
%if 0%{?fedora}
%bcond_with bundled
%else
%bcond_without bundled
%endif


%global goipath         repospanner.org/repospanner
%global gcommit         7e4a11255b00b8e25e542feedb35ca957edc0763

# https://bugzilla.redhat.com/show_bug.cgi?id=995136#c12
%global _dwz_low_mem_die_limit 0

%if 0%{?fedora}
%gometa
%endif

%define dist .el7.infra

Name:           repoSpanner
Version:        0.5
Release:        1.%{gcommit}%{?dist}
Summary:        repoSpanner is a distributed Git storage server

License:        BSD
URL:            https://repospanner.org/
# git archive %%{gcommit} -o repoSpanner-%%{version}-%%{gcommit}.tar.gz --prefix repoSpanner-%%{version}/
Source0:        repoSpanner-%{version}-%{gcommit}.tar.gz
Source1:	repospanner.service

Requires: %{name}-filesystem = %{version}-%{release}

# While technically it can be build on go_arches, the golang-googlecode-goprotobuf
# library is not available on ppc64le
ExclusiveArch:  x86_64

BuildRequires: golang
BuildRequires: protobuf-compiler
BuildRequires: golang-googlecode-goprotobuf

%{?systemd_requires}
BuildRequires:	systemd

%if !%{with bundled}
%if %{with server}
BuildRequires:	golang(github.com/golang/protobuf/proto)
BuildRequires:	golang(github.com/spf13/cobra)
BuildRequires:	golang(github.com/mattn/go-sqlite3)
BuildRequires:	golang(github.com/Sirupsen/logrus)
BuildRequires:	etcd-devel
BuildRequires:	protobuf-devel
BuildRequires:  golang-googlecode-goprotobuf
BuildRequires:	golang(github.com/pkg/errors)
%endif  # Server deps

# These deps are used for both server and bridge
BuildRequires:	golang(github.com/spf13/viper)
BuildRequires:	golang(golang.org/x/net/http2)
%endif


%description
repoSpanner is a distributed Git storage server.

%package bridge
Summary:	The repoSpanner bridge
Requires: %{name}-filesystem = %{version}-%{release}

%description bridge
The repoSpanner bridge

%package filesystem
Summary:	Common filesystem paths
BuildArch:	noarch

%description filesystem
Common filesystem components


%prep
%setup -q

%build
%if !%{with bundled}
    rm -rf vendor/
%endif

# https://fedoraproject.org/wiki/PackagingDrafts/Go#Debuginfo
function gobuild {
	go build -mod vendor -a -ldflags "-B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \n') -X repospanner.org/repospanner/server/constants.version=%{version} -X repospanner.org/repospanner/server/constants.gitdescrip=%{release}" -v -x "$@";
}

%if %{with server}
    go generate ./...
    for cmd in $(ls -1 cmd) ; do
        gobuild -o $cmd %{goipath}/cmd/$cmd
    done
%else
    # Only build the bridge
    gobuild -o repobridge %{goipath}/cmd/repobridge
%endif


%install
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_sysconfdir}/repospanner
install repobridge %{buildroot}%{_libexecdir}

%if %{with server}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_unitdir}

install repospanner %{buildroot}%{_bindir}
install repohookrunner %{buildroot}%{_libexecdir}
install %{SOURCE1} %{buildroot}%{_unitdir}

%post
%systemd_post repospanner.service

%preun
%systemd_preun repospanner.service

%postun
%systemd_postun_with_restart repospanner.service

%files
%doc README.md config.yml.example
%license LICENSE
%{_bindir}/repospanner
%{_libexecdir}/repohookrunner
%{_unitdir}/repospanner.service
%endif  # with server

%files bridge
%doc bridge_config.json.example
%{_libexecdir}/repobridge

%files filesystem
%{_sysconfdir}/repospanner

%changelog
* Tue Mar 05 2019 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.5-1.7e4a11255b00b8e25e542feedb35ca957edc0763.el7.infra
- Improve hook running significantly
- Make HTTP services not run during initialization
- Allow group writing to repoSpanner files
- Allow configuring bridge CA and baseurl from environment

* Wed Feb 13 2019 Patrick Uiterwijk <puiterwijk@redhat.com> - 1.4-0.f38383546f7ce0e88ec7b9c5bf7959521af2c941
- Start moving to contexts for request info
- Add object listing to storage layer
- Optimize tree storage lister
- Default to paranoid object checking
- Return more concise error messages
- Fix lock taking for hasRepo
- Add updating for symrefs
- Add more verbose output to bridge error messages
- Add "ca info" command for certificate information
- Make state folder creation optional
- Bump version to 0.4
- Update dependencies

* Thu Nov 01 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-19.4de0303739e95661cc7a1b4324d2f91d12005d90
- Add monitor certificates

* Thu Nov 01 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-18.1fbdb7ad2cda0a4eb15a07cea94b3a8cebac8066
- Fix sending pings with snapshot in place

* Wed Oct 31 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-17.f27442a960a681768ab654c903a59ea60374860e
- Fix race condition on push

* Wed Oct 24 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-16.035a82940859adb0ff7dccb4a6391fbeb3bd833f
- Rebuilt package

* Wed Oct 24 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-15.035a82940859adb0ff7dccb4a6391fbeb3bd833f
- Some stability improvements
- Delta rebuilding is now parallel
- Peer pings added
- Nodestatus now can give a nagios summary
- Nodestatus now provides exit codes for current status

* Mon Oct 22 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-14.b211b84729037d3e5cf3e6ac3fc22ecf73612249
- Delete Git example hook files before running

* Mon Oct 22 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-13.6397e39d876a887ae6dd132ebbf5421f5b6030cd
- Make hook cloning clone everything at once

* Mon Oct 22 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-12.78687ffe6554988a038683f75e598d609e4f942c
- Run pre-receive and update hooks before waiting for object sync

* Mon Oct 22 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-11.eb97cde898d6a7b97fff24594e62e0057f1cefe4
- Ignore non-existing submodule objects during cloning

* Mon Oct 22 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-10.4ee97589b7ba25070f153d01f171897d4b94494e
- Add debugging for hook cloning

* Mon Oct 22 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-9.bf7712e29bc50ebdfdd1369be00e92d37db6fd51
- Ignore submodules during object validation

* Fri Oct 19 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-8.a6230fe13334025545d194c93e37b0e3723aa383
- Fix empty tree pushing

* Tue Oct 16 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-7.70e088ab29dbcd0d300e668aa3222856ca63198b
- Fix race condition between repo list and changes

* Tue Oct 16 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-6.1db4239408e4bdfedeae42f938ec0e30275693cf
- Fix checksum reading bug

* Tue Oct 16 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-5.f49f250dda18384045a7d10b4b152b6251f0b6c1
- Fix rpcClient keepalives and add retries

* Tue Oct 16 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-4.a6efed11e01d94b60137d36d299a993618f0976d
- Make sure to only load a newer snapshot

* Mon Oct 15 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-3.cbd1aa8c25dacd4490ec6de57fba8e4b3a5cf2e5
- Try another snapshot fix

* Mon Oct 15 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-2.f09e534300e6b90c6678d18be147b52950c25b48
- Fix snapshot restoration bug

* Wed Oct 10 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.3-1.880431b3feecc5158466ad68f83ee0c1a6a8671e
- Add repoBridge configuration via environment

* Tue Oct 09 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.10.09ca6bc37a29d59e1729bbad6377740b773fdbf5
- Log encoding
- Fix file descriptor leakage with compressed requests

* Fri Oct 05 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.9.9f0d7660452da0b16041d584b48adae6f583c56c
- Fix bug when client sends gzip encoded request

* Fri Oct 05 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.8.5a7245e0e8ef6d66c5a992a78658317b101f13a2
- Add repo delete
- Fix packet reading bug

* Mon Oct 01 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.7.53848bc45b236d6cd7519a7bc7d8ebc7c6a08bed
- Fix various hook environment issues

* Fri Sep 28 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.6.57d0369eb059bcd716b7b39a4994db014eaf9a1e
- Fix bug in hooks: stderr now goes to sideBandProgress

* Thu Sep 27 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.5.967a8d34c78c97beab20d92f57472b7cfddb189a
- Require -filesystem on bridge and main

* Thu Sep 27 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.4.967a8d34c78c97beab20d92f57472b7cfddb189a
- Add patch for issue #20 (duplicated object during push)

* Wed Sep 26 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.2.b4fadf611c928dc0cab59338b7b418e7c2c4d65b
- Added repoSpanner git- vs non fix

* Tue Sep 25 2018 Patrick Uiterwijk <puiterwijk@redhat.com> - 0.2-0.1.b4fadf611c928dc0cab59338b7b418e7c2c4d65b
- New build with repobridge extras

