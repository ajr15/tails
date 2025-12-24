from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan

ES_HOST = "http://localhost:9200"

es = Elasticsearch(ES_HOST)

PHd_CHUNKS_INDEX = "phd_chunks"
PHd_INDEX = "phd"

missing_doc_ids = set()
existing_doc_ids = set()
# 1. Iterate over all chunks
for doc in scan(
    client=es,
    index=PHd_CHUNKS_INDEX,
    query={
        "_source": ["doc_id"],
        "query": {"exists": {"field": "doc_id"}}
    },
    size=1000):
    doc_id = doc["_source"]["doc_id"]

    # 2. Check existence in phd index
    exists = es.exists(index=PHd_INDEX, id=doc_id)

    if not exists:
        #print(f"Missing doc_id: {doc_id}")
        if doc_id not in missing_doc_ids:
            missing_doc_ids.add(doc_id)
    else:
        #print(f"Found doc_id: {doc_id}")
        if doc_id not in existing_doc_ids:
            existing_doc_ids.add(doc_id)

# 3. Result
print(f"Missing doc_ids count: {len(missing_doc_ids)}")
print(f"existing doc_ids count: {len(existing_doc_ids)}")
for d in sorted(missing_doc_ids):
    #print(d)
    pass
