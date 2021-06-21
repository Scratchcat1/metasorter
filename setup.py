from setuptools import setup, find_packages

setup(
    name="metasorter",
    version="0.1",
    author="Connor Holloway",
    author_email="root_pfad@protonmail.com",
    description="Tool to automatically rename and organise photos and videos by date taken",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["metasorter = metasorter.main:main"]
    },
    install_requires=[
        "cffi==1.14.4",
        "ExifRead==2.3.2",
        "ffmpeg-python==0.2.0",
        "future==0.18.2",
        "pycparser==2.20",
        "watchdog==1.0.2",
    ],
)
