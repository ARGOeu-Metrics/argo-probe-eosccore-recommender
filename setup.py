from distutils.core import setup

NAME = "argo-probe-eosccore-recommender"


def get_ver():
    try:
        for line in open(NAME + '.spec'):
            if "Version:" in line:
                return line.split()[1]
    except IOError:
        raise SystemExit(1)


def get_data_files():
    import sys
    if sys.platform != "darwin":
        return [('/usr/libexec/argo/probes/eosccore-recommender', ['src/check_rs.py'])]


setup(
    name=NAME,
    version=get_ver(),
    author="GRNET",
    author_email="agelos.tsal@gmail.com",
    description="ARGO probe that checks the recommender system and its components",
    url="https://github.com/ARGOeu-Metrics/argo-probe-eosccore-recommender",
    package_dir={'argo_probe_eosccore_recommender': 'modules'},
    packages=['argo_probe_eosccore_recommender'],
    data_files=get_data_files()
)
