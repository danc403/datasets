Dataset Documentation: World Factbook

This repository contains a modularized, chronologically organized version of the CIA World Factbook, specifically optimized for training Large Language Models on Associative Recall, Spatial Awareness, and Temporal Reasoning.

Status: Work in Progress. The 2026 dataset is the current "Golden Standard" for the schema; previous years are being back-ported to this optimized format.

1\. Directory Structure

The datasets are organized by year to allow for temporal comparisons and specific epoch training:

• 

/datasets/factbook/: Root directory.

• 

/\[YEAR]/: Contains the processed JSONL for specific years (1990 to present).

factbook.py: The primary transformation engine for sovereign entity data.

global.py: The specialized engine for non-sovereign, oceanic, and world-scale data.

2\. Core Transformation Engines

factbook.py (Sovereign Entities)

Converts raw World Factbook JSON into the Deterministic Masking Schema.

Structural Shuffling: Narrative and fact-sheet blocks are shuffled to prevent the model from relying on positional memorization.

Context-Instruction Pairs: Generates high-density training rows that force the model to attend to the provided context.

global.py (World \& Oceans)

Handles non-standard schemas for oceanic and global-scale data.

World Facts: Aggregated global data (population, trade, etc.).

Oceanic Data: Geographical and environmental data for the Atlantic, Pacific, etc.

Alignment: Ensures global entries use the same deterministic masking anchors as country files for architectural consistency.

3\. Training Methodology

This dataset supports a two-phase training protocol:

1\. 

Phase 1: Base Knowledge (Random Masking)

Uses the text rows with standard random masking to build foundational statistical "weights" within the model.

2\. 

Phase 2: Deterministic Alignment (Instruct Tuning)

Uses the prompt/response rows with Deterministic Masking. By targeting the data between specific anchors, the model learns the protocol for Accurate Data Retrieval.

Note: Masking anchors (mask\_pre, mask\_target, mask\_post) are consistent across all years, ensuring a stable retrieval logic across the entire temporal span of the dataset.

4\. Data Provenance \& Attribution

The raw data for this collection is sourced from the factbook.json repository maintained by Gerald Bauer.

Source Schema: Original JSON structure provided by factbook.json.

License: CC0 1.0 Universal (Public Domain).

Modifications: All conversion logic, sharding, and the creation of the Deterministic Masking instruction sets (Phase 1/Phase 2) were developed by the iDragonfly project to support local SLM training.

&#x20;

5\. Usage

To generate the final training sets from the raw source files, run the scripts from within the root directory:

Bash

Download codeCopy code

python3 factbook.py

python3 global.py

&#x20;

Special Feature: Spatial Reasoning Engine

Unlike standard fact dumps, this dataset includes a Spatial Logic layer. The processing scripts perform coordinate-based calculations to generate:

Proximity Checks: "Is \[Country A] within 500km of \[Country B]?"

Cardinal Directions: "In which direction would you travel to get from \[City A] to \[City B]?"

Geometric Adjacency: Fact-checked neighbor validation based on border coordinates.

This is specifically designed to test the model's ability to ground factual knowledge in mathematical reality.



