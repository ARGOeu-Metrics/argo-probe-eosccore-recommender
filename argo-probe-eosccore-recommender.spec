%global __python ${python3}
%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       ARGO probe that checks the recommender system and its components
Name:          argo-probe-eosccore-recommender
Version:       0.1.0
Release:       2%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

BuildRequires: python3-devel
Requires: python36-requests

%description
ARGO probe that checks the recommender system and its components

%prep
%setup -q

%build
%{py3_build}

%install
%{py3_install "--record=INSTALLED_FILES" }

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%dir %{python3_sitelib}/%{underscore %{name}}/
%{python3_sitelib}/%{underscore %{name}}/*.py
%{_libexecdir}/argo/probes/eosccore-recommender/*.py

%changelog
* Fri Jan 20 2023 Angelos Tsalapatis <agelos.tsal@gmail.com> - 0.1.0-1
- REC-173 Create eosccore-recommender probe