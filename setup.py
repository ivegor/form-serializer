from setuptools import setup


setup(
    name='form-serializer',
    version='0.1.2',
    description='Class based serializer for form.',
    author_email='ivankegor@gmail.com',
    url='https://github.com/ivegor/form-serializer',
    long_description=open('README.md', 'r').read(),
    packages=[
        'form_serializer',
    ],
    zip_safe=False,
    requires=[
    ],
    install_requires=[
    ],
    classifiers=[
        'Development Status :: Pre Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
