from setuptools import setup

__author__ = 'notcammy'
__email__ = 'neus2benen@gmail.com'
__version__ = '3.2.4'

_api_version = '1.6.0'
_api_extensions_version = '0.3.9'

long_description = 'This Python script enables you to download any ongoing Instagram livestreams as well as any ' \
                   'available replays. It is based on another script that has now been discontinued. '

setup(
    name='pyinstalive',
    version=__version__,
    author=__author__,
    author_email=__email__,
    url='https://github.com/notcammy/PyInstaLive',
    packages=['pyinstalive'],
    entry_points={
        'console_scripts': [
            'pyinstalive = pyinstalive.__main__:run',
        ]
    },
    install_requires=[
        # 'instagram_private_api @ https://github.com/ping/instagram_private_api/archive/%(api)s.tar.gz#egg=instagram_private_api-%(api)s' % {'api': _api_version},
        'instagram_private_api_extensions @ https://github.com/ping/instagram_private_api_extensions/archive/%(api)s.tar.gz#egg=instagram_private_api_extensions-%(api)s' % {'api': _api_extensions_version},
        'argparse',
        'configparser'
    ],
    include_package_data=True,
    platforms='any',
    long_description=long_description,
    keywords='instagram-livestream-recorder record-instagram-livestreams live instagram record livestream video '
             'recorder downloader download save',
    description='This script enables you to download Instagram livestreams and replays.',
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
