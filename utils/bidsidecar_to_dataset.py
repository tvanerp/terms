
import os,sys
from os.path import isdir,isfile
from os import system
from argparse import ArgumentParser
import glob2
import logging
import subprocess
import pandas as pd
from rdflib import Graph,util,Namespace, Literal,RDFS,RDF, URIRef
from pyld import jsonld
from os.path import join
import json
from urllib.parse import urlparse
import tempfile
import urllib.request as ur
from urllib.parse import urldefrag

import datalad.api as dl
from shutil import copyfile


def main(argv):
    parser = ArgumentParser(description='This program will copy augmented BIDS sidecar files back'
                                        'to the original BIDS data and run bidsmri2nidm on it')

    parser.add_argument('-datalad_dir', dest='datalad_dir', required=True, help="Path to directory containing "
                            "datalad datasets to copy BIDS sidecar files to (e.g. /datasets.datalad.org/openfmri)")
    parser.add_argument('-new_sidecar_dir', dest='sidecar_dir', required=True, help="Path to directory containing "
                            "sub-directories for each BIDS dataset with augmented BIDS sidecar files")
    parser.add_argument('-nidm_dir', dest='nidm_dir', required=False, help="If path is included then "
                            "NIDM files will be put in this location under dataset name otherwise they will be"
                            "added to the datalad dataset directly.")
    parser.add_argument('-logfile', dest='logfile', required=True, help="Logfile to track progress and errors")

    args = parser.parse_args()

    # open log file
    logger = logging.getLogger('bidsidecar_to_datset')
    hdlr = logging.FileHandler(args.logfile)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

    # step 1 check directories exist
    if not isdir(args.datalad_dir):
        logger.error("Datalad directory not found: %s" %args.datalad_dir)
        exit(1)
    if not isdir(args.sidecar_dir):
        logger.error("BIDS augmented sidecar directory not found: %s" % args.sidecar_dir)
        exit(1)

    # set working directory to args.datalad_dir
    #os.chdir(args.datalad_dir)

    # step 2 loop through all datasets in args.sidecar_dir
    bids_datasets = [ x for x in os.listdir(args.sidecar_dir) if isdir(join(args.sidecar_dir,x)) ]
    # for each dataset
    for ds in bids_datasets:
        # search recursively in ds looking for json files.  Path should be same as found within the dataset in
        # datalad so it'll be a simple copy.
        json_files = glob2.glob(join(args.sidecar_dir,ds,'**',"*.json"))

        # check of we have json files before we download dataset from datalad
        if len(json_files) == 0:
            continue

        # download datalad dataset and install
        #cmd = ["datalad","get", "-r", join(args.datalad_dir,ds)]
        # replacing with datalad api
        #cmd = ["datalad", "get", "-r", ds]
        try:
        	dl.get(path=join(args.datalad_dir,ds),recursive=True)
        	logger.info("Running datalad get command on dataset: %s" %join(args.datalad_dir,ds))
        	#ret = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        except:
                logger.error("Datalad returned error: %s for dataset %s." %(sys.exc_info()[0], ds))
                continue

        # now copy each of the json_files into the datalad dataset
        for file in json_files:
            # changing copy to use copyfile from shutil
            #cmd = ["cp",join(args.sidecar_dir,ds,file),join(args.datalad_dir,ds)]
            if not isdir(join(args.datalad_dir,ds)):
                 os.mkdir(join(args.datalad_dir,ds))
            logger.info("Copying file: source=%s, dest=%s" %(join(args.sidecar_dir,ds,file),join(args.datalad_dir,ds)))
            copyfile(join(args.sidecar_dir,ds,file),join(args.datalad_dir,ds,file))
            #ret = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)

        # make sure it's there
        if not isfile(join(args.datalad_dir,ds,file)):
            logger.error("ERROR: copy of file %s to %s didn't complete successfully!" %(join(args.sidecar_dir,ds,file),join(args.datalad_dir,ds)))

        # now run bidsmri2nidm
        if args.nidm_dir is not None:
            cmd = ["bidsmri2nidm","-d",join(args.datalad_dir,ds),"-o",join(args.nidm_dir,ds,"nidm.ttl"),"-bidsignore","-no_concepts"]
        else:
            cmd = ["bidsmri2nidm", "-d", join(args.datalad_dir, ds), "-o", join(args.datalad_dir, ds, "nidm.ttl"),
                   "-bidsignore","-no_concepts"]
        logger.info("Running command: %s" % cmd)
        ret = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)

        # now remove the datalad dataset to save space
        # replacing with datalad api call
        #cmd = ["datalad", "uninstall", "-r", join(args.datalad_dir, ds)]
        dl.uninstall(path=join(args.datalad_dir,ds),recursive=True)
        logger.info("Running datalad uninstall command on dataset: %s" %join(args.datalad_dir,ds))
        #ret = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)












if __name__ == "__main__":
   main(sys.argv[1:])
