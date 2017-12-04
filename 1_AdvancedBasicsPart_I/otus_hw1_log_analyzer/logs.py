#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import sys


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s %(message)s',
                    datefmt='%Y.%m.%d %H:%M:%S',
                    stream=sys.stdout)

formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
fh = logging.FileHandler("./monitoring/log_analyzer.log")
fh.setFormatter(formatter)
logging.root.addHandler(fh)

logging.info(f'Filehandler added successfully. Checking filehandler formatting.')
