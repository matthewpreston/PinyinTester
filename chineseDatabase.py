# chineseDatabase.py - interacts with DB

import sys

from chineseClasses import HSK_LEVEL
from database import *

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
from PyQt6.QtSql import QSqlQuery

USAGE = f"python {sys.argv[0]} <dbFile.db> <vocab1.txt> <data1.tsv> [<vocab2.txt> <data2.tsv>]..."

class ChineseData(Data):
    def __init__(self,
                 simplified: str, 
                 traditional: str,
                 pinyin: str, 
                 english: str, 
                 classifier: str, 
                 taiwanPinyin: str, 
                 wordsWithSamePinyin: str) -> None:
        super().__init__()
        self.simplified = simplified
        self.traditional = traditional
        self.pinyin = pinyin
        self.english = english
        self.classifier = classifier
        self.taiwanPinyin = taiwanPinyin
        self.wordsWithSamePinyin = wordsWithSamePinyin

    @classmethod
    def fromDelimitedString(cls, data: str, separator: str='\t'):
        """Create a ChineseData object given a delimited string"""
        entry = data.split(separator)
        if len(entry) < 7:
            raise IndexError("Not enough data")
        return cls(
            entry[0].strip(),
            entry[1].strip(),
            entry[2].strip(),
            entry[3].strip(),
            entry[4].strip(),
            entry[5].strip(),
            entry[6].strip()
        )

class ChineseDataWithStats(ChineseData):
    def __init__(self,
                 id: int,
                 simplified: str,
                 traditional: str,
                 pinyin: str,
                 english: str,
                 classifier: str,
                 taiwanPinyin: str,
                 wordsWithSamePinyin: str,
                 timesSeen: int,
                 timesCorrect: int,
                 lastTimeSeen: str,
                 lastTimeCorrect: str,
                 dueDate: str,
                 easeFactor: float) -> None:
        super().__init__(simplified, traditional, pinyin, english, classifier, taiwanPinyin, wordsWithSamePinyin)
        self.id = id
        self.timesSeen = timesSeen
        self.timesCorrect = timesCorrect
        self.lastTimeSeen = lastTimeSeen
        self.lastTimeCorrect = lastTimeCorrect
        self.dueDate = dueDate
        self.easeFactor = easeFactor

class ChineseDB(Database):
    bands = {
        HSK_LEVEL.HSK_1: "hsk1",
        HSK_LEVEL.HSK_2: "hsk2",
        HSK_LEVEL.HSK_3: "hsk3",
        HSK_LEVEL.HSK_4: "hsk4",
        HSK_LEVEL.HSK_5: "hsk5",
        HSK_LEVEL.HSK_6: "hsk6",
        HSK_LEVEL.HSK_7_9: "hsk7-9"
    }

    def __init__(self, dbName: str) -> None:
        super().__init__(dbName)

    def deletePhrase(self, id: int) -> bool:
        """Deletes given phrase via ID"""
        return self._execQueryNoResults(
            query="""
            UPDATE chinesePhrases
            SET
                deleted = 1
            WHERE
                id = :_id;
            """,
            _id=id
        )

    def getResponseTimeAverage(self) -> float:
        """Returns the average response time"""
        result = self._execQueryGetResult(
            query="""
            SELECT
                AVG(responseTime)
            FROM
                responseTimes;
            """
        )
        if result == "": # Empty table
            return float("NaN")
        else:
            return float(result)
    
    def getResponseTimeCount(self) -> int:
        """Returns the number of response times"""
        return int(self._execQueryGetResult(
            query="""
            SELECT
                COUNT(1)
            FROM
                responseTimes;
            """
        ))

    def getResponseTimeVariance(self) -> float:
        """Returns the variance in response times"""
        result = self._execQueryGetResult(
            query="""
            SELECT
                AVG((responseTimes.responseTime - temp.avg) * (responseTimes.responseTime - temp.avg))
            FROM
                responseTimes,
            (
                SELECT
                    AVG(responseTime)
                AS
                    avg
                FROM
                    responseTimes
            )
                AS
                    temp
            ;
            """
        )
        if result == "": # Empty table
            return float("NaN")
        else:
            return float(result)

    def getPhrasesWithSameLogographs(self, simplified: str, originalID: int) -> list[ChineseDataWithStats]:
        """
        Returns a list of phrases that have the same string of Chinese characters,
        but exclude the original
        Ex. 吧 has 3 phrases: ba5, ba1, bia1, perhaps with ID's 0, 1, and 2 resp.
        getPhrasesWithSameLogographs(吧, 0) returns [(1, 吧 data...), (2, 吧 data...)]
        """
        return self._execQueryGetResults(
            query="""
            SELECT
                id,
                simplified,
                traditional,
                pinyin,
                english,
                classifier,
                taiwanPinyin,
                wordsWithSamePinyin,
                timesSeen,
                timesCorrect,
                lastTimeSeen,
                lastTimeCorrect,
                dueDate,
                easeFactor
            FROM
                chinesePhrases
            WHERE
                simplified = :_simplified AND
                id != :_originalID AND
                deleted = 0;
            """,
            constructor=lambda r: ChineseDataWithStats(
                r.value(0), # id
                r.value(1), # simplified
                r.value(2), # traditional
                r.value(3), # pinyin
                r.value(4), # english
                r.value(5), # classifier
                r.value(6), # taiwanPinyin
                r.value(7), # wordsWithSamePinyin
                r.value(8), # timesSeen
                r.value(9), # timesCorrect
                r.value(10),# lastTimeSeen
                r.value(11),# lastTimeCorrect
                r.value(12),# dueDate
                r.value(13) # easeFactor
            ),
            _simplified=simplified,
            _originalID=originalID
        )

    def getPhrasesWithSamePinyin(self, pinyin: str, originalID: int) -> list[ChineseDataWithStats]:
        """
        Returns a list of phrases that have the same pinyin but exclude the original
        Ex. tā has 3 phrases: 它, 踏, 塌 perhaps with ID's 0, 1, and 2 resp.
        getPhrasesWithSamePinyin(<span class="tone1">tā</span>, 0) returns [(1, 踏 data...), (2, 塌 data...)]
        """
        return self._execQueryGetResults(
            query="""
            SELECT
                id,
                simplified,
                traditional,
                pinyin,
                english,
                classifier,
                taiwanPinyin,
                wordsWithSamePinyin,
                timesSeen,
                timesCorrect,
                lastTimeSeen,
                lastTimeCorrect,
                dueDate,
                easeFactor
            FROM
                chinesePhrases
            WHERE
                pinyin = :_pinyin AND
                id != :_originalID AND
                deleted = 0;
            """,
            constructor=lambda r: ChineseDataWithStats(
                r.value(0), # id
                r.value(1), # simplified
                r.value(2), # traditional
                r.value(3), # pinyin
                r.value(4), # english
                r.value(5), # classifier
                r.value(6), # taiwanPinyin
                r.value(7), # wordsWithSamePinyin
                r.value(8), # timesSeen
                r.value(9), # timesCorrect
                r.value(10),# lastTimeSeen
                r.value(11),# lastTimeCorrect
                r.value(12),# dueDate
                r.value(13) # easeFactor
            ),
            _pinyin=pinyin,
            _originalID=originalID
        )

    def getPhrases(self, level: HSK_LEVEL, maxOrdinalID: int) -> list[ChineseDataWithStats]:
        """Gets a list of phrase data given a particular level and an upper bound in that level"""
        return self._execQueryGetResults(
            query="""
            SELECT
                id,
                simplified,
                traditional,
                pinyin,
                english,
                classifier,
                taiwanPinyin,
                wordsWithSamePinyin,
                timesSeen,
                timesCorrect,
                lastTimeSeen,
                lastTimeCorrect,
                dueDate,
                easeFactor
            FROM
                chinesePhrases
            WHERE
                band = :_band AND
                ordinalID <= :_maxOrdinalID AND
                deleted = 0;
            """,
            constructor=lambda r: ChineseDataWithStats(
                r.value(0), # id
                r.value(1), # simplified
                r.value(2), # traditional
                r.value(3), # pinyin
                r.value(4), # english
                r.value(5), # classifier
                r.value(6), # taiwanPinyin
                r.value(7), # wordsWithSamePinyin
                r.value(8), # timesSeen
                r.value(9), # timesCorrect
                r.value(10),# lastTimeSeen
                r.value(11),# lastTimeCorrect
                r.value(12),# dueDate
                r.value(13) # easeFactor
            ),
            _band=ChineseDB.bands[level],
            _maxOrdinalID=maxOrdinalID
        )

    def initializeDB(self) -> bool:
        """Creates table schemas"""
        query = QSqlQuery(self.con)
        query.exec("DROP TABLE IF EXISTS chinesePhrases;")
        result = query.exec(
            """
            CREATE TABLE chinesePhrases (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                band TEXT NOT NULL,
                ordinalID INTEGER NOT NULL,
                simplified TEXT NOT NULL,
                traditional TEXT NOT NULL DEFAULT "",
                pinyin TEXT NOT NULL,
                english TEXT NOT NULL,
                classifier TEXT NOT NULL DEFAULT "",
                taiwanPinyin TEXT NOT NULL DEFAULT "",
                wordsWithSamePinyin TEXT NOT NULL DEFAULT "",
                timesSeen INTEGER DEFAULT 0,
                timesCorrect INTEGER DEFAULT 0,
                lastTimeSeen TEXT DEFAULT NULL,
                lastTimeCorrect TEXT DEFAULT NULL,
                dueDate TEXT DEFAULT NULL,
                easeFactor REAL DEFAULT 2.5,
                deleted INTEGER DEFAULT 0
            );
            """
        )
        if result == False:
            return result
        query.exec("DROP TABLE IF EXISTS responseTimes;")
        return query.exec(
            """
            CREATE TABLE responseTimes (
                reponseID INTEGER PRIMARY KEY AUTOINCREMENT,
                chinesePhraseID INTEGER,
                timeStamp TEXT,
                responseTime REAL,
                FOREIGN KEY(chinesePhraseID) REFERENCES chinesePhrases(id)
            );
            """
        )

    def insertPhrase(self, level: HSK_LEVEL, ordinalID: int, data: ChineseData) -> bool:
        """Inserts into database a new phrase given phrase data"""
        return self._execQueryNoResults(
            query="""
            INSERT OR IGNORE INTO chinesePhrases (
                band,
                ordinalID,
                simplified,
                traditional,
                pinyin,
                english,
                classifier,
                taiwanPinyin,
                wordsWithSamePinyin
            )
            VALUES (
                :_band,
                :_ordinalID,
                :_simplified,
                :_traditional,
                :_pinyin,
                :_english,
                :_classifier,
                :_taiwanPinyin,
                :_wordsWithSamePinyin
            )
            """,
            _band=ChineseDB[level],
            _ordinalID=ordinalID,
            _simplified=data.simplified,
            _traditional=data.traditional,
            _pinyin=data.pinyin,
            _english=data.english,
            _classifier=data.classifier,
            _taiwanPinyin=data.taiwanPinyin,
            _wordsWithSamePinyin=data.wordsWithSamePinyin
        )

    def insertResponseTime(self, id: int, timeStamp: datetime.datetime, responseTime: float) -> bool:
        """Logs how long one took to answer a flashcard"""
        return self._execQueryNoResults(
            query="""
            INSERT OR IGNORE INTO responseTimes (
                chinesePhraseID,
                timeStamp,
                responseTime
            )
            VALUES (
                :_id,
                :_timeStamp,
                :_responseTime
            )
            """,
            _id=id,
            _timeStamp=ChineseDB.formatTimeToStr(timeStamp),
            _responseTime=responseTime
        )

    def updatePhrase(
            self, 
            id: int, 
            wasCorrect: bool, 
            lastTimeCorrect: datetime.datetime, 
            dueDate: datetime.datetime, 
            easeFactor: float
        ) -> bool:
        """Updates entry with the user's results (were they correct in answering or not)"""

        lastTimeCorrect = ChineseDB.formatTimeToStr(lastTimeCorrect)
        dueDate = ChineseDB.formatTimeToStr(dueDate)
        if wasCorrect:
            return self._execQueryNoResults(
                query="""
                UPDATE chinesePhrases
                SET
                    timesCorrect = timesCorrect + :_correct,
                    lastTimeSeen = :_lastTimeSeen,
                    lastTimeCorrect = :_lastTimeCorrect,
                    dueDate = :_dueDate,
                    easeFactor = :_easeFactor
                WHERE id = :_id;
                """,
                _id=id,
                _correct=int(wasCorrect),
                _lastTimeSeen=lastTimeCorrect,
                _lastTimeCorrect=lastTimeCorrect,
                _dueDate=dueDate,
                _easeFactor=easeFactor
            )
        else:
            return self._execQueryNoResults(
                query="""
                UPDATE chinesePhrases
                SET
                    timesCorrect = timesCorrect + :_correct,
                    lastTimeSeen = :_lastTimeSeen,
                    dueDate = :_dueDate,
                    easeFactor = :_easeFactor
                WHERE id = :_id;
                """,
                _id=id,
                _correct=int(wasCorrect),
                _lastTimeSeen=lastTimeCorrect,
                _dueDate=dueDate,
                _easeFactor=easeFactor
            )

def main(args: list[str]) -> None:
    if len(args) <= 3:
        sys.stderr.write("Error: invalid number of inputs\n")
        sys.stderr.write(f"{USAGE}\n")
        sys.exit(1)
    dbFile = args[1]
    vocabFiles = args[2::2]
    dataFiles = args[3::2]

    app = QApplication([])
    db = ChineseDB(dbFile)
    db.open()
    if not db.initializeDB(): # Failed to initialize
        raise
    for vocabFile, dataFile, level in zip(vocabFiles, dataFiles, HSK_LEVEL):
        vocabHandle = open(vocabFile, encoding="utf8")
        dataHandle = open(dataFile, encoding="utf8")
        dataHandle.readline() # Skip header
        data = ChineseData.fromDelimitedString(dataHandle.readline(), '\t')
        for ordinalID, vocab in enumerate(vocabHandle.readlines()):
            vocab = vocab.rstrip()
            while vocab == data.simplified:
                if not db.insertPhrase(level, ordinalID, data): # Failed to insert
                    raise
                if (l := dataHandle.readline()) == "": # EOF
                    break
                data = ChineseData.fromDelimitedString(l, '\t')
        vocabHandle.close()
        dataHandle.close()
    db.close()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)