# Pipeline

Steps to get data in the RAG

## parse original docs from txt

With scripts in parsing
- reconcile_regulation
- reconcile_recital
- reconcile_annex

this creates json files in ./data/rag
recital|regulation|annex_{date}.json

## combine data for rag
build_rag4embedding aggregates the section data files in rag into a
ragtime_{date}.json file that has all the columns and rows for embedding and ingestion in the vector db

## (Re) Create collection
if needed, create a new collection with
./scrpt/embedding/create_collection

>> %run script/embedding/create_collection.py  --collection_name  "AIAct_240219" --location "cloud"

## embed data

>> %run script/embedding/embed.py  --collection_name  "AIAct_240219" --dataset "ragtime_20240219.json" --location "cloud"
