from setuptools import setup, find_packages


with open("pennylane_kq/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")


pennylane_devices_list = [
    "kq.cloudv2 = pennylane_kq:KQCloudV2Device",
]

# requirements = ["pennylane>=0.19,<0.30"]

setup(
    name="pennylane-kq",
    version=version,
    description="A Pennylane plugin for KQ Cloud System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://www.github.com/inojeon/pennylane-kq",
    author="Inho Jeon",
    author_email="inojeon@kisti.re.kr",
    license="BSD-2",
    packages=find_packages(),
    zip_safe=False,
    # install_requires=requirements,
    entry_points={
        "pennylane.plugins": pennylane_devices_list
    },  # for registering the pennylane device(s)
    include_package_data=True,
    install_requires=[
        "pennylane >= 0.40",
        "numpy",
        "requests >= 2.26.0",
    ],
    provides=["pennylane_kq"],
)
