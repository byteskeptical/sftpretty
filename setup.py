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

DESCRIPTION = 'Pretty secure file transfer made easy.'

setup(
    # metadata for upload to PyPI
    author='byteskeptical',
    author_email='40208858+byteskeptical@users.noreply.github.com',
    description=DESCRIPTION,
    download_url='https://pypi.python.org/pypi/sftpretty',
    install_requires=['paramiko>=1.17'],
    keywords='ftp scp sftp ssh',
    license='BSD',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    name='sftpretty',
    packages=['sftpretty', ],
    platforms=['any'],
    url='https://github.com/byteskeptical/sftpretty',
    version='1.1.1',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
