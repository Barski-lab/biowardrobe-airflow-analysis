#! /usr/bin/env python3
"""
****************************************************************************

 Copyright (C) 2018 Datirium. LLC.
 All rights reserved.
 Contact: Datirium, LLC (datirium@datirium.com)

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 ****************************************************************************"""


from setuptools import setup, find_packages
import os
from setuptools.command.install import install
from subprocess import check_call


class ActionOnInstall(install):
    def run(self):
        try:
            check_call(['git', 'clone', '-b', 'v1.0.2', '--single-branch', "https://github.com/Barski-lab/workflows/",
                        "biowardrobe_airflow_analysis/biowardrobe_workflows"])
        except:
            pass
        install.run(self)

setup(
    name='biowardrobe-airflow-analysis',
    description='Python package to extend BioWardrobe functionality with CWL Airflow',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    version='1.0.0',
    url='https://github.com/datirium/biowardrobe-airflow-analysis',
    download_url='https://github.com/datirium/biowardrobe-airflow-analysis',
    author='Datirium, LLC',
    author_email='porter@datirium.com',
    license='Apache-2.0',
#    packages=find_packages('biowardrobe_airflow_analysis'),
    packages=find_packages(),
    install_requires=[
        'cwltool',
        'jsonmerge',
        'ruamel.yaml < 0.15',
        'MySQLdb',
        'apache-airflow >= 1.9.0, < 2'
    ],
    cmdclass={
        'install': ActionOnInstall
    },
    zip_safe=False,
    include_package_data=True,
    package_data={
        'biowardrobe_airflow_analysis': ['biowardrobe_workflows/workflows/*.cwl',
                                         'biowardrobe_workflows/expressiontools/*.cwl',
                                         'biowardrobe_workflows/metadata/*.cwl',
                                         'biowardrobe_workflows/tools/*.cwl',
                                         'biowardrobe_workflows/tools/metadata/*.yaml',
                                         'biowardrobe_workflows/tools/metadata/*.yml']
    }
    # dependency_links=[
    #  "https://github.com/Barski-lab/workflows/archive/v1.0.2.zip#egg=biowardrobe_workflows-1.0.2"
    #  "git+https://github.com/Barski-lab/workflows/tree/v1.0.2#egg=biowardrobe_workflows-1.0.2"
    # ],
    #    entry_points={
    #        'console_scripts': [
    #            "cwl-airflow-parser=cwl-airflow-parser.main:main"
    #        ]
    #    }
)
