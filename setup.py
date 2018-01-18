from setuptools import setup

setup(
    name='WebServerPlugin',
    version='1.0',
    packages=['WebServerPlugin'],
    install_requires=
    [
        'Coronado',
        'tornado==4.5.2'
    ],
    author='Mukul Majmudar',
    author_email='mukul@curecompanion.com',
    description='Web server plugin for Coronado')
