# Log analyzer script
### Description
According to the project task, this script should be used to parse nginx access logs and render a report page 
with a subset of n records for urls, which have the highest total request time statistics. 

### Input
Script is designed to parse `.gz` and plain logs.

It has one optional argument `--config` for a path to config file. 

The config must have following fields:
* `REPORT_SIZE` - size of subset for report;
* `REPORT_DIR` - path to reportsm rendered by script, a dummy report `report.html` should always stay in that folder; 
* `LOG_DIR` - path to a folder for nginx access logs;
* `TIMESTAMP_DIR` - path to a folder, where script writes latest completion timestamp.

Arbitrary arguments could be provided within config file, like:
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

### Code author
Алексей Агарков

slack: Alexey Agarkov (Alex_A)
