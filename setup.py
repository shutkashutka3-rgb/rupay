from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rupay",
    version="0.1.0",
    author="rupay contributors",
    description="Единая Python-библиотека для работы с российскими платежными системами",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shutkashutka3-rgb/rupay",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "aiohttp>=3.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.12.0",
            "black>=21.0",
            "flake8>=3.9.0",
            "mypy>=0.900",
        ],
    },
    keywords="payment yoomoney qiwi tinkoff russia acquiring payments",
    project_urls={
        "Documentation": "https://github.com/shutkashutka3-rgb/rupay#readme",
        "Source": "https://github.com/shutkashutka3-rgb/rupay",
        "Issues": "https://github.com/shutkashutka3-rgb/rupay/issues",
    },
)

