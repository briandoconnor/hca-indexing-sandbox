# hca-indexing-sandbox

A place to explore indexing

## Upload Data

    docker run --rm -e ACCESS_TOKEN=`cat token.txt` -e REDWOOD_ENDPOINT=ops-dev.ucsc-cgl.org -v $(pwd)/outputs:/outputs  -v `pwd`:/dcc/data quay.io/ucsc_cgl/core-client:1.1.0-alpha spinnaker-upload --force-upload --skip-submit  /dcc/data/manifest.tsv  > >(tee stdout.upload.txt) 2> >(tee stderr.upload.txt >&2)
