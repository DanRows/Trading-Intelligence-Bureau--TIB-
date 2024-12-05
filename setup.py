from setuptools import setup, find_packages

setup(
    name="trading-intelligence-bureau",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pybit>=2.4.1",
        "pandas>=1.5.3",
        "numpy>=1.24.2",
        "plotly>=5.13.1",
        "streamlit>=1.20.0",
        "python-dotenv>=1.0.0",
    ],
    author="Tu Nombre",
    author_email="tu@email.com",
    description="Sistema de análisis de trading de criptomonedas",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tu-usuario/trading-intelligence-bureau",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 