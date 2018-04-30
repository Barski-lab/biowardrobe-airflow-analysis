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
from os import path
from subprocess import check_output, CalledProcessError
from time import strftime, gmtime
from setuptools.command.egg_info import egg_info

SETUP_DIR = path.dirname(__file__)
README = path.join(SETUP_DIR, 'README.md')


class EggInfoFromGit(egg_info):
    """Tag the build with git commit timestamp.

    If a build tag has already been set (e.g., "egg_info -b", building
    from source package), leave it alone.
    """

    def git_timestamp_tag(self):
        gitinfo = check_output(
            ['git', 'log', '--first-parent', '--max-count=1',
             '--format=format:%ct', '.']).strip()
        return strftime('.%Y%m%d%H%M%S', gmtime(int(gitinfo)))

    def tags(self):
        if self.tag_build is None:
            try:
                self.tag_build = self.git_timestamp_tag()
            except CalledProcessError:
                pass
        return egg_info.tags(self)


tagger = EggInfoFromGit


setup(
    name='biowardrobe-airflow-analysis',
    description="Replaces BioWardrobe's backend with CWL Airflow",
    long_description=open(README).read(),
    version='1.0',
    url='https://github.com/datirium/biowardrobe-airflow-analysis',
    download_url='https://github.com/datirium/biowardrobe-airflow-analysis',
    author='Datirium, LLC',
    author_email='support@datirium.com',
    # license='Apache-2.0',
    packages=find_packages(),
    install_requires=[
        'cwltool == 1.0.20180220121300',
        'sqlparse',
        'jsonmerge',
        'ruamel.yaml < 0.15',
        'biowardrobe-cwl-workflows == 1.0.20180423012817',
        'cwl-airflow-parser == 1.0.20180220071453',
        'apache-airflow >= 1.9.0, < 2'
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "biowardrobe-init=biowardrobe_airflow_analysis.biowardrobe_init:generate_biowardrobe_workflow"
        ]
    },
    include_package_data=True,
    package_data={
        '': ['*.sh'],
        'biowardrobe_airflow_analysis': [
            'sql_patch/biowardrobe_tables/*.sql',
            'sql_patch/biowardrobe_views/*.sql',
            'system/macosx/*.plist',
            'system/ubuntu/*.service'
        ]
    },
    cmdclass={'egg_info': tagger},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: Microsoft :: Windows :: Windows 8.1',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Medical Science Apps.'
    ]
)
