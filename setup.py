import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="localshit",
    version="0.0.1",
    author="David Luettmann, Markus Drespling, Frederick Dehner",
    author_email="",
    description="distributed system lecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    package_dir={"": "src"},
    packages=setuptools.find_namespace_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        "console_scripts": ["localshit = localshit.__main__:main", "client = localshit.client:main", "frontend = localshit.frontend:main"]
    }
)