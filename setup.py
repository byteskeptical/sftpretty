'''setup for package'''

from setuptools import setup

with open('README.rst') as h_rst:
    LONG_DESCRIPTION = h_rst.read()

with open('docs/changes.rst') as h_rst:
    BUF = h_rst.read()
    BUF = BUF.replace('``', '$')        # protect existing code markers
    for xref in [':meth:', ':attr:', ':class:', ':func:']:
        BUF = BUF.replace(xref, '')     # remove xrefs
    BUF = BUF.replace('`', '``')        # replace refs with code markers
    BUF = BUF.replace('$', '``')        # restore existing code markers
LONG_DESCRIPTION += BUF

DESCRIPTION = "Pretty secure file transfer made easy."

setup(
    name='sftpretty',
    version='1.0.3',

    packages=['sftpretty', ],

    install_requires=['paramiko>=1.17'],

    # metadata for upload to PyPI
    author='byteskeptical',
    author_email='40208858+byteskeptical@users.noreply.github.com',
    description=DESCRIPTION,
    license='BSD',
    keywords='ftp scp sftp ssh',
    url='https://github.com/byteskeptical/sftpretty',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    platforms=['any'],
    download_url='https://pypi.python.org/pypi/sftpretty',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
