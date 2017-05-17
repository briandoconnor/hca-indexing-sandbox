#!/usr/bin/env python

"""
    author Brian O'Connor
    broconno@ucsc.edu

    This module first queries a given Redwood instance for metadata document,
    downloads them, minimally transforms them, and, finally, loads them into
    Elasticsearch ready for querying.

"""

import semver
import logging
import os
import os.path
import platform
import argparse
import json
import jsonschema
import datetime
import re
import dateutil
import ssl
import dateutil.parser
import ast
#from urllib import urlopen
from urllib2 import urlopen, Request
from subprocess import Popen, PIPE


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
        os.environ["REDWOOD_ENDPOINT"] = self.redwood_domain

        print ("** FINDING FILES **")
        last= False
        page=0
        obj_arr=[]
        # figure out the pages
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        #json_str = urlopen(str("https://"+self.redwood_domain+":8444/entities?fileName=assay.json&page=0"), context=ctx).read()
        json_str = urlopen(str("https://"+self.redwood_domain+"/api/v1/repository/files?include=facets&from=1&size=200&filters=%7B%22file%22:%7B%22fileFormat%22:%7B%22is%22:%5B%22json%22%5D%7D%7D%7D"), context=ctx).read()
        metadata_struct = json.loads(json_str)

        for hit in metadata_struct['hits']:
            #print (hit)
            if hit['fileCopies'][0]['fileName'] == "assay.json" or hit['fileCopies'][0]['fileName'] == "provenance.json":
                object_id = hit['objectID']
                print("INFO: "+hit['fileCopies'][0]['repoDataBundleId']+" "+hit['objectID'])
                print("** DOWNLOAD **")
                # docker run -it --rm -e ACCESS_TOKEN=`cat token.txt` -e REDWOOD_ENDPOINT=ops-dev.ucsc-cgl.org -v $(pwd)/samples:/samples -v $(pwd)/outputs:/outputs -v $(pwd):/dcc/data quay.io/ucsc_cgl/core-client:1.1.0-alpha /bin/
                # icgc-storage-client download --output-dir /outputs --object-id bd9a15ad-758b-5c8e-8e63-340e511789cf --output-layout bundle --force
                command = ["docker", "run", "--rm", "-e", "ACCESS_TOKEN="+self.redwood_token, "-e", "REDWOOD_ENDPOINT="+self.redwood_domain, "-v", "$(pwd)/samples:/samples", "-v", "$(pwd)/outputs:/outputs", "-v", "$(pwd):/dcc/data", "quay.io/ucsc_cgl/core-client:1.1.0-alpha"]
                command.append("icgc-storage-client")
                command.append("download")
                command.append("--output-dir")
                command.append("/outputs")
                command.append("--object-id")
                command.append(str(object_id))
                command.append("--output-layout")
                command.append("bundle")
                command.append("--force")
                print " ".join(command)
                try:
                    c_data=Popen(["/bin/bash", "-c", " ".join(command)], stdout=PIPE, stderr=PIPE)
                    stdout, stderr = c_data.communicate()
                    print (stdout)
                    print (stderr)
                except Exception as e:
                    print 'Error while downloading file with content ID: %s Error: %s' % (object_id, e)

        print ("** BUILDING INDEX **")
        outfile = open("elasticsearch_index.jsonl", "w")
        index_index = 1
        # walk directory structure, parse JSONs, put in single json, write ES index file
        for root, dirs, files in os.walk("outputs"):
            for currdir in dirs:
                assay_file = open("outputs/"+currdir+"/assay.json", "r")
                assay_str = json.dumps(json.loads(assay_file.read()))
                assay_file.close()
                provenance_file = open("outputs/"+currdir+"/provenance.json", "r")
                provenance_str = json.dumps(json.loads(provenance_file.read()))
                provenance_file.close()
                outfile.write('{"index":{"_id":"' + str(index_index) + '","_type":"meta"}}\n')
                outfile.write('{"assay_json": '+assay_str+', "provenance_json": '+provenance_str+'}')
                index_index += 1
        outfile.close()


# run the class
if __name__ == '__main__':
    runner = QueryAndLoad()
