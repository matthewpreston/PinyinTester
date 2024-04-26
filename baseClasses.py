from enum import Enum

class LABEL_SIDE(Enum):
    START = 0
    END = 1

# Future proofing for other languages
class LEARNING_LEVEL(Enum):
    pass

class ANSWER_STATE(Enum):
    CORRECT=0
    WRONG=1
    HOMONYM=2

class QUALITY(Enum):
    """Qualities used for SuperMemo 2 (SM-2) algorithm"""
    FIVE = 5    # Perfect response
    FOUR = 4    # Correct response after hesitation
    THREE = 3   # Correct response but with serious difficulty
    TWO = 2     # Incorrect response with a quick response
    ONE = 1     # Incorrect response that matches a different answer
    ZERO = 0    # Incorrect response with no recollection