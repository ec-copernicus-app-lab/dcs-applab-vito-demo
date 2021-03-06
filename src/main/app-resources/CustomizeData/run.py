#!/opt/anaconda/bin/python

import sys
import os
import atexit
import commands

sys.path.append(os.environ['_CIOP_APPLICATION_PATH'] + '/util')

# import the ciop functions (e.g. copy, log)

import cioppy
ciop = cioppy.Cioppy()

# define the exit codes
SUCCESS = 0
ERR_INVALIDTYPE = 1
ERR_INVALIDROI = 2
ERR_CUSTOMIZATION = 3

# add a trap to exit gracefully
def clean_exit(exit_code):
    log_level = 'INFO'

    if exit_code != SUCCESS:
        log_level = 'ERROR'

    msg = { SUCCESS           : 'Product customization concluded successfully',
            ERR_INVALIDTYPE   : 'Invalid product type specified (expected: BA, LAI or NDVI)',
            ERR_INVALIDROI    : 'Invalid region of interest specified (expected: tlx,tly,brx,bry)',
            ERR_CUSTOMIZATION : 'Failed to customize product'}

    ciop.log(log_level, msg[exit_code])

def main(inputs):

    # retrieve some customization parameters
    roi  = ciop.getparam('roi')
    type = ciop.getparam('type')

    if type != "BA" and type != "NDVI" and type != "LAI": 
        sys.exit(ERR_INVALIDTYPE);

    bbox = roi.split(",");

    if len(bbox) != 4:
        sys.exit(ERR_INVALIDROI);

    tlx = bbox[0]
    tly = bbox[1]
    brx = bbox[2]
    bry = bbox[3]

    # create the output folder to store the output products and export it
    outputDir = os.path.join(ciop.tmp_dir, 'output')
    inputDir = os.path.join(ciop.tmp_dir, 'input')
    os.makedirs(outputDir);
    os.makedirs(inputDir);

    ciop.log('INFO', 'Found %d inputs published' % len(inputs))

    # Input files come from STDIN (standard input) and they are retrieved
    # line-by-line.
    for input in inputs:
        
        ciop.log('INFO', 'Input = %s' % input)

        # retrieve the file to the local temporary folder TMPDIR provided by the framework (this folder is only used by this process).
        retrieved = ciop.copy(input, inputDir)
        ciop.log('INFO', 'Retrieved ' + os.path.basename(retrieved))

        # perform customization
        outputBasename   = os.path.splitext(os.path.basename(retrieved))[0] + "_CUSTOM.TIFF"
        outputPath       = os.path.join(outputDir, outputBasename);
        outputPathDocker = os.path.join("/home/worker/workDir/outDir", outputBasename);
        inputDirDocker   = "/home/worker/workDir/inDir"
        inputPathDocker  = os.path.join(inputDirDocker, os.path.basename(retrieved))

        # "applab/applab-data-customization:latest " \
        cmd = "docker run " \
              "-v " + os.path.dirname(outputPath) + ":" + os.path.dirname(outputPathDocker) + " " \
              "-v " + os.path.dirname(retrieved) + ":" + inputDirDocker + " " \
              "-v /data:/data " \
              "vito-docker-private.artifactory.vgt.vito.be/applab-data-customization:latest " \
              "python /home/worker/applab/customize.py -tlx %s -tly %s -brx %s -bry %s -type %s -in %s -out %s" % (tlx, tly, brx, bry, type, inputPathDocker, outputPathDocker) 

        ciop.log('INFO', 'Executing command %s ' % cmd);

        stat, out = commands.getstatusoutput(cmd);

        if stat != 0:
            ciop.log('ERROR', 'Failed to customize product: %s' % out);
            sys.exit(ERR_CUSTOMIZATION)

        # publish results
        ciop.publish(outputPath, metalink=True);

        ciop.log('INFO', 'Results published to %s ' % outputPath)

        # cleanup results
        os.remove(retrieved);

try:

    inputs = []
    for input in sys.stdin:
        inputs.append(input)

    main(inputs)

except SystemExit as e:
    if e.args[0]:
         clean_exit(e.args[0])
    raise
else:
    atexit.register(clean_exit, 0)
    
