import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="onl",
    version="0.3",
    author="zdszero",
    author_email="dingzifeng8@gmail.com",
    description="onl for education 2023 By USTC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onl/onl-Edu",
    project_urls={
        "Bug Tracker": "https://github.com/onl/onl-Edu/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)
