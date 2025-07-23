# Scientific CMS

A lightweight CMS parser for Markdown content with frontmatter support.

## Features

- Parse Markdown files with YAML frontmatter
- Schema validation (Pydantic or JSON Schema)
- Flexible URL generation
- Configurable validation modes

## Installation

```bash
pip install scientific-cms
```

## Usage

```python
from scientific_cms import parse_collection

docs = parse_collection("path/to/content")
for doc in docs:
    print(doc.metadata["title"])
    print(doc.compiled_body)
```
