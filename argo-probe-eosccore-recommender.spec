%global __python ${python3}
%define underscore() %(echo %1 | sed 's/-/_/g')

Summary:       ARGO probe that checks the recommender system and its components
Name:          argo-probe-eosccore-recommender
Version:       0.1.1
Release:       2%{?dist}
Source0:       %{name}-%{version}.tar.gz
License:       ASL 2.0
Group:         Development/System
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Prefix:        %{_prefix}
BuildArch:     noarch

BuildRequires: python3-devel

%if 0%{?el7}
Requires:      python36-requests

%else
Requires:      python3-requests

%endif

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
* Thu Apr 4 2024 Katarina Zailac <kzailac@srce.hr> - 0.1.1-1
- AO-933 Create Rocky 9 RPM for argo-probe-eosccore-recommender
- REC-173 Fix import path for checks module
- REC-173 Add support for recursively checking component dependencies
* Fri Jan 20 2023 Angelos Tsalapatis <agelos.tsal@gmail.com> - 0.1.0-1
- REC-173 Create eosccore-recommender probe
