# This repository is the central hub for the high-density training data used to build the Sprite (22m), Nymph (50m), dragonfly (65m), and Wyrm (135m) model families. The focus here is on quality over raw volume, ensuring that small-parameter models have enough structural diversity and factual grounding to perform with high fidelity in local, private environments.

# &#x20;

# The training pipeline is under development and constantly changing.

It is posted at https://github.com/danc403/training and can be used with these datasets to train your own model from scratch.

No weights from other models needed.

All models can be trained on a modest 4060 8Gb card in under 6 hours.

That is the whole family in that 6 hours.



# Directory Structure

# Directory

# Content Overview

# Training Utility

# /articles

# \~16k rows of high-quality prose.

# Acts as a buffer/filler to balance segment lengths and inject linguistic variety (e.g., neuroscience/biology).

# /factbook

# CIA World Factbook (2026 current) + Python parsers.

# Provides rigorous geopolitical and statistical grounding for objective world knowledge.

# /pokemon

# 1025-row stats and \~14k-row instruction set.

# High-density taxonomic and logical instruction-following data.

# /scripts

# Text cleaning and normalization tools.

# Ensures all data is terminal-safe, ANSI-compliant, and optimized for local inference.

# /space

# \~100 row solar system facts (solar.jsonl).

# Specific domain grounding for astronomical data and instructional prompts.

# /text

# \~30k poems and titles.md manifest.

# The "Wyrm" core—developing rhythmic sensitivity and linguistic nuance.

# /wikifacts

# \~300k rows of simple, plain-text facts.

# The foundational logic layer (e.g., "April is the 4th month") for consistent reasoning.

# Export to Sheets

# Copy table

# &#x20;

# Core Components

# 1\. The Knowledge Base (/wikifacts \& /factbook)

# With over 300,000 simple facts and the 2026 CIA Factbook, this layer ensures the model doesn't hallucinate foundational reality. The included Python scripts allow for multi-year parsing to maintain temporal accuracy.

# 2\. The Artistic Core (/text)

# The Wyrm Archive poetry collection (\~30k rows) is designed to sharpen the model’s grasp of cadence and emotion. To maintain copyright compliance, novels and textbooks are excluded from the public push but are indexed in titles.md for transparency.

# 3\. Structural Filling (/articles)

# The 16,000 diverse articles (including science and biology features) are used to fill "token gaps." If a training block is short on data, these articles provide high-quality "noise" to prevent the model from overfitting on specific formats.

# 4\. Specialized Logic (/pokemon \& /space)

# Instruction sets like the Pokémon data (\~14k rows) test the model's ability to handle complex, interconnected stats and specific user queries within a closed system.

# &#x20;

# Technical Standards

# Terminal Safety: All datasets in this repository are processed to be ANSI/ASCII compliant. We strip "smart" characters (curly quotes, em-dashes) and Unicode artifacts that interfere with screen readers or legacy terminal outputs.

# Cleaning Pipeline

# Current tools in the /scripts directory include:

# • 

# Unicode Normalization: Standardizing character sets for clean training loss.

# • 

# Pronoun Replacement: Refined text processing for consistent instruction-tuning.

# &#x20;

# This structure puts us at roughly 110 million base tokens, creating a dense, versatile environment for the next generation of iDragonfly models.



