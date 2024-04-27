# Base classes for interacting with databases

from collections.abc import Callable
from contextlib import AbstractContextManager
import datetime
import errno
from pathlib import Path
from typing import Self

import parse
from PySide6.QtSql import QSqlDatabase, QSqlError, QSqlQuery

from baseClasses import LEARNING_LEVEL

class Data:
    def __init__(self) -> None:
        pass

class Database(AbstractContextManager):
    """Base class for all language databases"""

    def __init__(self, dbName: str) -> None:
        self.db = dbName
        self.con = QSqlDatabase.addDatabase("QSQLITE")
        self.con.setDatabaseName(self.db)

    def __enter__(self) -> Self:
        self.open()
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_value, traceback) -> (bool | None):
        self.close()
        return super().__exit__(exc_type, exc_value, traceback)

    def _execQuery(self, /, query: str, **kwargs: str) -> tuple[bool, QSqlQuery]:
        """Executes query with given keyword arguments"""
        _query = QSqlQuery(self.con)
        _query.setForwardOnly(True)
        r = _query.prepare(query)
        for key, value in kwargs.items():
            _query.bindValue(f":{key}", value)
        result = _query.exec()
        return (result, _query)

    def _execQueryNoResults(self, /, query: str, **kwargs: str) -> bool:
        """Executes query with given keyword arguments, returns success/fail"""
        return self._execQuery(query, **kwargs)[0]

    def _execQueryGetResult(
            self,
            /,
            query: str,
            **kwargs: str
        ) -> object:
        """Executes query with given keyword arguments and returns the single value stored"""
        _query = self._execQuery(query, **kwargs)[1]
        _query.next()
        result = _query.value(0)
        _query.finish()
        return result

    def _execQueryGetResults(
            self,
            /,
            query: str,
            constructor: Callable[[QSqlQuery], object],
            **kwargs: str
        ) -> list[object]:
        """Executes query with given keyword arguments and packages data via a constructor"""
        _query = self._execQuery(query, **kwargs)[1]
        results = []
        while _query.next():
            results.append(constructor(_query))
        _query.finish()
        return results
    
    @staticmethod
    def formatTimeToStr(time: datetime.datetime) -> str:
        """Converts to YYYY-MM-DD HH:MM:SS"""
        year = f"{time.year:04}"
        month = f"{time.month:02}"
        day = f"{time.day:02}"
        hour = f"{time.hour:02}"
        minute = f"{time.minute:02}"
        second = f"{time.second:02}"
        return f"{year}-{month}-{day} {hour}:{minute}:{second}"

    @staticmethod
    def formatTimeToDateTime(time: str) -> datetime.datetime:
        """Converts from YYYY-MM-DD HH:MM:SS to datetime object"""
        return parse.parse("{:%Y-%m-%d %H:%M:%S}", time)[0]
    
    def close(self) -> None:
        """Close database connection"""
        if self.con.isOpen():
            self.con.close()

    def open(self) -> bool:
        """Opens database connection. Returns True if successful, False otherwise"""
        if self.con.isOpen(): # Already open
            return
        if not Path(self.db).is_file():
            raise FileNotFoundError(errno.ENOENT, "Unable to find given file", self.db)
        result = self.con.open()
        if not result:
            match self.con.lastError().type():
                case QSqlError.ErrorType.NoError:
                    pass
                case QSqlError.ErrorType.ConnectionError:
                    raise ConnectionRefusedError(errno.ECONNREFUSED, "Connection refused for file", self.db)
                case QSqlError.ErrorType.StatementError: # Should be impossible
                    raise RuntimeError("Unable to open database due to a statement error")
                case QSqlError.ErrorType.TransactionError: # Should be impossible
                    raise RuntimeError("Unable to open database due to a transaction error")
                case QSqlError.ErrorType.UnknownError:
                    raise RuntimeError("Unable to open database for unknown reason")
                case _:
                    pass
        return result
    
    def deletePhrase(self, id: int) -> bool:
        """Deletes given phrase via ID"""
        raise NotImplementedError

    def getPhraseById(self, id: int) -> Data | None:
        """Returns the datum associated with the given ID if exists"""
        raise NotImplementedError

    def getPhrases(self, level: LEARNING_LEVEL, maxOrdinalID: int) -> list[Data]:
        """Gets a list of phrase data given a particular level and an upper bound in that level"""
        raise NotImplementedError

    def getPhrasesDueToday(self, level: LEARNING_LEVEL, maxOrdinalID: int, limit: int=None) -> list[Data]:
        """Gets a list of phrases that are due today (i.e. date <= now())"""
        raise NotImplementedError

    def getResponseTimeAverage(self) -> float:
        """Returns the average response time"""
        raise NotImplementedError
    
    def getResponseTimeCount(self) -> int:
        """Returns the number of response times"""
        raise NotImplementedError

    def getResponseTimeVariance(self) -> float:
        """Returns the variance in response times"""
        raise NotImplementedError

    def initializeDB(self) -> bool:
        """Creates table schemas"""
        raise NotImplementedError
    
    def insertPhrase(self, band: LEARNING_LEVEL, ordinalID: int, data: Data) -> bool:
        """Inserts into database a new phrase given phrase data"""
        raise NotImplementedError
    
    def insertResponseTime(self, id: int, timeStamp: datetime.datetime, responseTime: float) -> bool:
        """Logs how long one took to answer a flashcard"""
        raise NotImplementedError

    def isOpen(self) -> bool:
        """Returns True if connection is open"""
        return self.con.isOpen()

    def updatePhrase(
            self, 
            id: int, 
            wasCorrect: bool,  
            dueDate: datetime.datetime, 
            easeFactor: float,
            lastTimeCorrect: datetime.datetime=None
        ) -> bool:
        """Updates entry with the user's results (were they correct in answering or not)"""
        raise NotImplementedError