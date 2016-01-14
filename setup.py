from setuptools import setup, find_packages

setup(
    name='uptime',
    version=0.1,
    packages=find_packages(),
    package_dir={'uptime': 'uptime'},
    package_data={ 'uptime': ['templates/*', 'static/*'] },
    entry_points={'console_scripts': ['uptime = uptime.cli:main']},
    install_requires=['gevent==1.1b1', 'jinja2', 'flask==0.10.1', 'flask_restful==0.3.2', 'redis', 'requests'],
    include_package_data=True,
    classifiers=[
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4'
    ]
)
