"""CLI application to translate messages between Braille and English.

--------------------------------------------------------------------------------
IMPORTANT
--------------------------------------------------------------------------------
I've created a companion repo to store my additional test cases
and documentation. This way, I don't accidentally break the
automated validation by modifying other files in this repo.

You can find the companion repo here:
https://github.com/callumcurtis/shopify-intern-challenge-harness
--------------------------------------------------------------------------------

This application makes some assumptions (since the starter repo did not completely
specify expected behavior in all cases).

- A message is considered to be in Braille if it consists of only 'O' and '.'
  characters.
- If a message is not considered Braille then it is considered English.
- If a message is considered Braille but is not otherwise syntactically correct
  (e.g., its length is not evenly divisibly by 6), then this application will exit
  with an exception.
- If a message is considered English but contains periods then it is considered
  syntactically incorrect and the application will exit with an exception.
- The message is expected to fit in memory.
- Multiple consecutive spaces are combined into a single space in the **input**
  to maintain consistency between usage with quoted and unquoted arguments.
- Trailing and leading spaces are stripped in the **output** as spaces are
  intended only as separators between words.
"""

from __future__ import annotations

import typing
import enum


BRAILLE_ALPHABET = {"O", "."}
ENGLISH_ALPHABET = {*(
    [chr(i) for i in range(ord("a"), ord("z") + 1)]
    + [chr(i) for i in range(ord("A"), ord("Z") + 1)]
    + [chr(i) for i in range(ord("0"), ord("9") + 1)]
    + [" "]
)}
BRAILLE_CELL_SIZE = 6
BRAILLE_TO_ENGLISH_CAPITALIZED: dict[str, str] = dict([
    # uppercase letters
    ("O.....", "A"),
    ("O.O...", "B"),
    ("OO....", "C"),
    ("OO.O..", "D"),
    ("O..O..", "E"),
    ("OOO...", "F"),
    ("OOOO..", "G"),
    ("O.OO..", "H"),
    (".OO...", "I"),
    (".OOO..", "J"),
    ("O...O.", "K"),
    ("O.O.O.", "L"),
    ("OO..O.", "M"),
    ("OO.OO.", "N"),
    ("O..OO.", "O"),
    ("OOO.O.", "P"),
    ("OOOOO.", "Q"),
    ("O.OOO.", "R"),
    (".OO.O.", "S"),
    (".OOOO.", "T"),
    ("O...OO", "U"),
    ("O.O.OO", "V"),
    (".OOO.O", "W"),
    ("OO..OO", "X"),
    ("OO.OOO", "Y"),
    ("O..OOO", "Z"),
])
BRAILLE_SPACE = "......"
BRAILLE_TO_ENGLISH_CHARACTER: dict[str, str] = dict([
    # lowercase letters
    ("O.....", "a"),
    ("O.O...", "b"),
    ("OO....", "c"),
    ("OO.O..", "d"),
    ("O..O..", "e"),
    ("OOO...", "f"),
    ("OOOO..", "g"),
    ("O.OO..", "h"),
    (".OO...", "i"),
    (".OOO..", "j"),
    ("O...O.", "k"),
    ("O.O.O.", "l"),
    ("OO..O.", "m"),
    ("OO.OO.", "n"),
    ("O..OO.", "o"),
    ("OOO.O.", "p"),
    ("OOOOO.", "q"),
    ("O.OOO.", "r"),
    (".OO.O.", "s"),
    (".OOOO.", "t"),
    ("O...OO", "u"),
    ("O.O.OO", "v"),
    (".OOO.O", "w"),
    ("OO..OO", "x"),
    ("OO.OOO", "y"),
    ("O..OOO", "z"),
    # space
    (BRAILLE_SPACE, " "),
])
BRAILLE_TO_ENGLISH_NUMBER: dict[str, str] = dict([
    # numbers
    (".OOO..", "0"),
    ("O.....", "1"),
    ("O.O...", "2"),
    ("OO....", "3"),
    ("OO.O..", "4"),
    ("O..O..", "5"),
    ("OOO...", "6"),
    ("OOOO..", "7"),
    ("O.OO..", "8"),
    (".OO...", "9"),
])
BRAILLE_UPPERCASE_MODIFIER = ".....O"
BRAILLE_NUMBER_MODE_MODIFIER = ".O.OOO"
BRAILLE_NUMBER_MODE_TERMINAL = BRAILLE_SPACE


def chunk(s: str, chunk_size: int) -> typing.Iterator[str]:
    return (s[i:i + chunk_size] for i in range(0, len(s), chunk_size))


class Language(enum.Enum):
    BRAILLE = "braille"
    ENGLISH = "english"


class CliMessageParser:

    def __init__(
        self,
        *,
        separator: str = " ",
        split_compound_args: bool = True,
    ):
        """
        Optional keyword arguments:
            separator: the character(s) to place between tokens in the output message.
            split_compound_args: whether to split quoted arguments containing multiple tokens.
        """
        self.separator = separator
        self.split_compound_args = split_compound_args

    def parse(self, args: list[str] | None = None):
        """Returns the message formed by the given cli arguments.

        The first argument is assumed to be the name of the script and
        is excluded from the message.

        Arguments:
            args: list of cli arguments
        """
        if not args:
            import sys
            args = sys.argv
        if self.split_compound_args:
            args = [
                arg
                for compound in args
                for arg in compound.split()
            ]
        return self.separator.join(args[1:])


class LanguageDiscriminator:

    def __init__(
        self,
        *,
        braille_alphabet: set[str] = BRAILLE_ALPHABET,
        english_alphabet: set[str] = ENGLISH_ALPHABET,
    ):
        self._braille_alphabet = braille_alphabet
        self._english_alphabet = english_alphabet

    def determine(self, message: str) -> Language:
        is_english = is_braille = True
        for character in message:
            is_braille &= character in self._braille_alphabet
            is_english &= character in self._english_alphabet
            if not (is_braille or is_english):
                raise ValueError("the provided message is neither english nor braille")
        if is_braille:
            # braille takes priority over english
            return Language.BRAILLE
        return Language.ENGLISH


class BrailleToEnglishTranslator:

    class _Mode(enum.Enum):
        CAPITALIZE = "capitalize"
        NUMBER = "number"

    def __init__(
        self,
        *,
        braille_cell_size: int = BRAILLE_CELL_SIZE,
        braille_to_english_character: dict[str, str] = BRAILLE_TO_ENGLISH_CHARACTER,
        braille_to_english_capitalized: dict[str, str] = BRAILLE_TO_ENGLISH_CAPITALIZED,
        braille_to_english_number: dict[str, str] = BRAILLE_TO_ENGLISH_NUMBER,
        braille_uppercase_modifer: str = BRAILLE_UPPERCASE_MODIFIER,
        braille_number_mode_modifier: str = BRAILLE_NUMBER_MODE_MODIFIER,
        braille_number_mode_terminal: str = BRAILLE_NUMBER_MODE_TERMINAL,
    ):
        self._braille_cell_size = braille_cell_size
        self._braille_to_english_character = braille_to_english_character
        self._braille_to_english_capitalized = braille_to_english_capitalized
        self._braille_to_english_number = braille_to_english_number
        self._braille_uppercase_modifier = braille_uppercase_modifer
        self._braille_number_mode_modifier = braille_number_mode_modifier
        self._braille_number_mode_terminal = braille_number_mode_terminal

    def translate(self, message: str) -> str:
        if len(message) % self._braille_cell_size != 0:
            raise ValueError("the message size is not divisible by the braille cell size")

        mode: BrailleToEnglishTranslator._Mode | None = None
        translated: list[str] = []
        for cell in chunk(message, self._braille_cell_size):
            if cell == self._braille_uppercase_modifier:
                mode = self._Mode.CAPITALIZE
            elif cell == self._braille_number_mode_modifier:
                mode = self._Mode.NUMBER
            elif cell == self._braille_number_mode_terminal:
                translated.append(self._braille_to_english_character[cell])
                mode = None
            elif mode == self._Mode.CAPITALIZE:
                translated.append(self._braille_to_english_capitalized[cell])
                mode = None
            elif mode == self._Mode.NUMBER:
                translated.append(self._braille_to_english_number[cell])
            else:
                translated.append(self._braille_to_english_character[cell])

        return "".join(translated)


if __name__ == "__main__":
    original_message = CliMessageParser().parse()
    original_language = LanguageDiscriminator().determine(original_message)
    if original_language == Language.BRAILLE:
        translator = BrailleToEnglishTranslator()
    else:
        raise NotImplementedError("only braille is implemented")
    translated_message = translator.translate(original_message)
    print(translated_message)

