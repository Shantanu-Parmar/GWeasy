from setuptools import setup, find_packages

setup(
    name="GWeasy",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "Pillow",
        "cefPython3",
        "tkinter"
    ],
    entry_points={
        "console_scripts": [
            "GWeasy=GWeasy:main"
        ]
    },
    include_package_data=True,
    package_data={
        "": ["config.txt", "gravfetch.py"],
    },
)
