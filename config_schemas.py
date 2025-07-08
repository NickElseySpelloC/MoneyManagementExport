"""Configuration schemas for use with the SCConfigManager class."""


class ConfigSchema:
    """Base class for configuration schemas."""

    def __init__(self):
        self.default = {
            "MoneyManagement": {
                "HeadlessMode": False,
                "PageLoad": 20,
                "Funds": [
                    {
                        "URL": "https://investmentcentre.moneymanagement.com.au/factsheets/AH/09x2/pimco-global-bond-wholesale",
                        "Symbol": "ETL0018AU",
                        "Name": "PIMCO Global Bond",
                    }
                ]
            },
            "Files": {
                "OutputCSV": "price_data.csv",
                "DaysToSave": 30,
                "LogfileName": "logfile.log",
                "LogfileMaxLines": 500,
                "LogfileVerbosity": "detailed",
                "ConsoleVerbosity": "summary",
            },
            "Email": {
                "EnableEmail": False,
                "SendEmailsTo": None,
                "SMTPServer": None,
                "SMTPPort": None,
                "SMTPUsername": None,
                "SMTPPassword": None,
                "SubjectPrefix": None,
            },
        }

        self.placeholders = {
            "Email": {
                "SendEmailsTo": "<Your email address here>",
                "SMTPUsername": "<Your SMTP username here>",
                "SMTPPassword": "<Your SMTP password here>",
            }
        }

        self.validation = {
            "MoneyManagement": {
                "type": "dict",
                "schema": {
                    "HeadlessMode": {"type": "boolean", "required": False, "nullable": True},
                    "PageLoad": {"type": "number", "required": True},
                    "Funds": {
                        "type": "list",
                        "required": True,
                        "schema": {
                            "type": "dict",
                            "schema": {
                                "URL": {"type": "string", "required": True},
                                "Symbol": {"type": "string", "required": False, "nullable": True},
                                "Name": {"type": "string", "required": False, "nullable": True},
                            },
                        },
                    },
                },
            },
            "Files": {
                "type": "dict",
                "schema": {
                    "OutputCSV": {"type": "string", "required": True},
                    "DaysToSave": {
                        "type": "number",
                        "required": False,
                        "nullable": True,
                        "min": 0,
                        "max": 365,
                    },
                    "LogfileName": {"type": "string", "required": False, "nullable": True},
                    "LogfileMaxLines": {"type": "number", "min": 0, "max": 100000},
                    "LogfileVerbosity": {
                        "type": "string",
                        "required": True,
                        "allowed": ["none", "error", "warning", "summary", "detailed", "debug", "all"],
                    },
                    "ConsoleVerbosity": {
                        "type": "string",
                        "required": True,
                        "allowed": ["error", "warning", "summary", "detailed", "debug", "all"],
                    },
                 },
            },
            "Email": {
                "type": "dict",
                "schema": {
                    "EnableEmail": {"type": "boolean", "required": True},
                    "SendEmailsTo": {"type": "string", "required": False, "nullable": True},
                    "SMTPServer": {"type": "string", "required": False, "nullable": True},
                    "SMTPPort": {"type": "number", "required": False, "nullable": True, "min": 25, "max": 1000},
                    "SMTPUsername": {"type": "string", "required": False, "nullable": True},
                    "SMTPPassword": {"type": "string", "required": False, "nullable": True},
                    "SubjectPrefix": {"type": "string", "required": False, "nullable": True},
                },
            },
        }

        self.csv_header_config = [
            {
                "name": "Symbol",
                "type": "str",
                "match": True,
                "sort": 2,
            },
            {
                "name": "Date",
                "type": "date",
                "format": "%Y-%m-%d",
                "match": True,
                "sort": 1,
                "minimum": None,
            },
            {
                "name": "Name",
                "type": "str",
            },
            {
                "name": "Currency",
                "type": "str",
            },
            {
                "name": "Price",
                "type": "float",
                "format": ".2f",
            },
        ]
