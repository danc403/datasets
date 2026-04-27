iDragonfly Music Dataset Pipeline

This directory contains the core intelligence pipeline for processing musical discography and lyrics into high-quality instruction sets for the Nymph and Wyrm model families. It is designed to transform raw library data into a "Digital Liner Note" experience.

Directory Structure and Workflow

1\. 

music.jsonl (The Starting Point)

All music library metadata is stored here. It contains the Performer, Song Title, and Directory Hierarchy. Use this as a pattern if you wish to add custom entries to the set.

2\. 

music\_lyrics.py (The Scraper)

This script reads music.jsonl and scrapes the full lyrics for each entry. It outputs the results into a temporary music\_lyrics.jsonl file.

3\. 

music\_instruct.py (The Dataset Architect)

This processes the scraped lyrics into a structured instruction set. It converts metadata into stringified JSON objects within the context field to train the model to act as a tool-aware bridge between structured data and natural language. It also uses Blind-Hook Logic to automatically extract memorable song snippets while redacting the title.

4\. 

music\_instruct.jsonl (The Final Set)

The high-density output containing over 4,000 training rows. This is the only file intended for the training pipeline.

Integration with Shard Pipeline

The iDragonfly sharding and tokenization pipeline is configured to target only music\_instruct.jsonl. All other jsonl files in this directory, including raw metadata or intermediate scrapes, are ignored to ensure the training data remains high-fidelity and strictly follows the instruction-tuning format.

Example Data Format

Each row in the final set follows this rounded JSON schema:

{

"title": "Song Title",

"author": "Performer",

"context": "{"performer": "Artist", "count": 2, "tracks": \["Track A", "Track B"]}",

"prompt": "Natural language query?",

"response": "Conversational, accurate response."

}



