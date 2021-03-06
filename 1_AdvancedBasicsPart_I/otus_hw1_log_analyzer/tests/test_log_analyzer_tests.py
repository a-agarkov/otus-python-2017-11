from collections import namedtuple
from unittest import TestCase
import os
import datetime as dt
from log_analyzer import find_latest_log, check_if_report_exists, make_report_table, render_html_report, parse_log, parse_config, parse_line
import logging
import sys
import json
import re
import gzip

default_config = {"REPORT_SIZE": 1000,
                  "REPORT_DIR": "./reports",
                  "LOG_DIR": "./log"}

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s %(message)s',
                    datefmt='%Y.%m.%d %H:%M:%S',
                    stream=sys.stdout)


class TestLogAnalyzer(TestCase):
    def test_parse_config(self):
        # 1. Check good config.
        good_config_path = './tests/config/log_analyzer.conf'
        with open(good_config_path, mode='r') as f:
            passed_config = json.load(f)
        config = parse_config(default_config=default_config,
                              config_path=good_config_path)

        self.assertIsInstance(config, dict)
        self.assertNotEqual(default_config["REPORT_DIR"], passed_config["REPORT_DIR"])

        # 2. Check broken config path.
        config = parse_config(default_config=default_config,
                              config_path='./tests/config/no_log_analyzer_at_all')

        self.assertEqual(config, 'No config at given path.')

        # 3. Check broken config path.
        config = parse_config(default_config=default_config,
                              config_path='./tests/config/bad_log_analyzer.conf')

        self.assertEqual(config, 'Some config path is broken.')

        # 4. Check missing default config.
        config = parse_config(default_config=None,
                              config_path='./tests/config/bad_log_analyzer.conf')

        self.assertEqual(config, 'No default config provided.')

    def test_find_latest_log(self):
        # 1. Find latest log if file, named like log, exists in dir.
        self.assertTrue(find_latest_log("./log").log_name)
        # 2. Returns None if there's no file, named like log, in dir.
        self.assertIsNone(find_latest_log("./tests/reports").log_name)
        # 3. Returns None if the file has bad naming for date.
        self.assertIsNone(find_latest_log("./tests/log/bad_log_name").log_date)

    def test_check_if_report_exists(self):
        # 1. Checks if example report exists.
        latest_log = namedtuple('latest_log', ['log_name', 'log_date'])
        latest_log.log_date = dt.datetime(2017, 11, 27, 0, 0)

        self.assertTrue(check_if_report_exists(latest_log=latest_log,
                                               report_dir="./tests/reports/"))

        # 2. Check that there's no report for non-existant log.
        latest_log.log_date = dt.datetime(2017, 12, 31, 0, 0)
        self.assertFalse(check_if_report_exists(latest_log=latest_log,
                                                report_dir="./tests/reports/"))

    def test_parse_log_gzip(self):

        try:
            access_log = list(parse_log(log_path='./tests/log/test_nginx-access-ui.log-20170630.gz', parser=parse_line))
        except Exception as e:
            print(f"Something's wrong: {e}")
            access_log = list()

        # 1. Checks if log is parsed at all.
        self.assertTrue(access_log)
        # 2. Checks if parsed access_log is list of dicts.
        self.assertIs(type(access_log[0]), dict)

    def test_parse_log_plain(self):
        try:
            access_log = list(parse_log(log_path='./tests/log/test_nginx-access-ui.log-20170630', parser=parse_line))
        except Exception as e:
            print(f"Something's wrong: {e}")
            access_log = list()

        # 1. Checks if log is parsed at all.
        self.assertTrue(access_log)
        # 2. Checks if parsed access_log is list of dicts.
        self.assertIs(type(access_log[0]), dict)

    def test_make_report_table(self):

        latest_log = find_latest_log(log_dir='./tests/log/')
        access_logs = parse_log(log_path=f'./tests/log/{latest_log.log_name}', parser=parse_line)

        try:
            report_table = make_report_table(access_logs, report_length=10)
        except Exception as e:
            print(f"Something is wrong: {e}")
            report_table = None

        # 1. Checks if report table is constructed.
        self.assertIsNotNone(report_table)
        # 2. Checks if report table is a list.
        self.assertIs(type(report_table), list)
        # 3. Checks if report table is a list of dicts.
        self.assertIs(type(report_table[0]), dict)
        # 4. Checks if report table is sorted properly.
        self.assertGreater(report_table[0]['time_sum'], report_table[1]['time_sum'])

    def test_render_html_report(self):
        latest_log = find_latest_log(log_dir='./tests/log/')
        access_log = parse_log(log_path=f'./tests/log/{latest_log.log_name}', parser=parse_line)
        report_length = 10
        report_table = make_report_table(access_log, report_length=report_length)

        new_report_date = latest_log.log_date.strftime("%Y.%m.%d")

        try:
            os.remove(f"./tests/reports/report-{new_report_date}.html")
        except OSError:
            pass

        render_result = render_html_report(table=report_table,
                                           report_path="./tests/reports/",
                                           latest_log_date=latest_log.log_date)

        # 1. Checks if report is created.
        self.assertTrue(render_result in os.listdir("./tests/reports/"))
        # 2. Checks if report has desired length.
        self.assertEqual(len(report_table), report_length)
