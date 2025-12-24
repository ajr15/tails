#!/usr/bin/env bash
set -e

ES="http://localhost:9200"
INDEX="debug_path"

echo "Deleting index (if exists)"
curl -s -X DELETE "$ES/$INDEX" >/dev/null || true

echo "Creating index"
curl -s -X PUT "$ES/$INDEX" -H "Content-Type: application/json" -d '{
  "settings": {
    "analysis": {
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        }
      },
      "analyzer": {
        "custom_english": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "english_stop",
            "english_stemmer"
          ]
        },
        "path_analyzer": {
          "tokenizer": "pattern",
          "filter": ["lowercase"]
        }
      }
     
    }
  },
  "mappings": {
    "properties": {
     "path": {
        "properties": {
          "real": {
            "type": "text",
            "analyzer": "path_analyzer"
          },
          "filename": {
            "type": "text"
           
          }
        }
      },
      "content": {
        "type": "text",
        "analyzer": "custom_english"
      }
    }
  }
}'

echo
echo "Indexing document"
curl -s -X POST "$ES/$INDEX/_doc/1" -H "Content-Type: application/json" -d '{
   "path": {
    "real": "/home/barako/docs/my.file.v1.pdf",
    "filename": "my.file.v1.pdf"
  },
  "content": "Running runners ran easily. The documents are stored here."
}'

echo
echo "Refreshing index"
curl -s -X POST "$ES/$INDEX/_refresh" >/dev/null

echo
echo "Searching path field for docs"
curl -s -X GET "$ES/$INDEX/_search?pretty" -H "Content-Type: application/json" -d '{
  "query": {
    "match": {
      "path.real": "barako"
    }
  },
  "highlight": {
    "fields": {
      "path.real": {}
    }
  }
}'
