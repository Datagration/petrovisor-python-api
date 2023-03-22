import setuptools

# long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="petrovisor",
    version="0.1.0",
    author="Datagration Solutions Inc.",
    author_email="developers@datagration.com",
    description="Python API for PetroVisor platform.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Datagration/petrovisor-python-api",
    classifiers=[
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=['petrovisor'],
    python_requires=">=3.7",
)
