#!/usr/bin/env python3

#
#

from astroquery.mast import Observations

import boto3
import json
import os

import IPython

wfc = Observations.query_criteria(
    dataproduct_type=['image'],
    project='HST',
    instrument_name='ACS/WFC',
)
print("WFC: ", len(wfc))

hrc = Observations.query_criteria(
    dataproduct_type=['image'],
    project='HST',
    instrument_name='ACS/HRC',
)
print("HRC: ", len(hrc))

IPython.embed()

