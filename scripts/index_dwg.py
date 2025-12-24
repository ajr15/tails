# script to go over Elastic index and Index all DWG files using command line
import argparse
import requests
import utils
import os
import subprocess
import json


def get_dwgs(es_client, index_name, reindex: bool):
    query = {
        "query": {
            "term": {
                "file.extension": "dwg"
            }
        }
    }
    response = es_client.search(index=index_name, body=query, size=10000)
    # return all hits, make sure they DO NOT have content already
    hits = response['hits']['hits']
    print(f"Found {len(hits)} DWG files in index {index_name}")
    for hit in hits:
        if "dwg_indexed" in hit['_source'] and not reindex:
            continue
        ajr = hit['_source']
        ajr["id"] = hit["_id"]
        yield ajr


def index_dwg_obselete(path: str):
    """Index a single DWG file using .NET exe"""
    config = utils.get_config("dwg_indexer")
    # Ensure the path is correct and you have execution permissions
    exe_path = config["path"]
    if not os.access(exe_path, os.X_OK):
        raise PermissionError(f"Cannot execute: {exe_path}. Check file permissions.")
    process = subprocess.run([exe_path, path, config["fonts_csv"], config["fonts_dir"]], capture_output=True, text=True)
    output = process.stdout.strip()
    try:
        result = json.loads(output)
    except json.JSONDecodeError:
        result = {"error": "Failed to parse output", "raw": output}
    return result
def index_dwg(path: str):
    """Index a single DWG file using DwgExtract docker api"""
    url = "http://localhost:4100/process"
    with open(path, "rb") as f:
        response = requests.post(url, files={"file": f})

    response.raise_for_status()

    data = response.json()          # the API’s JSON
    stdout_text = data["stdout"]    # this is a long text
    stdout_json = json.loads(stdout_text)  # parse it as JSON

    return stdout_json

def update_dwg(es_client, file_id: str, index_name: str, content: dict):
    """Update a DWG (with file id) with content dictionary"""
    update_body = {
        "doc": {
            "dwg_content": content,
            "dwg_indexed": True
        }
    }
    print(f"updating {index_name}/{file_id} with {len(str(content))} content characters")
    es_client.update(index=index_name, id=file_id, body=update_body)


def main(es_client, index_name, reindex: bool):
    dwgs = list(get_dwgs(es_client, index_name, reindex))
    ndwgs = len(dwgs)
    print(f"*** START INDEXING {ndwgs} DWG FILES FOR INDEX {index_name}***")
    for dwg in dwgs:
        file_path = dwg.get("path", {}).get("real")
        file_id = dwg.get("id")
        if file_path and file_id:
            content = index_dwg(file_path)
            update_dwg(es_client, file_id, index_name, content)
    print(f"*** DONE INDEXING {ndwgs} DWG FILES FOR INDEX {index_name}***")

if __name__ == "__main__":
    description="Index DWG files from Elastic index."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("index_name", help="Name of the Elastic index to get DWG files from")
    parser.add_argument("--reindex", help="Reindex DWG files even if they have been indexed before", action="store_true")
    args = parser.parse_args()
    main(utils.get_esclient(), args.index_name,args.reindex)
    
