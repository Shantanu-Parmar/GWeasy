from setuptools import setup, find_packages

setup(
    name="gweasy",
    version="0.1.0",
    description="A user-friendly GUI for gravitational wave data analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Shantanusinh Parmar",
    author_email="gweasysoftware@gmail.com", 
    url="https://github.com/shantanu-parmar/GWeasy",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "gwpy",
        "PyQt5",
        "requests-pelican",
    ],
    extras_require={
        "dev": ["build", "twine"],
    },
    entry_points={
        "console_scripts": [
            "gweasy = gweasy.gweasy:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.10",
)
