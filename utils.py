def is_valid_data(data):
    """
    Validates the input data.

    Parameters:
        - data

    Returns:
        - bool
        - str 
    """
    if not data or "groupId" not in data:
        return False, "Bad request. Missing 'groupId'."
    if not isinstance(data["groupId"], str):
        return False, "'groupId' must be a string."
    return True, None
