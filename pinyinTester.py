# pinyinTester.py
#
# A simple program that gives a Chinese word and asks the user to write it in
# pinyin. For example:
#
# 你好 -> ni3hao3

from collections.abc import Callable
from enum import Enum
import random
import sys

from baseClasses import LABEL_SIDE, LEARNING_LEVEL
from chineseClasses import HSK_LEVEL
from chineseDatabase import ChineseDB, ChineseDataWithStats

from bs4 import BeautifulSoup
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget
)

tempDB = {
    "你好": "ni3hao3",
    "再见": "zai4jian4",
    "没关系": "mei2guan1xi5"
}

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600

class View(QMainWindow):
    """The GUI"""
    class STATE(Enum):
        NULL = 0
        SETUP = 1
        TESTING = 2
    
    checkboxLabels = {
        HSK_LEVEL.HSK_1: "HSK Band 1",
        HSK_LEVEL.HSK_2: "HSK Band 2",
        HSK_LEVEL.HSK_3: "HSK Band 3",
        HSK_LEVEL.HSK_4: "HSK Band 4",
        HSK_LEVEL.HSK_5: "HSK Band 5",
        HSK_LEVEL.HSK_6: "HSK Band 6",
        HSK_LEVEL.HSK_7_9: "HSK Bands 7-9"
    }

    def __init__(self, windowWidth: int, windowHeight: int) -> None:
        super().__init__()
    
        self.state = View.STATE.NULL
        self.setWindowTitle("Pinyin Tester")
        self.setFixedSize(windowWidth, windowHeight)

        # Construct views
        # ==== Setup view ====
        self.setupView = QWidget(self)
        self.setupLayout = QVBoxLayout()
        self.gridLayout = QGridLayout()
        self.checkboxes:    dict[HSK_LEVEL, QCheckBox]      = {}
        self.labelsStart:   dict[HSK_LEVEL, QLabel]         = {}
        self.sliders:       dict[HSK_LEVEL, QSlider]        = {}
        self.labelsEnd:     dict[HSK_LEVEL, QLabel]         = {}
        for row, level in enumerate(HSK_LEVEL):
            self.checkboxes[level] = QCheckBox(View.checkboxLabels[level])
            self.gridLayout.addWidget(self.checkboxes[level], row, 0)
            self.labelsStart[level] = QLabel()
            self.labelsStart[level].setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.labelsStart[level].setMinimumWidth(60)
            self.gridLayout.addWidget(self.labelsStart[level], row, 1)
            self.sliders[level] = QSlider(Qt.Orientation.Horizontal)
            self.sliders[level].setMinimum(1)
            self.gridLayout.addWidget(self.sliders[level], row, 2)
            self.labelsEnd[level] = QLabel()
            self.labelsEnd[level].setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.labelsEnd[level].setMinimumWidth(60)
            self.gridLayout.addWidget(self.labelsEnd[level], row, 3)
        self.setupLayout.addLayout(self.gridLayout)
        self.buttonBegin = QPushButton("Begin")
        self.buttonBegin.setMaximumWidth(100)
        self.setupLayout.addWidget(self.buttonBegin, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.setupView.setLayout(self.setupLayout)

        # ==== Testing view ====
        self.testingView = QWidget(self)
        self.testingLayout = QVBoxLayout()
        self.buttonBack = QPushButton("Back")
        self.buttonBack.setMaximumWidth(100)
        self.testingLayout.addWidget(self.buttonBack)
        self.labelChinese = QLabel()
        self.labelChinese.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.labelChinese.setFont(QFont("Arial", 60))
        self.labelChinese.setWordWrap(True)
        self.testingLayout.addWidget(self.labelChinese)
        self.labelPinyin = QLabel()
        self.labelPinyin.setMargin(int(windowHeight * 0.01))
        self.labelPinyin.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.labelPinyin.setFont(QFont("Arial", 40))
        self.testingLayout.addWidget(self.labelPinyin)
        self.labelDetails = QLabel()
        self.labelDetails.setMinimumHeight(int(windowHeight * 0.6))
        self.labelDetails.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.labelDetails.setFont(QFont("Arial", 18))
        self.labelDetails.setWordWrap(True)
        self.testingLayout.addWidget(self.labelDetails)
        self.lineEditPinyin = QLineEdit()
        self.lineEditPinyin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineEditPinyin.setFont(QFont("Arial", 40))
        self.testingLayout.addWidget(self.lineEditPinyin)
        self.testingButtonLayout = QHBoxLayout()
        self.buttonCheck = QPushButton("Check")
        self.testingButtonLayout.addWidget(self.buttonCheck)
        self.buttonNext = QPushButton("Next")
        self.testingButtonLayout.addWidget(self.buttonNext)
        self.testingLayout.addLayout(self.testingButtonLayout)
        self.testingView.setLayout(self.testingLayout)

    def clearInput(self) -> None:
        """Sets textbox to blank"""
        self.labelPinyin.setText("")

    def getAnswer(self) -> str:
        """Returns what the answer should be"""
        return self.labelPinyin.text()

    def getCheckBoxState(self, level: LEARNING_LEVEL) -> bool:
        """Returns whether a given box is checked or not"""
        return self.checkboxes[level].isChecked()

    def getInput(self) -> str:
        """Returns what the user has typed"""
        return self.lineEditPinyin.text()
    
    def getSliderValue(self, level: LEARNING_LEVEL) -> int:
        """Returns what value the specified slider is at"""
        return self.sliders[level].value()

    def loadNextQuestion(self, prompt: str, answer: str, details: str) -> None:
        """Fetches new question and sets up display"""
        self.labelChinese.setText(prompt)
        self.hideAnswer()
        self.labelPinyin.setText(answer)
        self.labelDetails.setText(details)
        self.lineEditPinyin.setText("")
    
    def loadSetupView(self) -> None:
        match self.state:
            case View.STATE.NULL: # No central widget yet
                pass
            case View.STATE.SETUP: # No point reloading view
                pass
            case View.STATE.TESTING:
                self.testingView = self.takeCentralWidget()
            case _:
                pass
        self.state = View.STATE.SETUP
        self.setCentralWidget(self.setupView)

    def loadTestingView(self) -> None:
        match self.state:
            case View.STATE.NULL: # No central widget yet
                pass
            case View.STATE.SETUP:
                self.setupView = self.takeCentralWidget()
            case View.STATE.TESTING: # No point reloading view
                pass
            case _:
                pass
        self.state = View.STATE.TESTING
        self.setCentralWidget(self.testingView)

    def hasInput(self) -> bool:
        """Return true if textbox isn't blank"""
        return (self.lineEditPinyin.text() != "")

    def hideAnswer(self) -> None:
        """Hides answer and its details"""
        self.labelPinyin.setStyleSheet("color: #00000000") # Nothing
        self.labelDetails.setStyleSheet("color: #00000000")

    def setCheckBoxState(self, level: LEARNING_LEVEL, state: bool) -> None:
        """Sets particular check box to a given state"""
        self.checkboxes[level].setChecked(state)

    def setLabel(self, labelSide: LABEL_SIDE, level: LEARNING_LEVEL, definition: str, index: int) -> None:
        """Sets particular label to 'definition\nindex'"""
        match labelSide:
            case LABEL_SIDE.START:
                self.labelsStart[level].setText(f"{definition}\n{index}")
            case LABEL_SIDE.END:
                self.labelsEnd[level].setText(f"{definition}\n{index}")
            case _:
                pass

    def setAnswerCorrect(self) -> None:
        """If answer was correct, show it in green and unhide description"""
        self.labelPinyin.setStyleSheet("color: #FF00FF00") # Green
        self.labelDetails.setStyleSheet("color: #FF000000")

    def setAnswerWrong(self) -> None:
        """If answer was incorrect, show it in red and unhide description"""
        self.labelPinyin.setStyleSheet("color: #FFFF0000") # Red
        self.labelDetails.setStyleSheet("color: #FF000000")

    def setSliderMaximum(self, level: LEARNING_LEVEL, maximum: int) -> None:
        """Set particular slider's maximum"""
        self.sliders[level].setMaximum(maximum)
    
    def setSliderPosition(self, level: LEARNING_LEVEL, position: int) -> None:
        """Set particular slider's position"""
        self.sliders[level].setSliderPosition(position)

    def unhideAnswer(self) -> None:
        """Unhides answer and its details"""
        self.labelPinyin.setStyleSheet("color: #FF000000") # Black
        self.labelDetails.setStyleSheet("color: #FF000000")


class Model():
    """The brains"""

    DIACRITIC_TO_TONE = {
        'ā': 1, 'ē': 1, 'ī': 1, 'ō': 1, 'ū': 1, 'ǖ': 1,
        'Ā': 1, 'Ē': 1, 'Ī': 1, 'Ō': 1, 'Ū': 1, 'Ǖ': 1,
        'á': 2, 'é': 2, 'í': 2, 'ó': 2, 'ú': 2, 'ǘ': 2,
        'Á': 2, 'É': 2, 'Í': 2, 'Ó': 2, 'Ú': 2, 'Ǘ': 2,
        'ǎ': 3, 'ě': 3, 'ǐ': 3, 'ǒ': 3, 'ǔ': 3, 'ǚ': 3,
        'Ǎ': 3, 'Ě': 3, 'Ǐ': 3, 'Ǒ': 3, 'Ǔ': 3, 'Ǚ': 3,
        'à': 4, 'è': 4, 'ì': 4, 'ò': 4, 'ù': 4, 'ǜ': 4,
        'À': 4, 'È': 4, 'Ì': 4, 'Ò': 4, 'Ù': 4, 'Ǜ': 4
    }
    TONE1_DIACRITICS_TO_VOWEL = {
        'ā':'a','ē':'e','ī':'i','ō':'o','ū':'u','ǖ':'v',
        'Ā':'A','Ē':'E','Ī':'I','Ō':'O','Ū':'U','Ǖ':'V'
    }
    TONE2_DIACRITICS_TO_VOWEL = {
        'á':'a','é':'e','í':'i','ó':'o','ú':'u','ǘ':'v',
        'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ǘ':'V'
    }
    TONE3_DIACRITICS_TO_VOWEL = {
        'ǎ':'a','ě':'e','ǐ':'i','ǒ':'o','ǔ':'u','ǚ':'v',
        'Ǎ':'A','Ě':'E','Ǐ':'I','Ǒ':'O','Ǔ':'U','Ǚ':'V'
    }
    TONE4_DIACRITICS_TO_VOWEL = {
        'à':'a','è':'e','ì':'i','ò':'o','ù':'u','ǜ':'v',
        'À':'A','È':'E','Ì':'I','Ò':'O','Ù':'U','Ǜ':'V'
    }

    class AnswerState(Enum):
        CORRECT=0
        WRONG=1
        HOMONYM=2

    def __init__(self, vocabularyFiles: list[str], databaseFile: str) -> None:
        self.vocabularies = self._getChineseVocabularies(vocabularyFiles)
        self.maximums = self._getMaximums()
        self.chineseDB = ChineseDB(databaseFile)
        self.chineseDB.open()
        self.currentPhrase: ChineseDataWithStats = None
        self.phrasesWithSameLogographs: list[ChineseDataWithStats] = None

    def _getChineseVocabularies(self, chineseVocabularyFiles: list[str]) -> dict[HSK_LEVEL, list[str]]:
        """Reads a list of files and harvests the first column"""
        results = {}
        for f, level in zip(chineseVocabularyFiles, HSK_LEVEL):
            result = []
            handle = open(f, encoding="utf8")
            for l in handle.readlines():
                # Get first column string, remove trailing '\n'
                result.append(l.split('\t', 1)[0][:-1])
            handle.close()
            results[level] = result
        return results
    
    def _getMaximums(self) -> dict[HSK_LEVEL, int]:
        """Returns a dict showing how much vocab in is each level"""
        return {level: len(self.vocabularies[level]) for level in HSK_LEVEL}

    def _getPhrasesWithSameLogographs(self, logograph: str, originalID: int) -> list[ChineseDataWithStats]:
        """Returns list of phrases with the same logograph but not with the same original ID"""
        return self.chineseDB.getPhrasesWithSameLogographs(logograph, originalID)

    @staticmethod
    def convertDiacriticToNumber(pinyin: str) -> str:
        """Given a character in pinyin with an accent, change it to the numbered form"""
        result = ""
        i = 0
        while i < len(pinyin):
            tone = Model.DIACRITIC_TO_TONE.get(pinyin[i])
            if tone is None:
                result += pinyin[i]
                i += 1
                continue
            match tone:
                case 1:
                    result += Model.TONE1_DIACRITICS_TO_VOWEL[pinyin[i]]
                case 2:
                    result += Model.TONE2_DIACRITICS_TO_VOWEL[pinyin[i]]
                case 3:
                    result += Model.TONE3_DIACRITICS_TO_VOWEL[pinyin[i]]
                case 4:
                    result += Model.TONE4_DIACRITICS_TO_VOWEL[pinyin[i]]
                case _:
                    pass
            result += pinyin[i+1:]
            break
        if tone is None:
            tone = 5
        return f"{result}{tone}"

    @staticmethod
    def getPinyinBetweenTags(markup: str) -> str:
        """Gets pinyin content between markup language tags"""
        formattedAnswer = ""
        for s in BeautifulSoup(markup, features="html.parser").find_all("span"):
            formattedAnswer += Model.convertDiacriticToNumber(s.string)
        return formattedAnswer

    @staticmethod
    def getPromptFromData(data: ChineseDataWithStats) -> str:
        """Returns a prompt string for the flashcard from the class"""
        if data.traditional != "":
            return f"{data.simplified}|{data.traditional}"
        else:
            return f"{data.simplified}"
        
    @staticmethod
    def getAnswerFromData(data: ChineseDataWithStats) -> str:
        """Returns an answer string for the flashcard from the class"""
        return data.pinyin
    
    @staticmethod
    def getDetailsFromData(data: ChineseDataWithStats) -> str:
        """Returns a details string for the flashcard from the class"""
        return data.english

    def checkAnswer(self, userInput: str) -> AnswerState:
        """Return true if correct pinyin for given chinese phrase"""
        # Pinyin has HTML tags so extract the element within
        i = userInput.lower().replace(' ','')
        if i == Model.getPinyinBetweenTags(self.currentPhrase.pinyin).lower():
            return Model.AnswerState.CORRECT
        # Check against homonyms
        for p in self.phrasesWithSameLogographs:
            if i == Model.getPinyinBetweenTags(p.pinyin).lower():
                return Model.AnswerState.HOMONYM
        return Model.AnswerState.WRONG

    def close(self) -> None:
        self.chineseDB.close()

    def getFirstPhraseInLevel(self, level: LEARNING_LEVEL) -> tuple[str, int]:
        """Returns the first phrase in a level and its index"""
        return (self.vocabularies[level][0], 1)

    def getLastPhraseInLevel(self, level: LEARNING_LEVEL) -> tuple[str, int]:
        """Returns the last phrase in a level and its index"""
        return (self.vocabularies[level][-1], self.maximums[level])

    def getPhraseInLevel(self, level: LEARNING_LEVEL, index: int) -> str:
        """Returns specified phrase"""
        return self.vocabularies[level][index]

    def getRandomPhraseInLevel(self, level: LEARNING_LEVEL, maximumBound: int) -> ChineseDataWithStats:
        """Returns a random phrase in (chinese, pinyin, details)"""
        self.currentPhrase = random.choice(self.chineseDB.getPhrases(level, maximumBound))
        self.phrasesWithSameLogographs = self._getPhrasesWithSameLogographs(
            self.currentPhrase.simplified,
            self.currentPhrase.id)
        return self.currentPhrase

class Controller():
    """Links view to model"""

    def __init__(self, model: Model, view: View, learningLevels: LEARNING_LEVEL) -> None:
        self.model = model
        self.view  = view
        self.learningLevels = learningLevels
        self.activeLearningLevels = [l for l in learningLevels]
        self.hasChecked = False

        self.initializeSetupView()
        self.connectSignalAndSlots()
        self.view.loadSetupView()
    
    def backToSetup(self) -> None:
        """Return to setup view"""
        self.view.loadSetupView()

    def beginTesting(self) -> None:
        if len(self.activeLearningLevels) == 0: # All were checked off
            messageBox = QMessageBox()
            messageBox.setWindowTitle("Error")
            messageBox.setText("Please select at least one level")
            messageBox.exec()
            return
        self.loadNextQuestion()
        self.view.loadTestingView()

    def checkAnswer(self) -> None:
        """Checks inputted pinyin versus true answer"""
        if (not self.view.hasInput()): # Accidental click
            return
        if self.hasChecked: # User already checked or hit Next, no point checking
            return
        self.hasChecked = True
        match self.model.checkAnswer(self.view.getInput()):
            case Model.AnswerState.CORRECT:
                self.view.setAnswerCorrect()
            case Model.AnswerState.WRONG:
                self.view.setAnswerWrong()
            case Model.AnswerState.HOMONYM:
                self.view.unhideAnswer()
            case _:
                pass

    def connectSignalAndSlots(self) -> None:
        """Hooks up model to view"""
        # Setup view
        for level in self.learningLevels:
            self.view.checkboxes[level].clicked.connect(
                self.manageLearningLevels(level)
            )
            self.view.sliders[level].valueChanged.connect(
                self.updateLabel(LABEL_SIDE.END, level)
            )
        self.view.buttonBegin.clicked.connect(self.beginTesting)

        # Testing view
        self.view.buttonBack.clicked.connect(self.backToSetup)
        self.view.buttonCheck.clicked.connect(self.checkAnswer)
        self.view.lineEditPinyin.returnPressed.connect(self.returnPressed)
        self.view.buttonNext.clicked.connect(self.nextQuestion)

    def initializeSetupView(self) -> None:
        """In the View's setup view, give the first and last phrases"""
        for level in self.learningLevels:
            self.view.setCheckBoxState(level, True)
            firstPhrase, firstIndex = self.model.getFirstPhraseInLevel(level)
            self.view.setLabel(LABEL_SIDE.START, level, firstPhrase, firstIndex)
            lastPhrase, lastIndex = self.model.getLastPhraseInLevel(level)
            self.view.setSliderMaximum(level, lastIndex)
            self.view.setSliderPosition(level, lastIndex)
            self.view.setLabel(LABEL_SIDE.END, level, lastPhrase, lastIndex)

    def loadNextQuestion(self) -> None:
        """Fetches next question and loads it to view"""
        level = random.choice(self.activeLearningLevels)
        data = self.model.getRandomPhraseInLevel(level, self.view.getSliderValue(level)-1)
        prompt = Model.getPromptFromData(data)
        answer = Model.getAnswerFromData(data)
        details = Model.getDetailsFromData(data)
        self.view.loadNextQuestion(prompt, answer, details)

    def manageLearningLevels(self, level: LEARNING_LEVEL) -> Callable[[], None]:
        """
        Ensure that there are no gaps in learning levels, i.e. if level 4 is
        checked, levels 1-3 are checked and levels 5+ are unchecked"""
        def dummy() -> None:
            if self.view.getCheckBoxState(level): # If newly checked
                # Check all lower level check boxes
                self.activeLearningLevels = []
                for l in self.learningLevels:
                    if l == level: # Found the ceiling
                        self.activeLearningLevels.append(l)
                        break
                    self.activeLearningLevels.append(l)
                    self.view.setCheckBoxState(l, True)
            else: # If newly unchecked
                # Uncheck all higher level check boxes
                self.activeLearningLevels = []
                found = False
                for l in self.learningLevels:
                    if not found:
                        if l == level:
                            found = True
                            continue
                        self.activeLearningLevels.append(l)
                        continue
                    self.view.setCheckBoxState(l, False)
        return dummy

    def nextQuestion(self) -> None:
        """
        If the user has checked their answer, allow them to go to the next question.
        If the user hasn't checked their answer but wants to go to the next
        question anyways, flash the answer and have the user press the Next
        button again.
        """
        if self.hasChecked:
            self.loadNextQuestion()
            self.hasChecked = False
        else:
            self.view.unhideAnswer()
            self.hasChecked = True

    def returnPressed(self) -> None:
        """
        Special functionality for Enter button. Either check pinyin or go to
        next question.
        """
        if self.hasChecked:
            self.nextQuestion()
        else:
            if self.view.hasInput(): # User has typed something, wants to check
                self.checkAnswer()
            else: # User has typed nothing but wants to see the answer
                self.view.unhideAnswer()
                self.hasChecked = True
    
    def updateLabel(self, labelSide: LABEL_SIDE, learningLevel: LEARNING_LEVEL) -> Callable[[], None]:
        """When the slider was moved, changed what value the label shows"""
        def dummy() -> None:
            value = self.view.getSliderValue(learningLevel)
            self.view.setLabel(
                labelSide, 
                learningLevel, 
                self.model.getPhraseInLevel(learningLevel, value-1), 
                value
            )
        return dummy

def main(argv: list[str]) -> None:
    app = QApplication([])
    app.setStyleSheet("") # TODO
    view = View(WINDOW_WIDTH, WINDOW_HEIGHT)
    model = Model(argv[2:], argv[1])
    controller = Controller(model, view, HSK_LEVEL)
    view.show()
    result = app.exec()
    model.close()
    sys.exit(result)

if __name__ == "__main__":
    main(sys.argv)