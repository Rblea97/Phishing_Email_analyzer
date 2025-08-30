"""
JSON Schema Validation for AI Responses - Phase 3 Security Component

Validates OpenAI GPT-4o-mini responses against strict JSON schema to prevent
injection attacks and ensure data integrity.
"""

from jsonschema import validate, ValidationError
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# JSON Schema for AI phishing analysis response
AI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Risk score from 0-100"
        },
        "label": {
            "type": "string",
            "enum": ["Likely Safe", "Suspicious", "Likely Phishing"],
            "description": "Classification label"
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[A-Z_]+$",
                        "minLength": 1,
                        "maxLength": 50,
                        "description": "Rule ID (uppercase with underscores)"
                    },
                    "description": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 500,
                        "description": "Evidence description"
                    },
                    "weight": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Evidence weight"
                    }
                },
                "required": ["id", "description", "weight"],
                "additionalProperties": False
            },
            "maxItems": 20,
            "description": "Array of evidence objects"
        }
    },
    "required": ["score", "label", "evidence"],
    "additionalProperties": False
}


class AIResponseValidator:
    """Validates AI responses against JSON schema"""
    
    def __init__(self):
        self.schema = AI_RESPONSE_SCHEMA
    
    def validate_response(self, response_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate AI response against schema
        
        Args:
            response_data: AI response dictionary
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            validate(instance=response_data, schema=self.schema)
            
            # Additional business logic validation
            score = response_data.get('score', 0)
            label = response_data.get('label', '')
            
            # Ensure label matches score range
            if score >= 70 and label != "Likely Phishing":
                return False, "High score should have 'Likely Phishing' label"
            elif score <= 30 and label != "Likely Safe":
                return False, "Low score should have 'Likely Safe' label"
            elif 30 < score < 70 and label != "Suspicious":
                return False, "Medium score should have 'Suspicious' label"
            
            # Validate evidence weights sum reasonably
            evidence = response_data.get('evidence', [])
            if evidence:
                total_weight = sum(item.get('weight', 0) for item in evidence)
                if total_weight > score * 2:  # Reasonable upper bound
                    return False, f"Evidence weights ({total_weight}) too high for score ({score})"
            
            logger.info(f"AI response validation passed: score={score}, label={label}, evidence_count={len(evidence)}")
            return True, None
            
        except ValidationError as e:
            error_msg = f"Schema validation failed: {e.message}"
            logger.warning(f"AI response validation failed: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Unexpected validation error: {error_msg}")
            return False, error_msg
    
    def sanitize_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize AI response data for safe storage
        
        Args:
            response_data: Raw AI response
            
        Returns:
            Sanitized response data
        """
        try:
            sanitized = {}
            
            # Sanitize score
            score = response_data.get('score', 0)
            sanitized['score'] = max(0, min(100, int(score)))
            
            # Sanitize label
            valid_labels = ["Likely Safe", "Suspicious", "Likely Phishing"]
            label = response_data.get('label', 'Suspicious')
            sanitized['label'] = label if label in valid_labels else 'Suspicious'
            
            # Sanitize evidence
            evidence = response_data.get('evidence', [])
            sanitized_evidence = []
            
            for item in evidence[:20]:  # Max 20 items
                if isinstance(item, dict):
                    sanitized_item = {
                        'id': str(item.get('id', 'UNKNOWN'))[:50].upper(),
                        'description': str(item.get('description', ''))[:500],
                        'weight': max(1, min(100, int(item.get('weight', 1))))
                    }
                    # Clean ID to only allow A-Z and underscores
                    sanitized_item['id'] = ''.join(c if c.isalnum() or c == '_' else '_' 
                                                 for c in sanitized_item['id'])
                    if sanitized_item['id'] and sanitized_item['description']:
                        sanitized_evidence.append(sanitized_item)
            
            sanitized['evidence'] = sanitized_evidence
            
            logger.info(f"AI response sanitized: {len(sanitized_evidence)} evidence items")
            return sanitized
            
        except Exception as e:
            logger.error(f"Response sanitization failed: {str(e)}")
            # Return safe default
            return {
                'score': 50,
                'label': 'Suspicious',
                'evidence': [{'id': 'AI_ERROR', 'description': 'Response sanitization failed', 'weight': 10}]
            }


# Global validator instance
validator = AIResponseValidator()


def validate_ai_response(response_data: Dict[str, Any]) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Convenience function to validate and sanitize AI response
    
    Args:
        response_data: Raw AI response
        
    Returns:
        tuple: (is_valid, error_message, sanitized_data)
    """
    # First sanitize the response
    sanitized = validator.sanitize_response(response_data)
    
    # Then validate the sanitized response
    is_valid, error = validator.validate_response(sanitized)
    
    return is_valid, error, sanitized


# Example usage and testing
if __name__ == "__main__":
    # Test valid response
    valid_response = {
        "score": 75,
        "label": "Likely Phishing",
        "evidence": [
            {"id": "SPF_FAIL", "description": "SPF authentication failed", "weight": 25},
            {"id": "SUSPICIOUS_URL", "description": "Contains suspicious .xyz domain", "weight": 20}
        ]
    }
    
    is_valid, error, sanitized = validate_ai_response(valid_response)
    print(f"Valid response test: {is_valid}, Error: {error}")
    
    # Test invalid response
    invalid_response = {
        "score": 150,  # Invalid score
        "label": "Invalid Label",
        "evidence": []
    }
    
    is_valid, error, sanitized = validate_ai_response(invalid_response)
    print(f"Invalid response test: {is_valid}, Error: {error}")
    print(f"Sanitized: {sanitized}")