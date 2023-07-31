class IgnorableException(Exception):
    """Used for errors in transformers that should be ignored."""

    # For example, used when a transformer fails to find its target.
