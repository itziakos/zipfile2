import os
import subprocess

from setuptools import setup


MAJOR = 0
MINOR = 0
MICRO = 11

IS_RELEASED = True

VERSION_INFO = (MAJOR, MINOR, MICRO)
VERSION = ".".join(str(i) for i in VERSION_INFO)


# Return the git revision as a string
def git_version():
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        git_revision = out.strip().decode('ascii')
    except OSError:
        git_revision = "Unknown"

    try:
        out = _minimal_ext_cmd(['git', 'rev-list', '--count', 'HEAD'])
        git_count = out.strip().decode('ascii')
    except OSError:
        git_count = "0"

    return git_revision, git_count


def write_version_py(filename):
    template = """\
# THIS FILE IS GENERATED FROM ZIPFILE2 SETUP.PY
version = '{version}'
full_version = '{full_version}'
git_revision = '{git_revision}'
is_released = {is_released}

if not is_released:
    version = full_version
"""
    version = full_version = VERSION
    is_released = IS_RELEASED

    git_rev = "Unknown"
    git_count = "0"

    if os.path.exists('.git'):
        git_rev, git_count = git_version()
    elif os.path.exists(filename):
        # must be a source distribution, use existing version file
        try:
            from zipfile2._version import git_revision as git_rev
        except ImportError:
            raise ImportError("Unable to import git_revision. Try removing "
                              "zipfile2/_version.py and the build directory "
                              "before building.")

    if not is_released:
        full_version += '.dev{0}+{1}'.format(git_count, git_rev[:7])

    with open(filename, "wt") as fp:
        fp.write(template.format(version=version,
                                 full_version=full_version,
                                 git_revision=git_rev,
                                 is_released=is_released))


def main():
    write_version_py("zipfile2/_version.py")

    from zipfile2 import __version__

    setup(
        name="zipfile2",
        author="David Cournapeau",
        author_email="cournape@gmail.com",
        description="An improved ZipFile class.",
        packages=[
            "zipfile2",
            "zipfile2.tests",
        ],
        package_data={
            "zipfile2.tests": ["data/*.zip", "data/*egg"],
        },
        version=__version__,
        license="PSFL",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: Python Software Foundation License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
        ]
    )


if __name__ == "__main__":
    main()
