from setuptools import setup

f = open('README.md')
readme = f.read()
f.close()

setup(
    name='django-smoketest',
    version='0.1',
    description=('Django-smoketest is a pair of apps, one for running'
                 ' smoketests, and one for monitoring them remotely.'),
    long_description=readme,
    author='David Wolfe',
    author_email='davidgameswolfe@gmail.com',
    url='https://github.com/aioTV/django-smoketest/',
    license='MIT',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
