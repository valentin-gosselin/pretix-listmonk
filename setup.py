from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pretix-listmonk',
    version='1.0.0',
    description='Pretix plugin to subscribe attendees to a Listmonk newsletter list',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/valentin-gosselin/pretix-listmonk',
    author='Valentin Gosselin',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='pretix plugin listmonk newsletter',
    packages=['pretix_listmonk'],
    include_package_data=True,
    package_data={
        'pretix_listmonk': [
            'templates/pretix_listmonk/*.html',
            'locale/*/LC_MESSAGES/django.po',
            'locale/*/LC_MESSAGES/django.mo',
        ],
    },
    install_requires=[
        'requests>=2.25.0',
    ],
    python_requires='>=3.8',
    entry_points={
        'pretix.plugin': [
            'pretix_listmonk = pretix_listmonk:ListmonkPluginConfig',
        ],
    },
)
