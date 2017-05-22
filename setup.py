from setuptools import setup

setup(
    name="django-logicaldelete",
    version='1',
    author="Luis Velez",
    author_email="lvelezsantos@gmail.com",
    url="https://github.com/lvelezsantos/django-logicaldelete",
    description="a base model that provides built in logical delete functionality",
    long_description=open("README.rst").read(),
    packages=[
        "logicaldelete"
    ],
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ]
)
