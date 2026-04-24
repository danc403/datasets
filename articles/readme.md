\# Supplemental Article Corpus: Segment Balancing \& Noise Injection



Article Supplement Corpus



\## Overview

This directory contains `articles\\\_0.jsonl`, `articles\\\_1.jsonl`, `articles\\\_2.jsonl`, a collection of sixteen thousand articles used as a supplemental data source for training models. This dataset serves as "linguistic noise" and a structural filler to ensure the model maintains a broad understanding of natural language beyond specialized fact-pairs and poetry.



\## Purpose and Usage

The primary function of this dataset is \*\*Length-Aware Data Augmentation\*\*. It is used to fill specific gaps in the token-count distribution of the training corpus.



\- \*\*Gap Filling:\*\* Provides full-text examples for segment lengths that are underrepresented in the primary poetry or fact datasets.

\- \*\*Noise Injection:\*\* Introduces diverse prose structures to prevent the model from overfitting to the specific cadences of 18th-century verse or the rigid format of the World Factbook.

\- \*\*Dynamic Filtering:\*\* In current training runs, a length-based filter is applied to select an arbitrary subset—typically around two hundred and fifty rows—to mix into the active training set.



\## Dataset Statistics

\- \*\*Total Rows:\*\* 16,000

\- \*\*Format:\*\* JSONL (ANSI/Terminal-Safe)



\## Attribution

\*Status: Pending Final Verification.\*

This dataset is a curated subset of a much larger corpus. Potential sources include:

\- \*\*WikiText-103:\*\* A collection of verified "Good" and "Featured" articles from Wikipedia.

\- \*\*The Pile (Wikipedia/OpenWebText):\*\* High-density prose extracts used for foundational LLM training.



\## Character Standards

All text has been sanitized for terminal safety. Smart quotes, em-dashes, and non-standard UTF-8 symbols have been converted to their standard ASCII/ANSI equivalents to maintain consistency across legacy inference engines.



