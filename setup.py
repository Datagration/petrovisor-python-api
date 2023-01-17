import setuptools

# long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="petrovisor",
    version="0.0.1-preview",
    author="Datagration Solutions Inc.",
    author_email="developers@datagration.com",
    description="Python API for PetroVisor platform.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/petrovisor",
    project_urls={
        "Bug Tracker": "https://github.com/pypa/petrovisor/issues",
    },
    #py_modules=["petrovisor"],
    classifiers=[
        "Programming Language :: Python :: 3",
        #"Programming Language :: Python :: 3.5",
        #"Programming Language :: Python :: 3.6",
        #"Programming Language :: Python :: 3.7",
        #"Programming Language :: Python :: 3.8",
        #"Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    #packages=["petrovisor"],
    python_requires=">=3.6",
    #zip_safe=False,
)