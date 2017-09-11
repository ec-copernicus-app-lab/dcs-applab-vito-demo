#!/opt/anaconda/bin/python

import sys
import os
import atexit

sys.path.append(os.environ['_CIOP_APPLICATION_PATH'] + '/util')

# import the ciop functions (e.g. copy, log)

import cioppy
ciop = cioppy.Cioppy()

# define the exit codes
SUCCESS = 0
ERR_CUSTOMIZATION = 1

# add a trap to exit gracefully
def clean_exit(exit_code):
    log_level = 'INFO'

    if exit_code != SUCCESS:
        log_level = 'ERROR'

    msg = { SUCCESS           : 'Product customization concluded successfully',
            ERR_CUSTOMIZATION : 'Failed to customize product'}

    ciop.log(log_level, msg[exit_code])

def main():

    # retrieve some customization parameters
    roi = ciop.getparam('roi')

    # Input references come from STDIN (standard input) and they are retrieved
    # line-by-line.
    for input in sys.stdin:
        
        ciop.log('INFO', 'Input = %s' % input)


try:
    main()
except SystemExit as e:
    if e.args[0]:
         clean_exit(e.args[0])
    raise
else:
    atexit.register(clean_exit, 0)
    
