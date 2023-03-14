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
    url="https://github.com/pypa/petrovisor",
    project_urls={
        "Bug Tracker": "https://github.com/pypa/petrovisor/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)