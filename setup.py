from setuptools import setup

setup(
    name='FPGAedu',
    version='0.1',
    author='Matthijs Bos',
    author_email='matthijs_vlaarbos@hotmail.com',
    url='https://fpgaedu.com',
    packages=['fpgaedu'],
    entry_points={
        'console_scripts': [
            'fpgaedu = fpgaedu:main'
        ]
    }
)
