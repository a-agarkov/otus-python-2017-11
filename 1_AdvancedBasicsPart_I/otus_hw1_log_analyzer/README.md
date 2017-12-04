# Log analyzer script
### Description
According to the project task, this script should be used to parse nginx access logs and render a report page 
with a subset of n records for urls, which have the highest total request time statistics. 

### Input
Script is designed to parse `.gz` and plain logs.

The default config has following fields:
* `REPORT_SIZE` - size of subset for report;
* `REPORT_DIR` - path to reportsm rendered by script, a dummy report `report.html` should always stay in that folder; 
* `LOG_DIR` - path to a folder for nginx access logs.

Script has one optional argument `--config` for a path to a custom config file. 
Custom config overrides default fields (if included in custom config).  Arbitrary arguments could be provided within custom config file:
* `MONITORING_LOG` - filepath to script monitoring log output.

### Output
Script produces a report for the latest access log and stores it in `reports` folder. 

Rendered report will have access log's date. Example: `report-2017.06.30.html`.

A `.ts` file with latest execution timestamp would be produced and stored within `monitoring` folder.

Script will check if a report has already been rendered for the latest log and will terminate with due message. 

### Usage
1. Copy nginx access log into `log` folder within `log_analyzer.py` working directory. 
2. nginx access log naming should adhere to following convention `nginx-access-ui.log-<%Y%m%d>`.  E.g. `nginx-access-ui.log-20170630.gz`.
3. The `log_analyzer.py` should be called from command line with or without arguments.

### Run examples
To run `log_analyzer` with default configuration from command line:

`python log_analyzer.py`

And with custom configuration:

`python log_analyzer.py --config "config/log_analyzer.conf"`

### Tests
A test suite is provided with complete environment (config file, folders, etc.).

To perform tests, run from command line:

`python -m unittest tests/test_log_analyzer_tests.py`

### Code author
Алексей Агарков

slack: Alexey Agarkov (Alex_A)
