from importlib.machinery import SourceFileLoader
import io
import os.path

from setuptools import find_packages, setup

dashboard_server = SourceFileLoader(
    "dashboard_server", "./dashboard_server/__init__.py",
).load_module()

with io.open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    long_description = f.read()

include_tests = False
exclude_packages = ("dashboard_server.tests",) if not include_tests else ()

package_data = {"": ["README.md"]}
if include_tests:
    test_data_dirs = ["./data/*"]
    package_data["dashboard_server.tests"] = test_data_dirs

setup(
    name="dashboard_server",
    description="Magics for working with earth models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=dashboard_server.__version__,
    license="Proprietary",
    author="source{d}",
    author_email="production-machine-learning@sourced.tech",
    url="https://github.com/Guillemdb/dashboard_server",
    download_url="https://github.com/Guillemdb/dashboard_server",
    packages=find_packages(exclude=exclude_packages),
    keywords=["dashboard_server"],
    install_requires=["numpy>=1.16.2,<2",
                      "packaging>=19.0",
                      "pandas>=0.23.4,<1",
                      "panel",
                      "holoviews",
                      "bokeh",
                      "flask",
                      "hvplot",
                      "plotly",
                      "matplotlib",
                      "scipy",
                      "networkx",
                      ],
    package_data=package_data,
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: Propietary license",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
    ],
)
