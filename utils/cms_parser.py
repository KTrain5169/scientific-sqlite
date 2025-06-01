import os
import json
import frontmatter
import importlib.util
from typing import List, Dict, Any
from config.settings import settings
from pydantic import BaseModel
import markdown

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
    Recursively parse Markdown files in the collection_path directory.
    Files with .md extension are processed. Returns a list of document
    dictionaries with frontmatter metadata, compiled HTML content, and a computed URL path.
    """
    docs = []
    schema = load_schema(collection_path)
    
    for root, dirs, files in os.walk(collection_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            # Process only Markdown files
            if ext != ".md":
                continue
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            post = frontmatter.loads(content)
            data = post.metadata
            body = post.content

            # Validate against schema if available and if CMS_SCHEMA_VALIDATION is not "off"
            if schema and callable(schema):
                try:
                    validated = schema(**data)
                    if isinstance(validated, BaseModel):
                        data = validated.dict()
                    else:
                        data = getattr(validated, "__dict__", data)
                except Exception as e:
                    msg = f"Schema validation error for file {file_path}: {e}"
                    if settings.CMS_SCHEMA_VALIDATION.lower() == "enforce":
                        raise ValueError(msg)
                    elif settings.CMS_SCHEMA_VALIDATION.lower() == "warn":
                        print("WARNING:", msg)
            
            # Compile the Markdown content to HTML
            compiled_body = markdown.markdown(body)
            
            # Compute the relative URL path
            rel_path = os.path.relpath(file_path, collection_path)
            rel_path_no_ext = os.path.splitext(rel_path)[0].replace(os.sep, "/")
            base_name = os.path.basename(rel_path_no_ext)
            
            if base_name == "index":
                # For index file, use the directory path (empty string for collection root)
                url_path = os.path.dirname(rel_path_no_ext) or ""
            else:
                # Otherwise, build directory-based URL: folder/filename/
                dir_part = os.path.dirname(rel_path_no_ext)
                if dir_part:
                    url_path = f"{dir_part}/{base_name}/"
                else:
                    url_path = f"{base_name}"
            
            docs.append({
                "filename": url_path,
                "metadata": data,
                "body": compiled_body,
                "source": file_path
            })
            
    return docs