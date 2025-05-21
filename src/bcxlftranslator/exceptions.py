class InvalidXliffError(Exception):
    """Exception raised when the file is not a valid XLIFF file (missing <xliff> root)."""
    pass

class EmptyXliffError(Exception):
    """Exception raised when the XLIFF file is empty."""
    pass

class TerminologyDBError(Exception):
    """Exception raised when there is an error with the terminology database."""
    pass