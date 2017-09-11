#!/opt/anaconda/bin/python

import sys
import os
import atexit
import datetime

sys.path.append(os.environ['_CIOP_APPLICATION_PATH'] + '/util')

# import the ciop functions (e.g. copy, log)

import cioppy
ciop = cioppy.Cioppy()

# import catalog client
from catalogclient import catalog

# define the exit codes
SUCCESS = 0
ERR_NOINPUTS = 1
ERR_INVALIDTYPE = 2

# add a trap to exit gracefully
def clean_exit(exit_code):
    log_level = 'INFO'

    if exit_code != SUCCESS:
        log_level = 'ERROR'

    msg = { SUCCESS         : 'Querying VITO product catalogue successfully concluded',
            ERR_NOINPUTS    : 'No products found matching the given query fields',
            ERR_INVALIDTYPE : 'Invalid product type specified (expected: BA, LAI or NDVI)'}

    ciop.log(log_level, msg[exit_code])

def main():

    # get some user specified processing parameters
    startDate   = ciop.getparam('startdate')
    endDate     = ciop.getparam('enddate')
    producttype = ciop.getparam('type')

    ciop.log('INFO', 'Querying VITO product catalog: [StartDate = %s] [EndDate = %s] [Type = %s]' (startdate, enddate, roi, producttype))

    if   producttype == "BA":   type = "BioPar_BA300_V1_Global"
    elif producttype == "NDVI": type = "BioPar_NDVI_V2_Global"
    elif producttype == "LAI":  type = "BioPar_LAI_V2_Global"
    else:
        sys.exit(ERR_INVALIDTYPE);

    dt1 = datetime.strptime(startDate, "%Y%m%d");
    dt2 = datetime.strptime(endDate, "%Y%m%d");

    # query catalog matching the given fields
    catalog=catalog.Catalog()

    products = catalog.get_products(type, startdate=dt1.date(), enddate=dt2.date());

    # check whether any matches have been found
    if len(products) == 0:
        sys.exit(ERR_NOINPUTS);

    results = []

    # retrieve the local filenames
    for product in products:

        inputfile = product.files[0].filename

        if inputfile.startswith("file:"):
            inputfile = 'file://' + inputfile[5:]

        # retrieve the file to the local temporary folder TMPDIR provided by the framework (this folder is only used by this process).
        retrieved = ciop.copy(inputfile, ciop.tmp_dir)
        ciop.log('INFO', 'Retrieved ' + os.path.basename(retrieved))

        assert(retrieved)

        results.append(inputfile);

    ciop.log('INFO', 'Found ' + len(results) + ' products matching the given query fields')

    # publish the results that have been found
    published = ciop.publish(results)

try:
    main()
except SystemExit as e:
    if e.args[0]:
         clean_exit(e.args[0])
    raise
else:
    atexit.register(clean_exit, 0)
    
