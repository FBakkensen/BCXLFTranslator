class InvalidXliffError(Exception):
    """Exception raised when the file is not a valid XLIFF file (missing <xliff> root)."""
    pass

class EmptyXliffError(Exception):
    """Exception raised when the XLIFF file is empty."""
    pass