#!/usr/bin/env python3

import numpy
from astroquery.mast import Observations

obs = Observations.query_criteria(
    project='HST',
    instrument_name='ACS/WFC',
)
print("Observations: ", len(obs))

proposal_ids = numpy.unique(obs['proposal_id'])
print("Proposals: ", len(proposal_ids))

for prop in proposal_ids:
    proposal_obs = Observations.query_criteria(
        project='HST',
        instrument_name='ACS/WFC',
        proposal_id=[prop],
    )

    products = Observations.get_product_list(proposal_obs)
    print("Products for proposal %s: %d" % (prop, len(products)))

    filtered_products = Observations.filter_products(
        products,
        mrp_only=False,
        productSubGroupDescription='RAW',
        extension='fits',
    )
    print("RAW products for proposal %s: %d" % (prop, len(filtered_products)))

    if len(filtered_products) > 0:
        print("Downloading")
        manifest = Observations.download_products(filtered_products, mrp_only=False)
        print(manifest)
