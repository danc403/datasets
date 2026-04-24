\# Text Directory Overview



\## Data Structure and Components



\### 1. The Core Repository (text.jsonl)

This is the master ingestion file containing the full breadth of the current corpus. 

\- \*\*Note:\*\* This file is strictly excluded via `.gitignore` to ensure compliance with copyright standards and to maintain the privacy of the primary source material.

\- \*\*Scope:\*\* Includes thousands of proprietary and public domain books, technical articles, and specialized datasets.



\### 2. Poetic Corpus (poems.jsonl)

A filtered extraction dedicated to verse and narrative poetry.

\- \*\*Volume:\*\* 30,000+ entries.

\- \*\*Size:\*\* Approximately 86MB.



\### 3. favorites.jsonl

A curated subset of high-impact works specifically selected for oversampling and supervised fine-tuning (SFT). These entries are designed to be "recited" by the models with high fidelity.

\- \*\*Core Works:\*\* Includes \*Invictus\*, \*If\*, \*Desiderata\*, and \*Annie and Willie's Prayer\*.



\### 4. Manifest (titles.md)

To facilitate reproducibility without violating copyright, `titles.md` provides a comprehensive metadata list of the books and articles contained within the hidden `text.jsonl`.

\- \*\*Purpose:\*\* Allows researchers and developers to estimate token density, vocabulary breadth, and word counts for independent model evaluation.



\## Reproduction and Scaling



The data in this directory contributes to a base training set of approximately 110 million tokens. To reproduce the specific character of the Nymph and Sprite models, the following ingestion ratio is utilized:



\- \*\*Logic Layer:\*\* 300,000 rows of simple factual assertions.

\- \*\*Grounding Layer:\*\* 10,000 pairs from the World Factbook.

\- \*\*Taxonomy Layer:\*\* 10,000 Pokémon data pairs.

\- \*\*Nuance Layer:\*\* 35,000 rows of poetry.



