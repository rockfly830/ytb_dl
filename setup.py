from setuptools import find_packages, setup


requirements = [
    "python-dotenv==1.0.1",
    "google-api-python-client==2.136.0",
    "pydantic==2.7.1",
    "loguru==0.7.2",
    "yt-dlp==2024.7.2"
]
setup(
    name="youtube_dl",
    version="1.0.0",
    author="Rockfly830",
    license="MIT",
    url="https://github.com/rockfly830/you_dl",
    install_requires=requirements,
    packages=find_packages(),
    python_requires=">=3.9",
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
