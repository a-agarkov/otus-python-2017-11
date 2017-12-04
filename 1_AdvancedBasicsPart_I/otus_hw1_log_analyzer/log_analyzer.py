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

default_config = {"REPORT_SIZE": 1000,
                  "REPORT_DIR": "./reports",
                  "LOG_DIR": "./log"}

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s %(message)s',
                    datefmt='%Y.%m.%d %H:%M:%S',
                    stream=sys.stdout)


def timed(start_msg, finish_msg):
    def timed_func(func):
        def wrapped(*args, **kwargs):
            logging.info(start_msg)
            start = time()
            result = func(*args, **kwargs)
            logging.info(f'{finish_msg} {round(time() - start, 2)} seconds.')
            return result

        return wrapped

    return timed_func


def parse_config(default_config: dict,
                 main_config_path: str = './config/log_analyzer.conf') -> dict:
    """
    1. Checks whether main config exists at default path.
    2. Updates default config keys.
    3. Checks, whether any config file was passed in args.
    4. Updates config keys, if it was passed.
    5. Checks whether all dirs in config exist.
    6. Adds logging filehandler if it exists.

    :param default_config: default config file.
    :param main_config_path: main config file path.
    :return: log_analyzer config.
    """

    if os.path.exists(main_config_path):
        with open(main_config_path, mode='r') as f:
            main_config = json.load(f)
    else:
        logging.info("No default config at default path.")
        sys.exit(1)

    config = {k: v for k, v in default_config.items()}

    def update_config_params(config_to_update, config_from_file):
        # override config_to_update keys, if config_from_file contains them
        for key in config_to_update.keys():
            if key in config_from_file.keys():
                config_to_update[key] = config_from_file[key]
        # add new keys, if config_to_update doesn't have them
        for key in config_from_file.keys():
            if key not in config_to_update.keys():
                config_to_update[key] = config_from_file[key]

        return config_to_update

    config = update_config_params(config_to_update=config,
                                  config_from_file=main_config)

    # check for config path, passed via --config
    passed_config_path = None
    parser = argparse.ArgumentParser()
    parser.add_argument('--config')
    try:
        passed_config_path = parser.parse_args().config

    except Exception as e:
        logging.info(f"Something's wrong with passed config: {e}")

    passed_config = None
    if passed_config_path:
        logging.info('Got custom config path.')
        with open(passed_config_path, mode='r') as f:
            passed_config = json.load(f)

    if passed_config:
        config = update_config_params(config_to_update=config,
                                      config_from_file=passed_config)

    logging.info(f"Using custom config: {passed_config_path}."
                 if passed_config
                 else f"Using default config.")

    if not all((os.path.exists(config[k]) for k in config.keys() if k.endswith('DIR'))):
        logging.info(f"Some config path is broken.")
        sys.exit(1)

    # check if monitoring_log path is available in config
    # if monitoring_log path is in config, save to monitoring_log file
    if "MONITORING_LOG" in config.keys():
        formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
        fh = logging.FileHandler(config["MONITORING_LOG"])
        fh.setFormatter(formatter)
        logging.root.addHandler(fh)
        logging.info(f'Filehandler added successfully. Check logs here: {config["MONITORING_LOG"]}.')

    return config


def get_log_date(log_name):
    return dt.datetime.strptime((
        log_name.replace("nginx-access-ui.log-", "")
            .replace(".gz", "")
            .replace(".txt", "")
            .replace(".log", "")), "%Y%m%d")


def find_latest_log(log_dir: str):
    """
    Finds latest logfile in logs directory.

    :param log_dir:
    :return: name of the latest log or None if no log found.

    """
    log_files = {log_file: get_log_date(log_file)
                 for log_file
                 in os.listdir(log_dir) if 'nginx-access-ui.log' in log_file}

    if not log_files:
        return None

    return max(log_files.keys(), key=(lambda key: log_files[key]))

    # latest_log = max(log_files.keys(), key=(lambda key: log_files[key]))
    # if not latest_log:
    #     return None
    #
    # return latest_log if 'nginx-access-ui.log' in latest_log else None


def log_finish_timestamp():
    """
    Updates log_analyzer.ts with latest timestamp, if script has terminated successfully.
    """

    with open("./monitoring/log_analyzer.ts", mode='w') as f:
        f.write(f'{time()}')
    sys.exit(0)


def check_if_report_exists(latest_log: str, report_dir: str):
    """
    Checks if report for a certain log file already exists.

    :param latest_log: latest log file, according to mtime;
    :param report_dir: path to reports;
    :return: True if report already exists, False otherwise.
    """

    report_name = f'report-{get_log_date(latest_log).strftime("%Y.%m.%d")}.html'
    return report_name in os.listdir(report_dir)


@timed(start_msg=f'Parsing access log...',
       finish_msg='Access log parsed in')
def parse_log(log_path: str, max_lines: int = None) -> list:
    """
    Parses a log file.

    :param log_path: path to log file.
    :param max_lines: maximal number of records to pass, to be used for testing.
    :param test: True enables test protocol.

    :return: log, parsed according to a given format.
    """

    # define context function to open gzip or plain file
    open_within_context = gzip.GzipFile if log_path.endswith(".gz") else open

    with open_within_context(log_path, 'r') as f:
        if not max_lines:
            access_logs = (extract_contents_from_log_line(line.decode("utf-8")) for line in f)

        else:
            lines = []
            n = 0
            for line in f:
                lines.append(line)
                n += 1
                if n >= max_lines:
                    break
            access_logs = (extract_contents_from_log_line(line.decode("utf-8")) for line in lines)

        access_logs = list(access_logs)

    return access_logs


def extract_contents_from_log_line(line: str) -> dict:
    """
    Parses single record from a log according to log_pattern.

    :param line: UTF-8 encoded string of a log record.
    :return: dictionary, made up according to regex_log_pattern.
    """

    log_contents = {}
    request_time_pat = ' \d*[.]?\d*$'
    request_pat = '"(GET|POST)\s(?P<url>.+?)\sHTTP/.+"\s'

    log_contents['request_time'] = re.findall(request_time_pat, line)[0].strip()
    log_contents['request'] = re.findall(request_pat, line)
    if log_contents['request']:
        log_contents['request'] = log_contents['request'][0]

    return log_contents


# @timed(start_msg=f'Commencing access log parsing:',
#        finish_msg='Access log parsed in')
# def parse_log_old(log_path: str, log_format: str, max_lines: int = None) -> list:
#     """
#     Parses a log file.
#
#     :param log_path: path to log file.
#     :param log_format: log format
#     :param max_lines: maximal number of records to pass, to be used for testing.
#     :param test: True enables test protocol.
#
#     :return: log, parsed according to a given format.
#     """
#
#     regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in re.findall(r'\$(\w+)|(.)', log_format))
#
#     # define context function to open gzip or plain file
#     open_within_context = gzip.GzipFile if log_path.endswith(".gz") else open
#
#     with open_within_context(log_path, 'r') as f:
#         if not max_lines:
#             access_logs = (extract_contents_from_log_line_old(line.decode("utf-8"), regex) for line in f)
#
#         else:
#             lines = []
#             n = 0
#             for line in f:
#                 lines.append(line)
#                 n += 1
#                 if n >= max_lines:
#                     break
#             access_logs = (extract_contents_from_log_line_old(line.decode("utf-8"), regex) for line in lines)
#
#         access_logs = list(access_logs)
#
#     return access_logs
#
#
# def extract_contents_from_log_line_old(line: str, regex_log_pattern: str) -> dict:
#     """
#     Parses single record from a log according to log_pattern.
#
#     :param line: UTF-8 encoded string of a log record;
#     :param regex_log_pattern: regex for parsing single log record;
#     :return: dictionary, made up according to regex_log_pattern.
#     """
#     log_contents = re.match(regex_log_pattern, line).groupdict()
#     if not log_contents['request_time']:
#         log_contents['request_time'] = re.findall(' \d*[.]?\d*$', line)[0].strip()
#         # log_contents['request_time'] = re.findall('[\s\w+|(.)]{1, }\n$', line)[0].strip()
#
#     return log_contents


@timed(start_msg='Constructing report table...',
       finish_msg='Report table constructed successfully in')
def make_report_table(access_logs: list, report_length: int = 1000) -> list:
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
    :return: Data to insert into report.
    """

    logging.info(f'Getting data ready for statistics calculation...')
    for record in access_logs:
        record['url'] = record['request'][1] if len(record['request']) >= 2 else "-"
        record['request_method'] = record['request'][0] if len(record['request']) >= 2 else "-"

    urls = {record['url']: {"url": record['url'],
                            "count": 0,
                            "count_perc": 0,
                            "time_sum": 0,
                            "time_max": 0,
                            "time_avg": 0,
                            "time_med": 0,
                            "time_perc": 0}
            for record in access_logs}

    total_count = len(access_logs)
    total_time = sum([float(record['request_time']) for record in access_logs])

    logging.info(f'Calculating statistics...')
    for url, group in groupby(sorted(access_logs, key=lambda x: x['url']), key=lambda x: x['url']):
        req_times = [float(record['request_time']) for record in group]
        urls[url]['count'] = len(req_times)
        urls[url]['time_sum'] = sum(req_times)
        urls[url]['time_max'] = max(req_times)
        urls[url]['time_med'] = median(req_times)
        urls[url]['time_avg'] = mean(req_times)
        urls[url]['time_perc'] = urls[url]['time_sum'] / total_time
        urls[url]['count_perc'] = urls[url]['count'] / total_count

    report_table = sorted(list(urls.values()), key=lambda k: k['time_sum'], reverse=True)

    if report_length >= len(report_table):
        return report_table
    else:
        return report_table[:report_length]


@timed(start_msg='Rendering report...',
       finish_msg='Report rendered successfully in')
def render_html_report(table: list,
                       report_path: str,
                       log_name: str) -> str:
    """
    Renders html report from dummy 'report.html'.

    :param table: Data to insert into dummy report.
    :param report_path: Path to dummy 'report.html'.
    :param log_name: Name of the logfile, used to make a date for a new report.
    :return: Returns name of freshly rendered report.

    """

    report_as_list = []
    with open(f"{report_path}/report.html", mode='r') as f:
        report_as_list = [line for line in f]

    report_as_list[64] = f'    var table = {json.dumps(table)};\n'

    latest_log_datetime_str = (log_name
        .replace("nginx-access-ui.log-", "")
        .replace(".gz", "")
        .replace(".txt", "")
        .replace(".log", ""))
    new_report_date = dt.datetime.strptime(latest_log_datetime_str, "%Y%m%d").strftime("%Y.%m.%d")

    with open(f"{report_path}/report-{new_report_date}.html", mode='w') as f:
        for line in report_as_list:
            f.writelines(str(line))

    return f"report-{new_report_date}.html"


def main(default_config=default_config,
         main_config_path='./config/log_analyzer.conf'):

    logging.info("Starting log_analyzer")

    config = parse_config(default_config=default_config,
                          main_config_path=main_config_path)

    # find latest access log
    log_name = find_latest_log(log_dir=config['LOG_DIR'])

    if not log_name:
        logging.info(f"No logs found in LOG_DIR: {config['LOG_DIR']}")
        sys.exit(1)

    logging.info(f"Latest log found: {log_name}")

    # check if report has already been created for this access log
    if check_if_report_exists(latest_log=log_name, report_dir=config["REPORT_DIR"]):
        logging.info(f"Report for latest logfile {log_name} already exists.")
        log_finish_timestamp()

    logging.info(f"No report found for {log_name}.")

    # parse log
    access_logs = parse_log(log_path=f'{config["LOG_DIR"]}/{log_name}')

    # make a report
    report_table = make_report_table(access_logs=access_logs, report_length=config['REPORT_SIZE'])

    # render html report
    render_result = render_html_report(table=report_table, report_path=config['REPORT_DIR'], log_name=log_name)

    if render_result:
        logging.info(f"New report {render_result} successfully rendered.")
        log_finish_timestamp()

    else:
        logging.error(f"Report render failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()