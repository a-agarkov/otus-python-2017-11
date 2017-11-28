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
from time import time
from itertools import groupby


utcnow = dt.datetime.utcnow


def init_logger(logger_name: str,
                formatter: object) -> object:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    new_logger = logging.getLogger(logger_name)
    new_logger.addHandler(console_handler)
    new_logger.setLevel(logging.DEBUG)

    return new_logger


def main(config_path=None, logger=None):
    global default_log_format
    global default_config
    global default_logger_formatter

    if not logger:
        logger = init_logger(logger_name="monitoring_logger", formatter=default_logger_formatter)

    logger.info("Starting log_analyzer")

    # check for config path, passed via --config

    passed_config = None
    if config_path:
        logger.info('Got custom config path.')
        passed_config = read_custom_config(path=config_path)
        if passed_config == "Required directories are missing.":
            logger.info(passed_config)
            passed_config = None

    # get default config if no config passed
    config = passed_config if passed_config else default_config
    logger.info(f"Using custom config: {passed_config_path}."
                if passed_config_path
                else f"Using default config.")

    if not all((os.path.exists(config[k]) for k in config.keys() if k.endswith('DIR'))):
        logger.info(f"Some config path is broken.")

        with open(f'{config["TIMESTAMP_DIR"]}/log_analyzer.ts', mode='w') as f:
            f.write(f'{utcnow().timestamp()}')

        sys.exit(0)

    # check if monitoring_log path is available in config
    # if monitoring_log path is in config, save to monitoring_log file
    if "MONITORING_LOG" in config.keys():
        logger_fh = logging.FileHandler(config["MONITORING_LOG"])
        logger_fh.setFormatter(default_logger_formatter)
        logger.addHandler(logger_fh)
        logger.info(f'Filehandler added successfully. Check logs here: {config["MONITORING_LOG"]}.')

    # find latest access log
    log_name = find_latest_log(log_dir=config['LOG_DIR'])

    if not log_name:
        logger.info(f"No logs found in LOG_DIR: {config['LOG_DIR']}")

        with open(f'{config["TIMESTAMP_DIR"]}/log_analyzer.ts', mode='w') as f:
            f.write(f'{utcnow().timestamp()}')

        sys.exit(0)

    logger.info(f"Latest log found: {log_name}")

    # check if report has already been created for this access log
    report_exists = check_if_report_exists(latest_log=log_name,
                                           report_dir=config["REPORT_DIR"])

    if report_exists:
        logger.info(f"Report for latest logfile {log_name} already exists.")

        with open(f'{config["TIMESTAMP_DIR"]}/log_analyzer.ts', mode='w') as f:
            f.write(f'{utcnow().timestamp()}')

        return sys.exit(0)

    logger.info(f"No report found for {log_name}.")

    # check if log format available in config
    log_format = config['LOG_FORMAT'] if 'LOG_FORMAT' in config.keys() else default_log_format
    logger.info(f"Using custom log format."
                if 'LOG_FORMAT' in config.keys()
                else f"No custom log format provided in config. Using default log format.")

    # parse log
    log_path = f'{config["LOG_DIR"]}/{log_name}'
    logger.info(f'Commencing access log parsing: {log_path}')
    parse_start = time()
    access_logs = parse_log(log_path=log_path,
                            log_format=log_format,
                            max_lines=config['REPORT_SIZE'])

    logger.info(f'Access log parsed in {time() - parse_start}')

    # make a report, if no report for this access log
    logger.info(f"Constructing report table...")
    report_construction_start = time()
    report_table = make_report_table(access_logs=access_logs,
                                     report_length=config['REPORT_SIZE'],
                                     logger=logger)
    logger.info(f"Report table constructed successfully in {time() - report_construction_start}.")

    # render html report
    logger.info(f"Rendering report...")
    render_result = render_html_report(table=report_table,
                                       report_path=config['REPORT_DIR'],
                                       log_name=log_name)

    if render_result:
        logger.info(f"New report {render_result} successfully rendered.")
        with open(f'{config["TIMESTAMP_DIR"]}/log_analyzer.ts', mode='w') as f:
            f.write(f'{utcnow().timestamp()}')

        sys.exit(0)

    else:
        logger.error(f"Report render failed.")
        with open(f'{config["TIMESTAMP_DIR"]}/log_analyzer.ts', mode='w') as f:
            f.write(f'{utcnow().timestamp()}')

        sys.exit(1)


def find_latest_log(log_dir: str):
    """
    Finds latest logfile in logs directory.

    :param log_dir:
    :return: name of the latest log or None if no log found.

    """
    log_files = {log_file: os.path.getmtime(f'{log_dir}/{log_file}')
                 for log_file
                 in os.listdir(log_dir)}
    latest_log = max(log_files.keys(),
                     key=(lambda key: log_files[key]))
    if not latest_log:
        return None

    return latest_log if 'nginx-access-ui.log' in latest_log else None


def read_custom_config(path: str):
    with open(path, mode='r') as f:
        custom_config = json.load(f)

    if all((k in custom_config for k in ("REPORT_SIZE", "REPORT_DIR", "LOG_DIR", "TIMESTAMP_DIR"))):
        return custom_config
    else:
        return "Required directories are missing."


def check_if_report_exists(latest_log: str, report_dir: str):
    """
    Checks if report for a certain log file already exists.

    :param latest_log: latest log file, according to mtime;
    :param report_dir: path to reports;
    :return: True if report already exists, False otherwise.
    """

    latest_log_datetime_str = (latest_log
                               .replace("nginx-access-ui.log-", "")
                               .replace(".gz", "")
                               .replace(".txt", "")
                               .replace(".log", ""))

    report_name = f'report-{dt.datetime.strptime(latest_log_datetime_str, "%Y%m%d").strftime("%Y.%m.%d")}.html'
    return report_name in os.listdir(report_dir)


def parse_log(log_path: str, log_format: str, max_lines: int, test: bool = False) -> list:
    """
    Parses a log file.

    :param log_path: path to log file.
    :param log_format: log format
    :param max_lines: maximal number of records to pass, to be used for testing.
    :param test: True enables test protocol.

    :return: log, parsed according to a given format.
    """

    regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c)
                    for g, c in re.findall(r'\$(\w+)|(.)', log_format))

    # define context function to open gzip or plain file
    open_within_context = gzip.GzipFile if log_path.endswith(".gz") else open

    with open_within_context(log_path, 'r') as f:
        if not test:
            access_logs = (extract_contents_from_log_line(line.decode("utf-8"), regex)
                           for line in f)

        else:
            lines = []
            n = 0
            for line in f:
                lines.append(line)
                n += 1
                if n >= max_lines:
                    break
            access_logs = (extract_contents_from_log_line(line.decode("utf-8"), regex)
                           for line in lines)

        access_logs = list(access_logs)

    return access_logs


def extract_contents_from_log_line(line: str, regex_log_pattern: str) -> dict:
    """
    Parses single record from a log according to log_pattern.

    :param line: UTF-8 encoded string of a log record;
    :param regex_log_pattern: regex for parsing single log record;
    :return: dictionary, made up according to regex_log_pattern.
    """
    log_contents = re.match(regex_log_pattern, line).groupdict()
    if not log_contents['request_time']:
        log_contents['request_time'] = re.findall(' \d*[.]?\d*$', line)[0].strip()
        # log_contents['request_time'] = re.findall('[\s\w+|(.)]{1, }\n$', line)[0].strip()

    return log_contents


def make_report_table(access_logs: list, report_length: int = 1000, logger: object = None) -> list:
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

    if logger:
        logger.info(f'Getting data ready for statistics calculation...')
    for record in access_logs:
        request = record['request'].split()
        record['url'] = request[1] if len(request) >= 2 else "-"
        record['request_method'] = request[0] if len(request) >= 2 else "-"

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

    if logger:
        logger.info(f'Calculating statistics...')
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


if __name__ == "__main__":

    default_log_format = f'$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" ' \
                         f'$status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' \
                         f'"$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time'

    default_config = {"REPORT_SIZE": 1000,
                      "REPORT_DIR": "./reports",
                      "LOG_DIR": "./log",
                      "TIMESTAMP_DIR": "./monitoring",
                      "MONITORING_LOG": './monitoring/log_analyzer.log'}
    default_logger_formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s',
                                                 datefmt='%Y.%m.%d %H:%M:%S')

    passed_config_path = None
    parser = argparse.ArgumentParser()
    parser.add_argument('--config')
    try:
        passed_config_path = parser.parse_args().config

    except Exception as e:
        print(f"Something's wrong: {w}")
        passed_config_path = None

    main(config_path=passed_config_path)
