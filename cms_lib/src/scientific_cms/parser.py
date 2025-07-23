"""Core parsing functionality for Scientific CMS."""

import os
import json
import frontmatter
import importlib.util
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import markdown

from .models import Document, ValidationSettings
from .exceptions import CMSError, SchemaValidationError, SchemaLoadError

try:
    from jsonschema import validate, ValidationError as JSONValidationError
except ImportError:
    validate = None
    JSONValidationError = Exception


class CMSParser:
    """Main CMS parser class."""
    
    def __init__(self, validation_settings: Optional[ValidationSettings] = None):
        self.validation_settings = validation_settings or ValidationSettings()
    
    def load_schema(self, collection_path: str) -> Any:
        """Load schema from collection path."""
        return load_schema(collection_path)
    
    def parse_collection(self, collection_path: str) -> List[Document]:
        """Parse a collection of documents."""
        return parse_collection(collection_path, self.validation_settings)


def load_schema(collection_path: str) -> Any:
    """
    Look for a schema.py or schema.json file in the collection_path and load it.
    """
    schema_py = os.path.join(collection_path, "schema.py")
    schema_json = os.path.join(collection_path, "schema.json")
    
    if os.path.exists(schema_py) and os.path.exists(schema_json):
        raise SchemaLoadError(
            f"Both schema.py and schema.json exist in {collection_path}. Please delete one."
        )
    elif os.path.exists(schema_py):
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


def parse_collection(
    collection_path: str, 
    validation_settings: Optional[ValidationSettings] = None
) -> List[Document]:
    """
    Parse Markdown files in the collection_path directory.
    """
    if validation_settings is None:
        validation_settings = ValidationSettings()
    
    docs = []
    schema = load_schema(collection_path)
    
    for root, dirs, files in os.walk(collection_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext != ".md":
                continue
            
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            post = frontmatter.loads(content)
            data = post.metadata
            body = post.content

            # Schema validation
            if schema:
                try:
                    _validate_schema(data, schema, file_path, validation_settings)
                except SchemaValidationError as e:
                    if validation_settings.mode == "enforce":
                        raise
                    elif validation_settings.mode == "warn":
                        print(f"WARNING: {e}")
            
            # Compile Markdown to HTML
            compiled_body = markdown.markdown(body)
            
            # Compute URL path
            rel_path = os.path.relpath(file_path, collection_path)
            rel_path_no_ext = os.path.splitext(rel_path)[0].replace(os.sep, "/")
            base_name = os.path.basename(rel_path_no_ext)
            
            if base_name == "index":
                url_path = os.path.dirname(rel_path_no_ext) or ""
            else:
                dir_part = os.path.dirname(rel_path_no_ext)
                if dir_part:
                    url_path = f"{dir_part}/{base_name}/"
                else:
                    url_path = f"{base_name}/"
            
            docs.append(Document(
                filename=url_path,
                metadata=data,
                body=body,
                compiled_body=compiled_body,
                source=file_path
            ))
    
    return docs


def _validate_schema(data: Dict[str, Any], schema: Any, file_path: str, settings: ValidationSettings):
    """Validate data against schema."""
    if callable(schema):
        try:
            validated = schema(**data)
            if isinstance(validated, BaseModel):
                return validated.dict()
            else:
                return getattr(validated, "__dict__", data)
        except Exception as e:
            raise SchemaValidationError(f"Schema validation error for {file_path}: {e}")
    
    elif isinstance(schema, dict) and validate is not None:
        try:
            validate(instance=data, schema=schema)
        except JSONValidationError as e:
            raise SchemaValidationError(f"JSON schema validation error for {file_path}: {e}")