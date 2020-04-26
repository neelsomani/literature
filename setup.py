from distutils.core import setup
setup(
    name='literature',
    packages=['literature'],
    version='0.1.0',
    license='MIT',
    description='Literature card game implementation',
    author='Neel Somani',
    author_email='neeljaysomani@gmail.com',
    url='https://github.com/neelsomani/literature',
    download_url='https://github.com/neelsomani/literature/releases',
    keywords=[
        'machine-learning',
        'q-learning',
        'neural-network',
        'artificial-intelligence',
        'card-game'
    ],
    install_requires=[
        'numpy==1.17.0',
        'pytest==5.0.1',
        'scikit-learn==0.21.3'
    ],
    classifiers=[
        '5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
)
