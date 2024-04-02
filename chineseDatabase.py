# chineseDatabase.py - interacts with DB

import datetime
import sys

from chineseClasses import HSK_LEVEL

from PyQt6.QtWidgets import QApplication
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

USAGE = f"python {sys.argv[0]} <dbFile.db> <vocab1.txt> <data1.tsv> [<vocab2.txt> <data2.tsv>]..."

class Data:
    def __init__(self) -> None:
        pass

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

def parse(data: str, separator: str='\t') -> ChineseData:
        """Create a ChineseData object given a delimited string"""
        entry = data.split(separator)
        if len(entry) < 7:
            raise IndexError("Not enough data")
        return ChineseData(
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
                 lastTimeCorrect: str) -> None:
        super().__init__(simplified, traditional, pinyin, english, classifier, taiwanPinyin, wordsWithSamePinyin)
        self.id = id
        self.timesSeen = timesSeen
        self.timesCorrect = timesCorrect
        self.lastTimeSeen = lastTimeSeen
        self.lastTimeCorrect = lastTimeCorrect

class ChineseDB:
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
        self.db = dbName
        self.con = QSqlDatabase.addDatabase("QSQLITE")
        self.con.setDatabaseName(self.db)

    def _execQuery(self, query: str, **kwargs: str) -> list[ChineseDataWithStats]:
        """Executes query with given keyword arguments"""
        _query = QSqlQuery(self.con)
        r = _query.prepare(query)
        for key, value in kwargs.items():
            _query.bindValue(f":{key}", value)
        _query.exec()
        results = []
        while _query.next():
            r = ChineseDataWithStats(
                _query.value(0), # id
                _query.value(1), # simplified
                _query.value(2), # traditional
                _query.value(3), # pinyin
                _query.value(4), # english
                _query.value(5), # classifier
                _query.value(6), # taiwanPinyin
                _query.value(7), # wordsWithSamePinyin
                _query.value(8), # timesSeen
                _query.value(9), # timesCorrect
                _query.value(10),# lastTimeSeen
                _query.value(11) # lastTimeCorrect
            )
            results.append(r)
        _query.finish()
        return results

    def _insertPhrase(self, 
                      band: str,
                      ordinalID: int,
                      simplified: str,
                      traditional: str,
                      pinyin: str,
                      english: str,
                      classifier: str,
                      taiwanPinyin: str,
                      wordsWithSamePinyin: str,
                      timesSeen: int = 0,
                      timesCorrect: int = 0,
                      lastTimeSeen: str = "",
                      lastTimeCorrect: str = "") -> bool:
        """Inserts into database a new phrase given phrase data"""
        query = QSqlQuery(self.con)
        query.prepare(
            """
            INSERT OR IGNORE INTO chinesePhrases (
                band,
                ordinalID,
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
                lastTimeCorrect
            )
            VALUES (
                :band,
                :ordinalID,
                :simplified,
                :traditional,
                :pinyin,
                :english,
                :classifier,
                :taiwanPinyin,
                :wordsWithSamePinyin,
                :timesSeen,
                :timesCorrect,
                :lastTimeSeen,
                :lastTimeCorrect
            )
            """
        )
        query.bindValue(":band", band)
        query.bindValue(":ordinalID", ordinalID)
        query.bindValue(":simplified", simplified)
        query.bindValue(":traditional", traditional)
        query.bindValue(":pinyin", pinyin)
        query.bindValue(":english", english)
        query.bindValue(":classifier", classifier)
        query.bindValue(":taiwanPinyin", taiwanPinyin)
        query.bindValue(":wordsWithSamePinyin", wordsWithSamePinyin)
        query.bindValue(":timesSeen", timesSeen)
        query.bindValue(":timesCorrect", timesCorrect)
        query.bindValue(":lastTimeSeen", lastTimeSeen)
        query.bindValue(":lastTimeCorrect", lastTimeCorrect)
        return query.exec()

    def close(self) -> None:
        """Close database connection"""
        self.con.close()

    def deletePhrase(self, id: int) -> bool:
        """Deletes given phrase via ID"""
        query = QSqlQuery(self.con)
        query.prepare(
            """
            UPDATE chinesePhrases
            SET
                deleted = 1
            WHERE
                id = :id;
            """
        )
        query.bindValue(":id", id)
        return query.exec()

    def getPhrasesWithSameLogographs(self, simplified: str, originalID: int) -> list[ChineseDataWithStats]:
        """
        Returns a list of phrases that have the same string of Chinese characters,
        but exclude the original
        Ex. 吧 has 3 phrases: ba5, ba1, bia1, perhaps with ID's 0, 1, and 2 resp.
        getPhrasesWithSameLogographs(吧, 0) returns [(1, 吧 data...), (2, 吧 data...)]
        """
        return self._execQuery(
            """
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
                lastTimeCorrect
            FROM
                chinesePhrases
            WHERE
                simplified = :_simplified AND
                id != :_originalID AND
                deleted = 0;
            """,
            _simplified=simplified,
            _originalID=originalID
        )

    def getPhrases(self, band: HSK_LEVEL, maxOrdinalID: int) -> list[ChineseDataWithStats]:
        """Gets a list of phrase data given a particular band and an upper bound in that band"""
        return self._execQuery(
            """
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
                lastTimeCorrect
            FROM
                chinesePhrases
            WHERE
                band = :_band AND
                ordinalID <= :_maxOrdinalID AND
                deleted = 0;
            """,
            _band=ChineseDB.bands[band],
            _maxOrdinalID=maxOrdinalID
        )

    def initializeDB(self) -> bool:
        """Creates table schemas"""
        query = QSqlQuery(self.con)
        query.exec("DROP TABLE IF EXISTS chinesePhrases;")
        return query.exec(
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
                deleted INTEGER DEFAULT 0
            );
            """
        )

    def insertPhrase(self, band: HSK_LEVEL, ordinalID: int, data: ChineseData) -> bool:
        """Inserts into database a new phrase given phrase data"""
        return self._insertPhrase(
            ChineseDB[band],
            ordinalID,
            data.simplified,
            data.traditional,
            data.pinyin,
            data.english,
            data.classifier,
            data.taiwanPinyin,
            data.wordsWithSamePinyin
        )

    def open(self) -> bool:
        """Open database connection"""
        return self.con.open()

    def updatePhrase(self, id: int, wasCorrect: bool) -> bool:
        """Updates entry with the user's results (were they correct in answering or not)"""
        now = datetime.datetime.now()
        year = f"{now.year:04}"
        month = f"{now.month:02}"
        day = f"{now.day:02}"
        hour = f"{now.hour:02}"
        minute = f"{now.minute:02}"
        second = f"{now.second:02}"
        lastTimeSeen = f"{year}-{month}-{day} {hour}:{minute}:{second}"
        
        query = QSqlQuery(self.con)
        if wasCorrect:
            query.prepare(
                """
                UPDATE chinesePhrases
                SET
                    timesCorrect = timesCorrect + :correct,
                    lastTimeSeen = :lastTimeSeen,
                    lastTimeCorrect = :lastTimeCorrect
                WHERE id = :id;
                """
            )
        else:
            query.prepare(
                """
                UPDATE chinesePhrases
                SET
                    timesCorrect = timesCorrect + :correct,
                    lastTimeSeen = :lastTimeSeen
                WHERE id = :id;
                """
            )
        query.bindValue(":id", id)
        query.bindValue(":correct", int(wasCorrect))
        query.bindValue(":lastTimeSeen", lastTimeSeen)
        if wasCorrect:
            query.bindValue(":lastTimeCorrect", lastTimeSeen)
        return query.exec()

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
        data = parse(dataHandle.readline())
        for ordinalID, vocab in enumerate(vocabHandle.readlines()):
            vocab = vocab.rstrip()
            while vocab == data.simplified:
                if not db.insertPhrase(level, ordinalID, data): # Failed to insert
                    raise
                if (l := dataHandle.readline()) == "": # EOF
                    break
                data = parse(l)
        vocabHandle.close()
        dataHandle.close()
    db.close()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)