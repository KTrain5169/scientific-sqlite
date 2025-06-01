import os
import json
import frontmatter
from typing import List, Dict, Any
import importlib.util

from config.settings import settings
from pydantic import BaseModel

def load_schema(collection_path: str) -> Any:
    """
    Look for a schema.py or schema.json file in the collection_path and load it.
    The schema should define a data structure (for example, a Pydantic model or a dictionary)
    named SCHEMA if using a Python file.
    """
    schema_py = os.path.join(collection_path, "schema.py")
    schema_json = os.path.join(collection_path, "schema.json")
    if os.path.exists(schema_py):
        spec = importlib.util.spec_from_file_location("schema", schema_py)
        if spec is None or spec.loader is None:
            return None
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        return getattr(schema_module, "SCHEMA", None)
    elif os.path.exists(schema_json):
        with open(schema_json, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def parse_collection(collection_path: str) -> List[Dict[str, Any]]:
    """
    Recursively parse Markdown (or MDX/Markdoc) files in the collection_path directory.
    Files with .md or .mdx extensions are processed.
    Returns a list of documents with extracted frontmatter, content and a computed URL path.
    """
    docs = []
    schema = load_schema(collection_path)
    
    for root, dirs, files in os.walk(collection_path):
        for filename in files:
            # Skip schema files
            if filename.startswith("schema"):
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".md", ".mdx"]:
                continue
            file_path = os.path.join(root, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
    
            post = frontmatter.loads(content)
            data = post.metadata
            body = post.content
            
            # Validate against schema if available and if CMS_SCHEMA_VALIDATION is not set to "off"
            if schema and callable(schema):
                try:
                    # Assuming schema is a Pydantic model class
                    validated = schema(**data)
                    if isinstance(validated, BaseModel):
                        data = validated.dict()
                    else:
                        # Fallback to using __dict__ if available.
                        data = getattr(validated, "__dict__", data)
                except Exception as e:
                    message = f"Schema validation error for file {file_path}: {e}"
                    if settings.CMS_SCHEMA_VALIDATION.lower() == "enforce":
                        raise ValueError(message)
                    elif settings.CMS_SCHEMA_VALIDATION.lower() == "warn":
                        print("WARNING:", message)
                    # If "off", ignore validation errors
            
            # Compute the file's relative path to the collection folder
            rel_path = os.path.relpath(file_path, collection_path)
            # Remove the original extension
            rel_path_no_ext = os.path.splitext(rel_path)[0]
            # Normalize path to use forward slashes for URL construction
            rel_path_no_ext = rel_path_no_ext.replace(os.sep, "/")
            
            # If the file name isn't "index", convert it to a directory-based route.
            # For example: v1.md becomes v1/index.html 
            base_name = os.path.basename(rel_path_no_ext)
            if base_name != "index":
                dir_part = os.path.dirname(rel_path_no_ext)
                if dir_part:
                    url_path = f"{dir_part}/{base_name}/index.html"
                else:
                    url_path = f"{base_name}/index.html"
            else:
                url_path = f"{rel_path_no_ext}.html"
    
            docs.append({
                "filename": url_path,
                "metadata": data,
                "body": body,
            })
    return docs