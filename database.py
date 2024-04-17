# Base classes for interacting with databases

from collections.abc import Callable
import datetime

from baseClasses import LEARNING_LEVEL

import parse
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

class Data:
    def __init__(self) -> None:
        pass

class Database:
    def __init__(self, dbName: str) -> None:
        self.db = dbName
        self.con = QSqlDatabase.addDatabase("QSQLITE")
        self.con.setDatabaseName(self.db)

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
        self.con.close()

    def open(self) -> bool:
        """Open database connection"""
        return self.con.open()
    
    def deletePhrase(self, id: int) -> bool:
        """Deletes given phrase via ID"""
        raise NotImplementedError
    
    def getPhrases(self, level: LEARNING_LEVEL, maxOrdinalID: int) -> list[Data]:
        """Gets a list of phrase data given a particular level and an upper bound in that level"""
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
    
    def updatePhrase(
            self, 
            id: int, 
            wasCorrect: bool, 
            lastTimeCorrect: datetime.datetime, 
            dueDate: datetime.datetime, 
            easeFactor: float
        ) -> bool:
        """Updates entry with the user's results (were they correct in answering or not)"""
        raise NotImplementedError