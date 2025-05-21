class InvalidXliffError(Exception):
    """Exception raised when the file is not a valid XLIFF file (missing <xliff> root)."""
    pass

class EmptyXliffError(Exception):
    """Exception raised when the XLIFF file is empty."""
    pass

class MalformedXliffError(Exception):
    """Exception raised when the XLIFF file is malformed or has structural issues."""
    pass

class NoTransUnitsError(Exception):
    """Exception raised when the XLIFF file does not contain any trans-unit elements."""
    pass