from pathlib import Path

from setuptools import setup


BASE_DIR = Path(__file__).parent
README_PATH = BASE_DIR / "README.md"


setup(
    name="literature",
    packages=["literature"],
    version="1.0.0",
    license="MIT",
    description="Literature card game implementation",
    long_description=README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else "",
    long_description_content_type="text/markdown",
    author="Neel Somani",
    author_email="neeljaysomani@gmail.com",
    url="https://github.com/neelsomani/literature",
    download_url="https://github.com/neelsomani/literature/releases",
    keywords=[
        "machine-learning",
        "q-learning",
        "neural-network",
        "artificial-intelligence",
        "card-game",
    ],
    install_requires=[
        "numpy>=1.24",
        "scikit-learn>=1.4",
    ],
    extras_require={
        "dev": ["pytest>=7.4"],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
