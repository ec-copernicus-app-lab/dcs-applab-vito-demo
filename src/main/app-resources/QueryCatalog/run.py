#!/opt/anaconda/bin/python

import sys
import os
import atexit
import commands
import tempfile
from datetime import *

# import the ciop functions (e.g. copy, log)

sys.path.append(os.environ['_CIOP_APPLICATION_PATH'] + '/util')

import cioppy
ciop = cioppy.Cioppy()

# define the exit codes
SUCCESS = 0
ERR_NOINPUTS = 1
ERR_INVALIDTYPE = 2
ERR_CATALOGQUERY = 3
ERR_DELETE = 4

# add a trap to exit gracefully
def clean_exit(exit_code):
    log_level = 'INFO'

    if exit_code != SUCCESS:
        log_level = 'ERROR'

    msg = { SUCCESS          : 'Querying VITO product catalogue successfully concluded',
            ERR_CATALOGQUERY : 'Querying VITO product catalogue failed',
            ERR_NOINPUTS     : 'No products found matching the given query fields',
            ERR_INVALIDTYPE  : 'Invalid product type specified (expected: BA, LAI or NDVI)',
            ERR_DELETE       : 'Cleaning up temporary data failed'}

    ciop.log(log_level, msg[exit_code])

def main():

    # get some user specified processing parameters
    startDate   = ciop.getparam('startdate')
    endDate     = ciop.getparam('enddate')
    producttype = ciop.getparam('type')

    ciop.log('INFO', 'Querying VITO product catalog: [StartDate = %s] [EndDate = %s] [Type = %s]' % (startDate, endDate, producttype))

    if   producttype == "BA":   type = "BioPar_BA300_V1_Global"
    elif producttype == "NDVI": type = "BioPar_NDVI_V2_Global"
    elif producttype == "LAI":  type = "BioPar_LAI_V2_Global"
    else:
        sys.exit(ERR_INVALIDTYPE);    

    results = []

    # execute docker container
    (tmpFd, tmpFn) = tempfile.mkstemp(suffix='.tmp', prefix='applab_', dir='/tmp', text=True);

    cmd = "docker run -v /tmp:/tmp " \
          "vito-docker-private.artifactory.vgt.vito.be/applab-data-customization:latest " \
          "python /home/worker/applab/query.py -startdate %s -enddate %s -type %s -out %s" % (startDate, endDate, type, tmpFn) 

    stat, out = commands.getstatusoutput(cmd);

    if stat != 0:
        ciop.log('ERROR', 'Querying VITO product catalogue failed: %s' % out);
        sys.exit(ERR_CATALOGQUERY)

    # retrieve list of results
    content = tmpFd.readlines();
    results = [x.strip()[7:] for x in content]    # Strip 'file://' from filenames

    tmpFd.close();

    if len(results) == 0:
        sys.exit(ERR_NOINPUTS);    

    ciop.log('INFO', 'Found %d products from VITO product catalog matching the given query fields' % len(results))

    # publish the results that have been found
    for result in results:
        published = ciop.publish(result)

    # cleanup results
    cmd = 'docker run -v /tmp:/tmp vito-docker-private.artifactory.vgt.vito.be/applab-data-customization:latest /bin/bash -c "rm -rf %s"' % tmpFn

    stat, out = commands.getstatusoutput(cmd);

    if stat != 0:
        ciop.log('ERROR', 'Cleaning up temporary data failed: %s' % out);
        sys.exit(ERR_DELETE)

try:
    main()
except SystemExit as e:
    if e.args[0]:
         clean_exit(e.args[0])
    raise
else:
    atexit.register(clean_exit, 0)
    
