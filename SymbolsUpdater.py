
from . import mysql
from . import iexcloudapi
from . import SQLTemples
from . import timestamp
from . import TerminalReporter

import os
import json
from datetime import datetime


class Updater:

    def __init__(self, sql_config_path: str= None, iextoken_path: str=None):
        self.iexapi = iexcloudapi.IEXAPI(tokenConfigPath=iextoken_path)
        if sql_config_path == None:
            self.sql_config_path = "./sql_config.json"
        else:
            self.sql_config_path = sql_config_path
        self.__get_sql_config()
        self.symbolDB = mysql.DB("symbols", self.host, self.port, self.user, self.password)
        self.__save_sql_config()
        self.__initialize_DB()
        self.symbolsTB = self.symbolDB.TB("symbols")

    def update_US(self):
        """
        Update symbols of US market.
        """
        reporter = TerminalReporter.Reporter("SymbolUpdater", "Updating US symbols...")
        reporter.report()
        symbols = self.iexapi.get_symbolList()
        query = self.symbolsTB.query("*", "WHERE market = 'US'")
        # we create a empty update list for insert new symbols
        insert_symbols = {}
        # disable all symbols
        reporter.what = "Disabling US symbols..."
        reporter.initialize_stepIntro(len(query))
        for symbol in query:
            reporter.report(True)
            if query[symbol]["auto_update"] == True:
                query[symbol]["enable"] = False
        # before we update the symbol list,
        # we get the timestamp today
        today = datetime.now()
        today = timestamp.to_timestampe(today)
        today = timestamp.to_midnight(today)
        # enable symbols
        reporter.what = "Enabling US symbols..."
        reporter.initialize_stepIntro(len(symbols))
        for symbol in symbols:
            reporter.report(True)
            # if symbol set to not auto-update,
            # we skip to update that symbol
            if symbol in query and query[symbol]["auto_update"] == False:
                continue
            if symbol in query:
                query[symbol]["enable"] = True
                query[symbol]["check_date"] = today
            else:
                insert_symbols[symbol] = {
                    "market": "us",
                    "check_date": today,
                    "enable": True,
                    "auto_update": True
                }
        # update to the sql server
        reporter.what = "Updating SQL Server..."
        reporter.report()
        if len(insert_symbols) > 0:
            self.symbolsTB.update(insert_symbols)
        if len(query) > 0:
            self.symbolsTB.update(query)
        self.symbolDB.commit()
        self.symbolDB.close()
        reporter.what = "Done."
        reporter.report()

    def __initialize_DB(self):
        tbs = self.symbolDB.list_tb()
        if not "symbols" in tbs:
            self.__create_tb_with_templates("symbols", SQLTemples.SYMBOLS)

    def __create_tb_with_templates(self, tableName: str, temp: dict):
        colnames = list(temp.keys())
        # first column as key column
        tb = self.symbolDB.add_tb(tableName, colnames[0], temp[colnames[0]])
        for i in range(1, len(colnames)):
            colname = colnames[i]
            tb.add_col(colname, temp[colname])
    
    def __get_sql_config(self):
        if not os.path.exists(self.sql_config_path):
            with open(self.sql_config_path, 'w') as f:
                j = {"host": "", "port": 0, "user": "", "password": ""}
                f.write(json.dumps(j))
        with open(self.sql_config_path, 'r') as f:
            sql_config = json.loads(f.read())
        self.host = sql_config["host"]
        self.port = sql_config["port"]
        self.user = sql_config["user"]
        self.password = sql_config["password"]
    
    def __save_sql_config(self):
        j = self.symbolDB.get_loginInfo()
        with open(self.sql_config_path, 'w') as f:
            f.write(json.dumps(j))