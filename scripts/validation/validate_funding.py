#!/usr/bin/env python3
"""
Data Validation System
Validates funding data against schema and quality rules
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ValidationResult:
    """Result of validation operation"""
    
    def __init__(self):
        self.passed = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: Dict[str, Any] = {}
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
    
    def add_info(self, key: str, value: Any):
        """Add informational metadata"""
        self.info[key] = value
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'passed': self.passed,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def __str__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        output = [f"Validation {status}"]
        
        if self.errors:
            output.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                output.append(f"  - {error}")
        
        if self.warnings:
            output.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                output.append(f"  - {warning}")
        
        if self.info:
            output.append(f"\nInfo:")
            for key, value in self.info.items():
                output.append(f"  {key}: {value}")
        
        return "\n".join(output)


class FundingDataValidator:
    """Validator for funding data files"""
    
    def __init__(self, schema_path: Optional[Path] = None, required_columns: Optional[List[str]] = None):
        """
        Initialize validator
        
        Args:
            schema_path: Path to JSON schema file (optional)
            required_columns: List of required column names (optional)
        """
        self.schema = None
        self.required_columns = required_columns or []
        
        if schema_path and schema_path.exists():
            with open(schema_path) as f:
                self.schema = json.load(f)
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a data file
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            ValidationResult object
        """
        result = ValidationResult()
        
        # Check file exists
        if not file_path.exists():
            result.add_error(f"File does not exist: {file_path}")
            return result
        
        # Check file is readable
        try:
            content = file_path.read_text()
            result.add_info('file_size_bytes', len(content))
        except Exception as e:
            result.add_error(f"Cannot read file: {e}")
            return result
        
        # Validate based on file type
        if file_path.suffix == '.json':
            return self._validate_json(file_path, content, result)
        elif file_path.suffix == '.csv':
            return self._validate_csv(file_path, content, result)
        else:
            result.add_warning(f"Unknown file type: {file_path.suffix}")
        
        return result
    
    def _validate_json(self, file_path: Path, content: str, result: ValidationResult) -> ValidationResult:
        """Validate JSON file"""
        try:
            data = json.loads(content)
            result.add_info('format', 'json')
            
            # Check if it's a list or single object
            if isinstance(data, list):
                result.add_info('record_count', len(data))
                
                # Validate each record
                for idx, record in enumerate(data):
                    self._validate_record(record, f"Record {idx}", result)
                    
            elif isinstance(data, dict):
                result.add_info('record_count', 1)
                self._validate_record(data, "Root object", result)
            
            else:
                result.add_error(f"JSON data must be object or array, got: {type(data)}")
            
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")
        
        return result
    
    def _validate_csv(self, file_path: Path, content: str, result: ValidationResult) -> ValidationResult:
        """Validate CSV file"""
        try:
            lines = content.strip().split('\n')
            if not lines:
                result.add_error("CSV file is empty")
                return result
            
            result.add_info('format', 'csv')
            
            # Parse header
            header = lines[0].split(',')
            header = [col.strip() for col in header]
            result.add_info('columns', header)
            result.add_info('record_count', len(lines) - 1)
            
            # Check required columns
            for required in self.required_columns:
                if required not in header:
                    result.add_error(f"Missing required column: {required}")
            
            # Check for data rows
            if len(lines) < 2:
                result.add_warning("CSV has header but no data rows")
            
        except Exception as e:
            result.add_error(f"Error parsing CSV: {e}")
        
        return result
    
    def _validate_record(self, record: dict, context: str, result: ValidationResult):
        """Validate a single record"""
        
        # Check required columns
        for required in self.required_columns:
            if required not in record:
                result.add_error(f"{context}: Missing required field '{required}'")
            elif record[required] is None or record[required] == "":
                result.add_warning(f"{context}: Field '{required}' is empty")
        
        # Check for common funding data fields
        if 'amount' in record:
            amount = record['amount']
            if not isinstance(amount, (int, float)):
                try:
                    float(str(amount).replace(',', '').replace('$', ''))
                except (ValueError, TypeError):
                    result.add_error(f"{context}: Invalid amount value: {amount}")
        
        if 'date' in record:
            date_value = record['date']
            if date_value:
                try:
                    # Try parsing common date formats
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            datetime.strptime(str(date_value), fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        result.add_warning(f"{context}: Date format may be non-standard: {date_value}")
                except Exception:
                    result.add_warning(f"{context}: Could not validate date: {date_value}")


def validate_directory(directory: Path, validator: FundingDataValidator) -> Dict[str, ValidationResult]:
    """
    Validate all files in a directory
    
    Args:
        directory: Directory to scan
        validator: Validator instance
        
    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}
    
    for file_path in directory.rglob('*.json'):
        results[str(file_path)] = validator.validate_file(file_path)
    
    for file_path in directory.rglob('*.csv'):
        results[str(file_path)] = validator.validate_file(file_path)
    
    return results


if __name__ == "__main__":
    # Test validation
    test_dir = Path("logs/test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test JSON file
    test_data = [
        {"grant_id": "G001", "amount": 50000, "date": "2024-01-15", "source": "Test Fund"},
        {"grant_id": "G002", "amount": 75000, "date": "2024-02-20", "source": "Test Fund"}
    ]
    
    test_file = test_dir / "test_data.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Validate
    validator = FundingDataValidator(required_columns=['grant_id', 'amount', 'date', 'source'])
    result = validator.validate_file(test_file)
    
    print(result)
    print("\nValidation test complete.")
    
    # Cleanup
    test_file.unlink()
