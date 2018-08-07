#!/usr/bin/env python3

from astroquery.mast import Observations

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
print("Downloading first 3 products")

Observations.download_products(filtered_products[0:3])
