from udemy_userAPI.__version__ import __version__, __autor__, __repo__, __lib_name__, \
    __description__
from setuptools import setup, find_packages

# Lê o conteúdo do README.md
with open('README_PYPI.md', 'r', encoding='utf-8') as file:
    long_description = file.read()

setup(
    name=__lib_name__,
    version=__version__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=__autor__,
    author_email="paulocesar0073dev404@gmail.com",
    license="MIT",
    keywords=["udemy", "udemy python", "pyudemy","udemy_userAPI","udemy api"],
    install_requires=[
        'requests',
        'cloudscraper',
        'pywidevine'
    ],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms=["any"],
    project_urls={
        'GitHub': __repo__,
        "Bugs/Melhorias": f"{__repo__}/issues",
        "Documentação": f"{__repo__}/wiki",
    }
)
