# This repository is the central hub for the high-density training data used to build the Sprite (384), Nymph (512), and Wyrm (768) model families. The focus here is on quality over raw volume, ensuring that small-parameter models have enough structural diversity and factual grounding to perform with high fidelity in local, private environments.

# 

# The training pipeline is under development and constantly changing. 

# It is posted at https://github.com/danc403/training and can be used with these datasets to train your own model from scratch. 

# No weights from other models needed. 

# All models can be trained on a modest 4060 8Gb card in under 6 hours. 

# That is the whole family in that 6 hours.

# 

# \## New: Starter Dataset (OSS Edition)

# We have included `text/oss.jsonl`, a collection of public domain books and articles derived from the `titles.md` manifest. This provides over 2 million words of high-signal "Anchor" data to get your training started immediately with proven, high-quality linguistic structures.

# 

# \## Custom Data Ingestion

# You can easily expand the training corpus with your own library. We provide a streamlined tool in `/scripts/txt2jsonl.py` to prepare your personal data for the pipeline.

# 

# \*\*To include your own books or articles:\*\*

# 1\. Navigate to the `datasets/user\_data/` directory.

# 2\. Drop your raw `.txt` or `.md` files into this folder.

# 3\. \*\*Format Requirement:\*\* The first line of the file must be the \*\*Title\*\*, and the second line must be the \*\*Author\*\*. 

# 4\. Run the conversion script: `python3 ./scripts/txt2jsonl.py`.

# 

# The training pipeline and sharding scripts will automatically detect the resulting `books.jsonl` in that directory and include it in both tokenizer training and dataset sharding.

# 

# \## Directory Structure

# 

# | Directory | Content Overview | Training Utility |

# | :--- | :--- | :--- |

# | \*\*/articles\*\* | \~16k rows of high-quality prose. | Acts as a buffer/filler to balance segment lengths and inject linguistic variety (e.g., neuroscience/biology). |

# | \*\*/factbook\*\* | CIA World Factbook (2026 current) + Python parsers. | Provides rigorous geopolitical and statistical grounding for objective world knowledge. |

# | \*\*/pokemon\*\* | 1025-row stats and \~14k-row instruction set. | High-density taxonomic and logical instruction-following data. |

# | \*\*/scripts\*\* | Text cleaning, normalization, and ingestion tools. | Contains `txt2jsonl.py` for user data and tools to ensure all data is terminal-safe and ANSI-compliant. |

# | \*\*/space\*\* | \~100 row solar system facts (solar.jsonl). | Specific domain grounding for astronomical data and instructional prompts. |

# | \*\*/text\*\* | \~30k poems, oss.jsonl (2M words), and titles.md. | The "Wyrm" core—developing rhythmic sensitivity and linguistic nuance via classic and public domain works. |

# | \*\*/user\_data\*\* | Local drop-zone for custom text files. | The integration point for adding personal `.txt` and `.md` files to the training run. |

# | \*\*/wikifacts\*\* | \~300k rows of simple, plain-text facts. | The foundational logic layer (e.g., "April is the 4th month") for consistent reasoning. |

# 

# \## Core Components

# 

# \### 1. The Knowledge Base (/wikifacts \& /factbook)

# With over 300,000 simple facts and the 2026 CIA Factbook, this layer ensures the model doesn't hallucinate foundational reality. The included Python scripts allow for multi-year parsing to maintain temporal accuracy.

# 

# \### 2. The Artistic Core (/text)

# The poetry collection (\~30k rows) and the `oss.jsonl` starter set are designed to sharpen the model’s grasp of cadence, logic, and long-form narrative. While private works are excluded from the public push, they are indexed in `titles.md` for transparency.

# 

# \### 3. Structural Filling (/articles)

# The 16,000 diverse articles (including science and biology features) are used to fill "token gaps." If a training block is short on data, these articles provide high-quality "noise" to prevent the model from overfitting on specific formats.

# 

# \### 4. Specialized Logic (/pokemon \& /space)

# Instruction sets like the Pokémon data (\~14k rows) test the model's ability to handle complex, interconnected stats and specific user queries within a closed system.

# 

# \## Technical Standards

# 

# \*\*Terminal Safety:\*\* All datasets in this repository are processed to be ANSI/ASCII compliant. We strip "smart" characters (curly quotes, em-dashes) and Unicode artifacts that interfere with screen readers or legacy terminal outputs.

# 

# \*\*Cleaning Pipeline:\*\*

# Current tools in the `/scripts` directory include:

# \* \*\*Unicode Normalization:\*\* Standardizing character sets for clean training loss.

# \* \*\*Pronoun Replacement:\*\* Refined text processing for consistent instruction-tuning.

# \* \*\*txt2jsonl.py:\*\* Automated mapping of title/author text files into the IDG-Suite JSONL format.

# 

# This structure puts us at roughly 100 million base tokens, creating a dense, versatile environment for the next generation of iDragonfly models.



