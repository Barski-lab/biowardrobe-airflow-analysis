#! /usr/bin/env python3

import argparse
import MySQLdb
from typing import Text
import os


class Settings:
    """Class to get access to DB"""

    _args = argparse.Namespace()

    def __init__(self):
        self.conn = None
        self._cursor = None
        not_normalized_args, _ = self.arg_parser().parse_known_args()
        self._args = self.normalize(not_normalized_args)
        try:
            with open(self._args.config, 'r') as conf_file:
                self.config = [line.strip() for line in conf_file.readlines() if not line.startswith("#") and line.strip()]
        except Exception as e:
            print("Can't open file " + self._args.config, str(e))
            return
        self.settings = {"emsdb": self.config[3]}
        self.def_connect()
        self.get_settings()

    @property
    def args(self):
        return self._args

    @property
    def cursor(self):
        return self._cursor

    def arg_parser(self):
        """Returns argument parser"""
        parser = argparse.ArgumentParser(description='BioWardrobe settings parser for DB connection', add_help=True)
        parser.add_argument("-c", "--config", type=Text, help="Wardrobe config file", default="/etc/wardrobe/wardrobe")
        parser.add_argument("-j", "--jobs", type=Text, help="Folder to export generated jobs", default="./")
        parser.add_argument("-w", "--working_dir", type=Text, help="Current working directory", default="./")
        return parser

    def normalize(self, not_normalized_args):
        """Resolves all relative paths to be absolute relatively to current working directory"""
        normalized_args = {}
        for key, value in not_normalized_args.__dict__.items():
            normalized_args[key] = value if not value or os.path.isabs(value) else os.path.normpath(
                os.path.join(os.getcwd(), value))
        return argparse.Namespace(**normalized_args)

    def def_connect(self):
        try:
            self.conn = MySQLdb.connect(host=self.config[0],
                                        user=self.config[1],
                                        passwd=self.config[2],
                                        db=self.config[3])
            self.conn.set_character_set('utf8')
            self._cursor = self.conn.cursor()
        except Exception as e:
            print("Database connection error: " + str(e))
        return self._cursor

    def def_close(self):
        try:
            #self._cursor.close()
            self.conn.close()
        except:
            pass

    def get_settings(self):
        self._cursor.execute("select * from settings")
        for (key, value, descr, stat, group) in self._cursor.fetchall():
            if key in ['advanced', 'bin', 'indices', 'preliminary', 'temp', 'upload']:
                value = value.lstrip('/')
            self.settings[key] = value

    def use_ems(self):
        self._cursor.execute('use {}'.format(self.settings["emsdb"]))

    def use_airflow(self):
        self._cursor.execute('use {}'.format(self.settings["airflowdb"]))
