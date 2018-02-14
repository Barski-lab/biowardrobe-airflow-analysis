# BioWardrobe backend (airflow+cwl)

### About
Python package to replace [BioWardrobe's](https://github.com/Barski-lab/biowardrobe) python/cron scripts. It uses
[Apache-Airflow](https://github.com/apache/incubator-airflow)
functionality with [CWL v1.0](http://www.commonwl.org/v1.0/).

### Install
1. Add biowardrobe MySQL connection into Airflow connections
    ```sql
    select * from airflow.connection;
    insert into airflow.connection values(NULL,'biowardrobe','mysql','localhost','ems','wardrobe','',null,'{"cursor":"dictcursor"}',0,0);
    ```
2. Install
    ```sh
    sudo pip3 install .
    ```

### Requirements
1. Make sure your system satisfies the following criteria:
      - Ubuntu 16.04.3
        - python3.6
            ```sh
            sudo add-apt-repository ppa:jonathonf/python-3.6
            sudo apt-get update
            sudo apt-get install python3.6
            ```
        - pip3
          ```sh
          curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6
          pip3 install --upgrade pip3
          ```
        - setuptools
          ```sh
          pip3 install setuptools
          ```
        - [docker](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/)
          ```sh
          sudo apt-get update
          sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
          curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
          sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
          sudo apt-get update
          sudo apt-get install docker-ce
          sudo groupadd docker
          sudo usermod -aG docker $USER
          ```
          Log out and log back in so that your group membership is re-evaluated.
        - libmysqlclient-dev
          ```sh
          sudo apt-get install libmysqlclient-dev
          ```
        - nodejs
          ```sh
          sudo apt-get install nodejs
          ```
2. Get the latest version of `cwl-airflow-parser`.
   If **[Apache-Airflow](https://github.com/apache/incubator-airflow)**
   or **[cwltool](http://www.commonwl.org/ "cwltool main page")** aren't installed,
   installation will be done automatically with recommended versions. Set `AIRFLOW_HOME` environment 
   variable to airflow config directory default is `~/airflow/`.
      ```sh
      git clone https://github.com/datirium/cwl-airflow-parser.git
      cd cwl-airflow-parser
      sudo pip3 install .
      ```

3. If required, add **[extra airflow packages](https://airflow.incubator.apache.org/installation.html#extra-packages)**
   for extending Airflow functionality, for instance, with MySQL support `pip3 install apache-airflow[mysql]`.

### Running

1. To create BioWardrobe's dags run `biowardrobe-init` in airflow's dags directory 
    ```
    cd ~/airflow/dags
    ./biowardrobe-init 
    ```
2. Run Airflow scheduler:
   ```sh
   airflow scheduler
   ```
3. Use `airflow trigger_dag` with input parameter `--conf "JSON"` where JSON is either job definition or biowardrobe_uid 
and explicitly specified cwl descriptor `dag_id`.
    ```sh
    airflow trigger_dag --conf "{\"job\":$(cat ./hg19.job)}" "bowtie-index"
    ```
    where `hg19.job` is:
    ```json
    {
      "fasta_input_file": {
        "class": "File", 
        "location": "file:///wardrobe/indices/bowtie/hg19/chrM.fa", 
        "format":"http://edamontology.org/format_1929",
        "size": 16909,
        "basename": "chrM.fa",
        "nameroot": "chrM",
        "nameext": ".fa"
      },
      "output_folder": "/wardrobe/indices/bowtie/hg19/",
      "threads": 6,
      "genome": "hg19"
    }
    ```

4. All the output will be moved from temporary directory into **output_folder** parameter
  of the job.
  
