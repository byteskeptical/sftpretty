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

DESCRIPTION = "Making SFTP great AGAIN!"

setup(
    name='sftpretty',
    version='0.0.3',

    packages=['sftpretty', ],

    install_requires=['paramiko>=1.17'],

    # metadata for upload to PyPI
    author='bornwitbugs',
    author_email='40208858+bornwitbugs@users.noreply.github.com',
    description=DESCRIPTION,
    license='BSD',
    keywords='sftp ssh ftp internet',
    url='https://github.com/bornwitbugs/sftpretty',
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    download_url='https://pypi.python.org/pypi/sftpretty',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
    ],

)
