
""" Here we save the sql table templates.
    Other functions can call it for creating new table.

    NOTE: The first column would be set as key column.
"""

SYMBOLS = {
    "symbol": "CHAR(20)",
    "market": "CHAR(2)",
    "type": "CHAR(20)",
    "check_date": "INT",
    "enable": "BOOLEAN",
    "auto_update": "BOOLEAN"
}
