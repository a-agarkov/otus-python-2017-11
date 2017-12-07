#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import json
import re
import logging
import sys
import datetime as dt
import os
from statistics import median, mean
import argparse
from time import time, sleep
from itertools import groupby
from collections import namedtuple
from string import Template
from functools import partial

default_config = {"REPORT_SIZE": 1000,
                  "REPORT_DIR": "./reports",
                  "LOG_DIR": "./log"}


def parse_config(default_config: dict = None,
                 config_path: str = None):
    """
    1. Checks whether main config exists at default path.
    2. Updates default config keys.
    3. Checks, whether any config file was passed in args.
    4. Updates config keys, if it was passed.
    5. Checks whether all dirs in config exist.

    :param default_config: default config file.
    :param config_path: main config file path.
    :return: log_analyzer config.
    """

    if not default_config:
        return "No default config provided."

    config = {k: v for k, v in default_config.items()}

    if os.path.exists(config_path):
        with open(config_path, mode='r') as f:
            main_config = json.load(f)
    else:
        return "No config at given path."

    config.update(main_config)

    if not all((os.path.exists(config[k]) for k in config.keys() if k.endswith('DIR'))):
        return "Some config path is broken."

    return config


def find_latest_log(log_dir: str):
    """
    Finds latest logfile in logs directory.

    :param log_dir:
    :return: name of the latest log or None if no log found.

    """

    def get_log_date(log_name):
        return dt.datetime.strptime(re.search('\d{4}\d{2}\d{2}', log_name).group(0), "%Y%m%d")

    latest_log = max((item for item in os.listdir(log_dir) if 'nginx-access-ui.log' in item),
                     key=lambda log_name: get_log_date(log_name),
                     default=None)

    return namedtuple('latest_log', ['log_name', 'log_date'])(
        latest_log, get_log_date(latest_log) if latest_log else None)


def log_finish_timestamp():
    """
    Updates log_analyzer.ts with latest timestamp, if script has terminated successfully.
    """

    with open("./monitoring/log_analyzer.ts", mode='w') as f:
        f.write(f'{time()}')
    sys.exit(0)


def check_if_report_exists(latest_log, report_dir: str):
    """
    Checks if report for a certain log file already exists.

    :param latest_log: latest log named tuple with log_date;
    :param report_dir: path to reports;
    :return: True if report already exists, False otherwise.
    """
    return os.path.exists(f'{report_dir}/report-{latest_log.log_date.strftime("%Y.%m.%d")}.html')


def parse_log(log_path: str, parser) -> list:
    """
    Parses a log file.

    :param log_path: path to log file.
    :param max_lines: maximal number of records to pass, to be used for testing.

    :return: log, parsed according to a given format.
    """

    open_log = partial(gzip.open, mode='rt', encoding="utf-8") if log_path.endswith(".gz") else partial(open, mode='r')
    with open_log(log_path) as f:
        for line in f:
            yield parser(line)


def parse_line(line: str) -> dict:
    """
    Parses single record from a log according to log_pattern.

    :param line: UTF-8 encoded string of a log record.
    :return: dictionary, made up according to regex_log_pattern.
    """

    log_contents = {}
    request_time_pat = ' \d*[.]?\d*$'
    request_pat = '"(GET|POST)\s(?P<url>.+?)\sHTTP/.+"\s'

    log_contents['request_time'] = re.findall(request_time_pat, line)[0].strip()
    request = re.findall(request_pat, line)
    log_contents['request'] = request[0][1] if request else "parse_failed"

    return log_contents


def make_report_table(access_logs: list, report_length: int = 1000, error_threshold: float = 0.05) -> list:
    """
    Calculates following statistics for all URLs within access log:
     - count of visits to a URL;
     - URL visit count percentage to total visits during log period;
     - total time of response for a given URL;
     - longest response time for a given URL;
     - average response time for a given URL;
     - median response time for a given URL;
     - percentage of total response time for a given URL to total response time of all URLs.

    :param access_logs: Parsed access log records.
    :param report_length: Report length.
    :param error_threshold: Sets parsing error threshold.
        Raises a warning if percent of urls, parsed correctly, is less than threshold.
    :return: Data to insert into report.
    """

    logging.info('Preparing data for statistics calculation...')

    urls = {}
    logging.info('Calculating statistics...')
    for url, group in groupby(sorted(access_logs, key=lambda x: x['request']), key=lambda x: x['request']):
        req_times = [float(record['request_time']) for record in group]
        urls[url] = {"url": url,
                     'count': len(req_times),
                     'time_sum': sum(req_times),
                     'time_max': max(req_times),
                     'time_med': median(req_times),
                     'time_avg': mean(req_times)}

    total_time = sum([record['time_sum'] for record in urls.values()])
    total_records = sum([record['count'] for record in urls.values()])
    failed_parse = urls["parse_failed"]['count'] if "parse_failed" in urls.keys() else 0

    if failed_parse / total_records >= error_threshold:
        return f"Failed to parse {round(failed_parse / total_records, 2) * 100}% records."

    for url in urls.keys():
        urls[url]['time_perc'] = urls[url]['time_sum'] / total_time
        urls[url]['count_perc'] = urls[url]['count'] / total_records

    report_table = sorted(list(urls.values()), key=lambda k: k['time_sum'], reverse=True)

    return report_table[:report_length]


def render_html_report(table: list,
                       report_path: str,
                       latest_log_date) -> str:
    """
    Renders html report from dummy 'report.html'.

    :param table: Data to insert into dummy report.
    :param report_path: Path to dummy 'report.html'.
    :param latest_log: Name of the logfile, used to make a date for a new report.
    :return: Returns name of freshly rendered report.

    """

    with open(os.path.join(report_path, "report.html"), mode='r') as f:
        report = f.read()

    new_report_name = f"report-{latest_log_date.strftime('%Y.%m.%d')}.html"

    with open(os.path.join(report_path, new_report_name), mode='w') as f:
        f.write(Template(report).safe_substitute(table_json=json.dumps(table)))

    return new_report_name


def main(config: dict = None):
    """
    Main procedure flow:
    1. Looks for latest log;
    2. Checks if report for this log already exists;
    3. Parses the log;
    4. Makes report table;
    5. Renders HTML report.

    :param config: Configuration dict.
    """

    # find latest access log
    latest_log = find_latest_log(log_dir=config['LOG_DIR'])

    if not latest_log.log_name:
        logging.info(f"No logs found in LOG_DIR: {config['LOG_DIR']}")
        sys.exit(0)

    logging.info(f"Latest log found: {latest_log.log_name}")

    # check if report has already been created for this access log
    if check_if_report_exists(latest_log=latest_log,
                              report_dir=config["REPORT_DIR"]):
        logging.info(f"Report for latest logfile {latest_log.log_name} already exists.")
        log_finish_timestamp()

    logging.info("No report found for latest_log.")

    # parse log
    logging.info(f"Parsing {latest_log.log_name}...")
    access_logs = parse_log(log_path=os.path.join(config["LOG_DIR"], latest_log.log_name), parser=parse_line)

    # make a report
    report_table = make_report_table(access_logs=access_logs,
                                     report_length=config['REPORT_SIZE'])

    if isinstance(report_table, str):
        logging.error(report_table)
        sys.exit(1)

    # render html report
    logging.info("Rendering report...")
    render_result = render_html_report(table=report_table,
                                       report_path=config['REPORT_DIR'],
                                       latest_log_date=latest_log.log_date)

    if render_result:
        logging.info(f"New report {render_result} successfully rendered.")
        log_finish_timestamp()

    else:
        logging.error("Report render failed.")
        sys.exit(1)


if __name__ == "__main__":

    # check for config path, passed via --config
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--config', default='./config/log_analyzer.conf')

    config = parse_config(default_config=default_config,
                          config_path=argument_parser.parse_args().config)

    if isinstance(config, str):
        logging.error(config)
        sys.exit(1)

    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S',
                        filename=config.get("MONITORING_LOG", None))

    logging.info("Starting log_analyzer")

    try:
        main(config=config)
    except Exception as e:
        logging.error(f'Something is wrong: {e}')
