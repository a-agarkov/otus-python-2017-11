from unittest import TestCase
import os
import datetime as dt
from log_analyzer import find_latest_log, check_if_report_exists, parse_log, make_report_table, render_html_report
from itertools import groupby
from statistics import median, mean

default_config = {"REPORT_SIZE": 1000,
                  "REPORT_DIR": "./reports",
                  "LOG_DIR": "./log",
                  "TIMESTAMP_PATH": "./monitoring/log_analyzer.ts",
                  "MONITORING_LOG": './monitoring/log_analyzer.log'}
default_log_format = f'$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" ' \
                         f'$status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' \
                         f'"$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time'


class TestLogAnalyzer(TestCase):
    def test_find_latest_log(self):
        # 1. Find latest log if file, named like log, exists in dir.
        self.assertTrue(find_latest_log("./log"))
        # 2. Returns None if there's no file, named like log, in dir.
        self.assertIsNone(find_latest_log("./reports"))

    def test_check_if_report_exists(self):
        # 1. Checks if example report exists.
        self.assertTrue(check_if_report_exists(latest_log='nginx-access-ui.log-20171127',
                                               report_dir="./tests/test_reports/"))

        # 2. Check that there's no report for non-existant log.
        self.assertFalse(check_if_report_exists(latest_log='nginx-access-ui.log-20171231',
                                                report_dir="./tests/test_reports/"))

    def test_parse_log(self):

        log_name = find_latest_log(log_dir=default_config['LOG_DIR'])
        max_lines = 10
        try:
            access_log = parse_log(log_path=f'{default_config["LOG_DIR"]}/{log_name}',
                                   log_format=default_log_format,
                                   max_lines=max_lines,
                                   test=True)
        except Exception as e:
            print(f"Something's wrong: {e}")
            access_log = None

        # 1. Checks if log is parsed at all.
        self.assertIsNotNone(access_log)
        # 2. Checks if parsed access_log is list.
        self.assertIs(type(access_log), list)
        # 3. Checks if parsed access_log is list of dicts.
        self.assertIs(type(access_log[0]), dict)
        # 4. Checks length of parsed access_log is exactly max_lines (test of test protocol).
        self.assertEquals(len(access_log), max_lines)

    def test_make_report_table(self):

        log_name = find_latest_log(log_dir=default_config['LOG_DIR'])
        max_lines = 10
        access_logs = parse_log(log_path=f'{default_config["LOG_DIR"]}/{log_name}',
                               log_format=default_log_format,
                               max_lines=max_lines,
                               test=True)

        # for record in access_logs:
        #     request = record['request'].split()
        #     record['url'] = request[1] if len(request) >= 2 else "-"
        #     record['request_method'] = request[0] if len(request) >= 2 else "-"
        #
        # urls = {record['url']: {"url": record['url'],
        #                         "count": 0,
        #                         "count_perc": 0,
        #                         "time_sum": 0,
        #                         "time_max": 0,
        #                         "time_avg": 0,
        #                         "time_med": 0,
        #                         "time_perc": 0}
        #         for record in access_logs}
        #
        # access_logs
        # total_count = len(access_logs)
        # total_time = sum([float(record['request_time']) for record in access_logs])
        #
        # for url, group in groupby(sorted(access_logs, key=lambda x: x['url']), key=lambda x: x['url']):
        #     time = [float(record['request_time']) for record in group]
        #     urls[url]['count'] = len(time)
        #     urls[url]['time_sum'] = sum(time)
        #     urls[url]['time_max'] = max(time)
        #     urls[url]['time_med'] = median(time)
        #     urls[url]['time_avg'] = mean(time)
        #     urls[url]['time_perc'] = urls[url]['time_sum'] / total_time
        #     urls[url]['count_perc'] = urls[url]['count'] / total_count

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

        # 5. Checks if report length is less than access log length.
        report_length_5 = make_report_table(access_logs, report_length=5)
        self.assertEquals(len(report_length_5), 5)

        # 6. Checks if report length is equal to access log length
        report_length_10 = make_report_table(access_logs, report_length=10)
        self.assertEquals(len(report_length_10), 10)

        # 7. Checks if report length is greater than actual access log length
        report_length_20 = make_report_table(access_logs, report_length=20)
        self.assertGreater(20, len(report_length_20))

    def test_render_html_report(self):
        log_name = find_latest_log(log_dir=default_config['LOG_DIR'])
        max_lines = 10
        access_log = parse_log(log_path=f'{default_config["LOG_DIR"]}/{log_name}',
                               log_format=default_log_format,
                               max_lines=max_lines,
                               test=True)

        report_table = make_report_table(access_log, report_length=10)

        latest_log_datetime_str = (log_name
                                   .replace("nginx-access-ui.log-", "")
                                   .replace(".gz", "")
                                   .replace(".txt", "")
                                   .replace(".log", ""))
        new_report_date = dt.datetime.strptime(latest_log_datetime_str, "%Y%m%d").strftime("%Y.%m.%d")

        try:
            os.remove(f"./tests/test_reports/report-{new_report_date}.html")
        except OSError:
            pass

        render_result = render_html_report(table=report_table,
                                           report_path="./tests/test_reports/",
                                           log_name=log_name)

        # 1. Checks if report is created.
        self.assertTrue(f"report-{new_report_date}.html" in os.listdir("./tests/test_reports/"))






