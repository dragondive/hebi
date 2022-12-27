import setuptools
import os
import sys

setup_folder = os.path.dirname(os.path.realpath(__file__))
requirements_file = os.path.join(setup_folder, "requirements.txt")
install_requires = []
with open(requirements_file) as file:
    install_requires = file.read().splitlines()

setuptools.setup(name="multibeggar",
version="1.0",
description="Analysis of Stock Portfolio Complexity",
author="Aravind Pai",
install_requires=install_requires,
author_email="dragondive@outlook.in",
packages=setuptools.find_packages(),
package_data={
    "multibeggar": ["data/*.csv", "data/memes/*.jpg"]
},
zip_safe=False)


