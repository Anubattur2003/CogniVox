"""
TOON (Token-Oriented Object Notation) Format Encoder/Decoder

TOON is a compact, human-readable, schema-aware JSON format optimized for LLM prompts.
Reference: https://github.com/toon-format/toon
"""
import json
import re
from typing import Any, Dict, List, Optional, Union
from collections.abc import Mapping, Sequence


class TOONEncoder:
    """Encoder for converting Python objects to TOON format."""
    
    @staticmethod
    def encode(obj: Any, delimiter: str = ",") -> str:
        """
        Encode a Python object to TOON format.
        
        Args:
            obj: Python object (dict, list, primitive)
            delimiter: Field delimiter (default: comma for token efficiency)
            
        Returns:
            TOON-formatted string
        """
        if obj is None:
            return "null"
        elif isinstance(obj, bool):
            return "true" if obj else "false"
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, str):
            # Escape special characters
            return TOONEncoder._escape_string(obj, delimiter)
        elif isinstance(obj, Mapping):
            return TOONEncoder._encode_object(obj, delimiter)
        elif isinstance(obj, Sequence):
            return TOONEncoder._encode_array(obj, delimiter)
        else:
            # Fallback to JSON string representation
            return json.dumps(obj)
    
    @staticmethod
    def _escape_string(s: str, delimiter: str = ",") -> str:
        """Escape special characters in strings."""
        # Only escape if necessary
        if any(c in s for c in ['"', '\n', '\r', '\t', delimiter]):
            return json.dumps(s)
        return s
    
    @staticmethod
    def _encode_object(obj: Dict[str, Any], delimiter: str) -> str:
        """Encode a dictionary/object to TOON format."""
        if not obj:
            return "{}"
        
        # Get all keys
        keys = list(obj.keys())
        
        # Build header: key1[key_count]{key1,key2,key3}:
        key_list = delimiter.join(keys)
        header = f"{keys[0]}[{len(keys)}]{{{key_list}}}:"
        
        # Build rows
        rows = []
        if isinstance(obj[keys[0]], Sequence) and not isinstance(obj[keys[0]], str):
            # Array of objects
            array_length = len(obj[keys[0]])
            for i in range(array_length):
                row_values = []
                for key in keys:
                    # Safely handle non-sequence values (like integers, strings, etc.)
                    if isinstance(obj[key], Sequence) and not isinstance(obj[key], str):
                        value = obj[key][i] if i < len(obj[key]) else None
                    else:
                        # For non-sequence values, use the value itself for all rows
                        value = obj[key]
                    row_values.append(TOONEncoder.encode(value, delimiter))
                rows.append(delimiter.join(str(v) for v in row_values))
        else:
            # Single object
            row_values = [TOONEncoder.encode(obj[key], delimiter) for key in keys]
            rows.append(delimiter.join(str(v) for v in row_values))
        
        return "\n".join([header] + rows)
    
    @staticmethod
    def _encode_array(arr: List[Any], delimiter: str) -> str:
        """Encode an array to TOON format."""
        if not arr:
            return "[]"
        
        # If array contains objects, use object format
        if arr and isinstance(arr[0], Mapping):
            # Merge objects into single structure
            all_keys = set()
            for item in arr:
                all_keys.update(item.keys())
            
            # Create object with arrays for each key
            merged = {}
            for key in sorted(all_keys):
                merged[key] = [item.get(key) for item in arr]
            
            return TOONEncoder._encode_object(merged, delimiter)
        else:
            # Simple array
            values = [TOONEncoder.encode(item, delimiter) for item in arr]
            return f"[{len(arr)}]:\n" + "\n".join(values)


class TOONDecoder:
    """Decoder for converting TOON format to Python objects."""
    
    @staticmethod
    def decode(toon_str: str, delimiter: str = ",") -> Any:
        """
        Decode a TOON-formatted string to Python object.
        
        Args:
            toon_str: TOON-formatted string
            delimiter: Field delimiter (default: comma)
            
        Returns:
            Python object (dict, list, or primitive)
        """
        toon_str = toon_str.strip()
        
        if not toon_str:
            return None
        
        # Handle null, boolean, number primitives
        if toon_str == "null":
            return None
        elif toon_str == "true":
            return True
        elif toon_str == "false":
            return False
        elif toon_str.isdigit() or (toon_str.startswith("-") and toon_str[1:].isdigit()):
            return int(toon_str)
        elif re.match(r'^-?\d+\.\d+$', toon_str):
            return float(toon_str)
        
        # Handle arrays
        if toon_str.startswith("["):
            return TOONDecoder._decode_array(toon_str, delimiter)
        
        # Handle objects
        if "{" in toon_str and "}:" in toon_str:
            return TOONDecoder._decode_object(toon_str, delimiter)
        
        # Handle strings (unquoted if no special chars)
        if toon_str.startswith('"') and toon_str.endswith('"'):
            return json.loads(toon_str)
        
        return toon_str
    
    @staticmethod
    def _decode_array(toon_str: str, delimiter: str) -> List[Any]:
        """Decode TOON array format."""
        lines = toon_str.split("\n")
        if not lines:
            return []
        
        # Parse header: [count]:
        header = lines[0]
        match = re.match(r'\[(\d+)\]:', header)
        if match:
            count = int(match.group(1))
            values = []
            for line in lines[1:]:
                if line.strip():
                    values.append(TOONDecoder.decode(line.strip(), delimiter))
            return values[:count]
        
        return []
    
    @staticmethod
    def _decode_object(toon_str: str, delimiter: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Decode TOON object format."""
        lines = [line.strip() for line in toon_str.split("\n") if line.strip()]
        if not lines:
            return {}
        
        # Parse header: key[count]{key1,key2,key3}:
        header = lines[0]
        match = re.match(r'(\w+)\[(\d+)\]\{([^}]+)\}:', header)
        if not match:
            return {}
        
        first_key = match.group(1)
        key_count = int(match.group(2))
        key_list_str = match.group(3)
        keys = [k.strip() for k in key_list_str.split(delimiter)]
        
        # Parse data rows
        rows = []
        for line in lines[1:]:
            if line.strip():
                values = [v.strip() for v in line.split(delimiter)]
                row_dict = {}
                for i, key in enumerate(keys):
                    if i < len(values):
                        row_dict[key] = TOONDecoder.decode(values[i], delimiter)
                    else:
                        row_dict[key] = None
                rows.append(row_dict)
        
        # If single row, return dict; if multiple rows, return list of dicts
        if len(rows) == 1:
            return rows[0]
        else:
            # Convert to array of objects format
            result = {}
            for key in keys:
                result[key] = [row.get(key) for row in rows]
            return result


def encode_toon(obj: Any, delimiter: str = ",") -> str:
    """Convenience function to encode to TOON format."""
    return TOONEncoder.encode(obj, delimiter)


def decode_toon(toon_str: str, delimiter: str = ",") -> Any:
    """Convenience function to decode from TOON format."""
    return TOONDecoder.decode(toon_str, delimiter)


def format_system_instruction(instruction_data: Dict[str, Any]) -> str:
    """
    Format system instruction data using TOON format for LLM prompts.
    
    Args:
        instruction_data: Dictionary containing instruction structure
        
    Returns:
        Formatted system instruction string
    """
    toon_str = encode_toon(instruction_data)
    return f"```toon\n{toon_str}\n```"

