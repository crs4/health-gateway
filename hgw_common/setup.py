from setuptools import setup, find_packages

desc = ''
with open('README.md') as f:
    desc = f.read()

setup(
    name='hgw_common',
    version='1.0.0',
    description=('Health Gateway common library'),
    long_description=desc,
    url='',
    author='Vittorio Meloni',
    author_email='vittorio.meloni@crs4.it',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='',
    packages=find_packages(exclude=['contrib', 'docs', 'test*']),
    install_requires=[
        'Django==2.2.5',
        'djangorestframework==3.10.3',
        'django-oauth-toolkit==0.12.0',
        'django-cors-middleware==1.3.1',
        'requests==2.22.0',
        'requests_oauthlib==0.8.0',
        'kafka_python==1.4.6',
        'pycryptodomex==3.4.7',
        'coreapi==2.3.3',
        'PyYAML==5.1.1',
        'djangosaml2==0.17.2',
    ],
    package_data={},
    data_files=[],
    entry_points={},
)
