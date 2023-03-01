class StringDict(dict):
    """
    A dictionary subclass that coerces all its values to strings.

    This class inherits from the built-in `dict` class, and overrides its
    constructor and two methods to ensure that all values are converted
    to strings.

    Attributes:
    -----------
    data : dict
        The dictionary of key-value pairs to be converted to strings.

    Methods:
    --------
    __init__(self, data)
        Initializes a new instance of the `StringDict` class with a given
        dictionary. All values are coerced to strings using the `str()` function.

    __getitem__(self, key)
        Gets the value associated with the specified key, and coerces it to a string
        using the `str()` function.

    get(self, key, default=None)
        Gets the value associated with the specified key, or returns the default
        value if the key is not present. All values are coerced to strings using
        the `str()` function.
    """

    def __init__(self, data):
        """
        Initialize the StringDict object with the given dictionary by converting all its values to strings.

        Parameters:
        ----------
        data : dict
            The dictionary to be initialized as a StringDict object.

        """
        data = {k: str(v) for k, v in data.items()}
        super().__init__(data)

    def __getitem__(self, key):
        """
       Get the value for the given key as a string.

       Parameters:
       ----------
       key : str
           The key whose value is to be retrieved.

       Returns:
       -------
       str
           The value for the given key as a string.

       """

        value = super().__getitem__(key)
        return str(value)

    def get(self, key, default=None):
        """
        Get the value for the given key as a string. If the key is not present, return the given default value.

        Parameters:
        ----------
        key : str
            The key whose value is to be retrieved.
        default : object
            The value to be returned if the key is not present in the StringDict object. Defaults to None.

        Returns:
        -------
        str
            The value for the given key as a string, or the default value if the key is not present.

        """

        value = super().get(key, default)
        return str(value)