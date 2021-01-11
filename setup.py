import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kmlb",
    version="0.0.1",
    author="HFM3",
    description="Google Earth KML Builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HFM3/kmlb",
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "images"]),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research"
    ],
    python_requires='>=3.8',
)
