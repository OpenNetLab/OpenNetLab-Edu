import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="OpenNetLab",
    version="0.2",
    author="zdszero",
    author_email="dingzifeng8@gmail.com",
    description="OpenNetLab for edu 2022 By USTC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zdszero/OpenNetLab",
    project_urls={
        "Bug Tracker": "https://github.com/zdszero/OpenNetLab/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)
