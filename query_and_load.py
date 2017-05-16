#!/usr/bin/env python

"""
    author Brian O'Connor
    broconno@ucsc.edu

    This module first queries a given Redwood instance for metadata document,
    downloads them, minimally transforms them, and, finally, loads them into
    Elasticsearch ready for querying.

"""

import json
import time
import re
from datetime import datetime
import subprocess
import argparse
import base64
import os
from urllib import urlopen
from uuid import uuid4

import logging
import hashlib
import errno
from functools import partial

import os
import sys


class QueryAndLoad:

    def __init__(self):
        parser = argparse.ArgumentParser(description='Queries Redwood, downloads metadata, and prepares Elasticsearch index.')
        parser.add_argument('--redwood-domain', default='ops-dev.ucsc-cgl.org', required=True)
        parser.add_argument('--redwood-token', default='token_path', required=True)
        parser.add_argument('--working-dir', default='working-dir', required=True)

        # get args
        args = parser.parse_args()
        self.redwood_domain = args.redwood_domain
        self.redwood_token = args.redwood_token
        self.working_dir = args.working_dir

        # run
        self.run()

    def run(self):
        #Assigning the environmental variables for REDWOOD ENDPOINT (here refered as redwood host),
        #and for the ACCESS_TOKEN (here referred to as redwood token)
        os.environ["ACCESS_TOKEN"] = self.redwood_token
        os.environ["REDWOOD_ENDPOINT"] = self.redwood_host

        print ("** FINDING FILES **")
        last= False
        page=0
        obj_arr=[]
        # figure out the pages
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        json_str = urlopen(str("https://"+self.redwood_domain+":8444/entities?fileName=assay.json&page=0"), context=ctx).read()
        metadata_struct = json.loads(json_str)
        for page in range(0, metadata_struct["totalPages"]):
            print "DOWNLOADING PAGE "+str(page)
            meta_cmd= ["curl", "-k"]
            url= 'https://'+args.server_host+':8444/entities?fileName=assay.json&page='
            new_url=  url + str(page)
            meta_cmd.append(new_url)
            c_data=Popen(meta_cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = c_data.communicate()
            json_obj= json.loads(stdout)
            last = json_obj["last"]
            obj_arr.append(json_obj)

        print("** DOWNLOAD **")
        d_utc_datetime = datetime.utcnow()
        d_start = time.time()
        # this will download and create a new JSON
        transformed_json_path = self.download_and_transform_json(self.json_encoded)
        d_end = time.time()
        d_utc_datetime_end = datetime.utcnow()
        d_diff = int(d_end - d_start)
        print("START: "+str(d_start)+" END: "+str(d_end)+" DIFF: "+str(d_diff))

# run the class
if __name__ == '__main__':
    runner = DockstoreRunner()
