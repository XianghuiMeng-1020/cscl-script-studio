"""JSON Schema validator for normalized specs"""
import json
import os
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError, Draft7Validator


def load_normalized_spec_schema() -> Dict[str, Any]:
    """Load normalized spec schema from file"""
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'docs',
        'SCHEMA_NORMALIZED_SPEC.json'
    )
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_normalized_spec(normalized_spec: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate normalized spec against JSON schema
    
    Returns:
        (is_valid, error_message)
    """
    try:
        schema = load_normalized_spec_schema()
        validate(instance=normalized_spec, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"
