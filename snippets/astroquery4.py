#!/usr/bin/env python3

import numpy
import sys
import boto3
import astropy.io.fits

from astroquery.mast import Observations

s3 = boto3.resource('s3')
stpubdata = s3.Bucket('stpubdata')

Observations.enable_s3_hst_dataset()
obs = Observations.query_criteria(
    project='HST',
    instrument_name='ACS/WFC',
)
print("Observations: ", len(obs), file=sys.stderr)

proposal_ids = numpy.unique(obs['proposal_id'])
print("Proposals: ", len(proposal_ids), file=sys.stderr)

shape_tally = {}

for prop in proposal_ids:
    proposal_obs = Observations.query_criteria(
        project='HST',
        instrument_name='ACS/WFC',
        proposal_id=[prop],
    )

    products = Observations.get_product_list(proposal_obs)
    print("Products for proposal %s: %d" % (prop, len(products)), file=sys.stderr)

    filtered_products = Observations.filter_products(
        products,
        mrp_only=False,
        productSubGroupDescription='RAW',
        extension='fits',
    )
    print("RAW products for proposal %s: %d" % (prop, len(filtered_products)), file=sys.stderr)

    if len(filtered_products) > 0:
        s3_uris = Observations.get_hst_s3_uris(filtered_products)
        for uri in s3_uris:
            key = uri.replace("s3://stpubdata/", "")
            print("Getting %s" % uri, file=sys.stderr)
            stpubdata.download_file(key, 'temp.fits', ExtraArgs={"RequestPayer": "requester"})
            fits = astropy.io.fits.getdata('temp.fits')
            print("{0},{1},{2},{3}".format(prop, key.split('/')[-1], fits.shape[0], fits.shape[1]))
            if shape_tally.get(fits.shape) is None:
                shape_tally[fits.shape] = 1
            else:
                shape_tally[fits.shape] += 1

print("\n\n")
print(shape_tally)
