import pathlib
from typing import Mapping, Sequence

import setuptools

DISTRIBUTION_PACKAGE_NAME = INSTALL_PACKAGE_NAME = "diagv"

FILE = pathlib.Path(__file__)
REQUIREMENTS = FILE.parent / "requirements"


def read_description() -> str:
    title = read_readme().splitlines()[0]
    prefix = "# "
    assert title.startswith(prefix)
    return title[len(prefix) :]


def read_readme() -> str:
    file = FILE.parent / "README.md"
    return file.read_text()


def read_requirements(name) -> Sequence[str]:
    file = REQUIREMENTS / f"{name}.txt"
    with file.open() as f:
        return list(f)


def read_install_requires() -> Sequence[str]:
    return read_requirements("install_requires")


def read_extras_require() -> Mapping[str, Sequence[str]]:
    return {
        file.stem.split("-", maxsplit=1)[1]: read_requirements(file.stem)
        for file in REQUIREMENTS.glob("extras_require-*.txt")
    }


setuptools.setup(
    author="AP Ljungquist",
    author_email="ap@ljungquist.eu",
    description=read_description(),
    extras_require=read_extras_require(),
    install_requires=read_install_requires(),
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    name=DISTRIBUTION_PACKAGE_NAME,
    package_data={
        INSTALL_PACKAGE_NAME: ["py.typed"],
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages("src"),
    python_requires=">=3.9",
    url="https://github.com/apljungquist/diagv",
)
