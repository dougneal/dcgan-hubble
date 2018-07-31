#!/usr/bin/env python3

from astroquery.mast import Observations
import IPython
import boto3

from s3_query import find_product_in_s3

Observations.enable_s3_hst_dataset()

obs = Observations.query_criteria(
    dataproduct_type=['image'],
    project='HST',
    instrument_name='ACS/WFC',
    filters='F555W',
    calib_level=3,
)

print("Observations: ", len(obs))

products = Observations.get_product_list(obs)
print("Products: ", len(products))

filtered_products = Observations.filter_products(
    products,
    productType='SCIENCE',
    extension='fits',
    description='DADS FLT file - Calibrated exposure ACS/WFC3/STIS/COS',
)
print("Filtered products: ", len(filtered_products))
print()

s3 = boto3.resource('s3')

for prod in filtered_products:
    (key, head) = find_product_in_s3(prod)
    filename = key.split('/').pop()
    print("Downloading ", filename)
    s3.Bucket("stpubdata").download_file(
        key, filename,
        {'RequestPayer':'requester'}
    )

