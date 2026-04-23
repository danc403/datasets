Wikipedia Fact Corpus (Simple English)

Source: This dataset is a heavily cleaned and processed version of the Simple Wikipedia dataset by rahular on Hugging Face.

Processing \& Cleaning:

The raw source contains approximately 770k rows of varying quality and formatting. This version has been reduced to 300k high-quality fact rows using a custom cleaning pipeline (wiki.py).

Cleaning steps included:

Removing redundant metadata and non-instructive fragments.

Normalizing character encoding and whitespace.

Filtering for entries that provide clear, standalone factual value for small-scale LLM training

Converting the source format into a single-line JSONL structure



