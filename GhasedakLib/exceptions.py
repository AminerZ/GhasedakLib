"""
ghasedak.exceptions
-------------------

This module contains the set of Ghasedaks' exceptions.
"""

class ApiException(Exception):
    """There was an ambiguous exception that occurred while handling your
    ghasedak api request.
    """
   
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        if 400 <= self.code < 500 : return f"{self.code} Client Error: {self.message}"

