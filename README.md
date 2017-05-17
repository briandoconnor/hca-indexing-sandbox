# hca-indexing-sandbox

A place to explore indexing for the HCA Blue Box using some Computational Genomics Platform (CGP) infrastructure from UCSC.

## Dependencies

I started with a `dcc-ops` deployed CGP instance running on AWS.  See the [dcc-ops](https://github.com/BD2KGenomics/dcc-ops/tree/release/1.0.0-alpha.2) GitHub site.

## Upload Data

An example where I uploaded a data bundle that contained an `assay.json` and a `provenance.json` in addition to the
`*.fastq.gz` file pair.  See the example `manifest.tsv`, you may need to customize for your own fastq files.  My token comes from the portal setup by the `dcc-ops` system.  You'll effectively need that whole stack installed on an AWS VM to get this to work.

    docker run --rm -e ACCESS_TOKEN=`cat token.txt` -e REDWOOD_ENDPOINT=ops-dev.ucsc-cgl.org -v $(pwd)/outputs:/outputs  -v `pwd`:/dcc/data quay.io/ucsc_cgl/core-client:1.1.0-alpha spinnaker-upload --force-upload --skip-submit  /dcc/data/manifest.tsv  > >(tee stdout.upload.txt) 2> >(tee stderr.upload.txt >&2)

## Trigger Indexing

This causes the indexer to re-run on the AWS VM hosting the `dcc-ops` stack. It means the results of the above upload show in the Boardwalk portal.

    sudo docker exec -it boardwalk_dcc-metadata-indexer_1 bash -c "/app/dcc-metadata-indexer/cron.sh"

## Prepare Index

This will query public endpoints to find `assay.json` and a `provenance.json` files, downloads them, and loads them into an elasticsearch index file ready for loading.

    virtualenv env
    source env/bin/activate
    pip install semver
    python query_and_load.py --redwood-token `cat token.txt` --redwood-domain ops-dev.ucsc-cgl.org --working-dir outputs

## Load Index

    curl -XPUT 'localhost:9200/bluebox?pretty' -H 'Content-Type: application/json' -d'
    {
      "mappings": {
        "my_type": {
          "properties": {
            "assay_json.characteristic.value": {
              "type": "text"
            }
          }
        }
      }
    }
    '
    curl -XGET 'localhost:9200/_cat/indices?v&pretty'
    curl -H "Content-Type: application/json" -XPOST 'localhost:9200/bluebox/assay/_bulk?pretty&refresh' --data-binary "@elasticsearch_index.jsonl"

To delete the index:

    curl -XDELETE 'localhost:9200/bluebox?pretty&pretty'


## Query the Index

The above script creates and index and the commands load it into elasticsearch.  How about a simple query?

Simple query, see the [docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-uri-request.html):

    curl -XGET 'localhost:9200/bluebox/_search?q=value:Homo+sapiens'

For more complex queries see the [Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html):

    curl -XGET 'localhost:9200/bluebox/_search?pretty' -H 'Content-Type: application/json' -d'
    {
    "query": { "match": { "assay_json.characteristic.value": "Homo Sapiens" } }
    }
    '

Boolean combination, I don't think this is getting the dependency right between the two fields:

    curl -XGET 'localhost:9200/bluebox/_search?pretty' -H 'Content-Type: application/json' -d'
    {
    	"query": {
    		"bool": {
    			"must": [{
    				"match": {
    					"assay_json.characteristic.value": "Homo Sapiens"
    				}
    			}, {
    				"match": {
    					"assay_json.characteristic.category": "organism"
    				}
    			}]
    		}
    	}
    }
    '
