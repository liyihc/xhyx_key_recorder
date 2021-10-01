import math
import logging
from datetime import datetime
import pathlib
from dataclasses import dataclass
from typing import List, Iterable

from sortedcontainers import SortedKeyList

from ..config import WORD_DIR

number_key = set(map(str, range(10)))
sign_key = set(',.":[]{}\\\|~!@#$%^&*()-=_+`')
select_key = {'space': 0, ';': 1, "'": 2}
alphabet_key = {chr(ord('a') + i) for i in range(26)}
for i in number_key:
    select_key[i] = int(i)


@dataclass
class Word:
    file: str
    code: str
    word: str
    top: bool = False
    priority: int = None

    @property
    def key(self):
        return self.code, not self.top, -(self.priority or 0)

    def __str__(self) -> str:
        return f"{self.code} {self.word} in {self.file}"

    @classmethod
    def specific(cls, code, name):
        return cls('', code, name)

    @classmethod
    def undefine(cls, code):
        return cls.specific(code, 'undefine')

    @classmethod
    def english(cls, code):
        return cls.specific(code, 'english')

    @classmethod
    def sign(cls, code):
        return cls.specific(code, 'sign')

    @classmethod
    def number(cls, code):
        return cls.specific(code, 'number')


def read_from_file(file_path: pathlib.Path):
    file_name = file_path.name
    with file_path.open('r', encoding='utf-8') as f:
        ret = []
        for line_number, line in enumerate(f):
            line = line.strip()
            try:
                if not line or line.startswith('#') or line.startswith('---'):
                    continue
                row = line.split('\t')
                if len(row) < 2:
                    raise ValueError()

                if '#' in row[1]:
                    top = True
                    row[1] = row[1].split('#')[0]
                else:
                    top = False

                word = Word(file_name, row[1], row[0],
                            top, float(row[2]) if len(row) > 2 else None)
                ret.append(word)
            except:
                exception = logging.getLogger('exception')
                exception.info(f"无法识别此行：{line}，位于文件{file_name}的{line_number}行")

        return ret


class CodeTable:
    def __init__(self) -> None:
        self.words: List[Word] = []
        self.codes_dict: SortedKeyList[Word] = SortedKeyList(
            key=lambda word: word.key)
        self.words_dict: SortedKeyList[Word] = SortedKeyList(
            key=lambda word: word.word)
        self.modify_time = datetime.now()

    def clear(self):
        self.words.clear()
        self.codes_dict.clear()
        self.words_dict.clear()

    def need_load(self):
        if len(self.words) == 0:
            return True
        for p in WORD_DIR.iterdir():
            if p.suffix.lower() == '.txt' and datetime.fromtimestamp(p.stat().st_mtime) > self.modify_time:
                return True
        return False

    def load_from(self):
        self.clear()

        for p in WORD_DIR.iterdir():
            if p.suffix.lower() == '.txt':
                self.words.extend(read_from_file(p))
        self.codes_dict.update(self.words)
        self.words_dict.update(self.words)
        self.modify_time = datetime.now()

    def match_exact_code(self, pattern, max_number, same: bool) -> List[Word]:
        position = self.codes_dict.bisect_key_left((pattern, False, -math.inf))
        ret = []
        while position < len(self.codes_dict):
            word: Word = self.codes_dict[position]
            if (word.code == pattern if same else word.code.startswith(pattern)):
                ret.append(word)
                if len(ret) > max_number:
                    break
            else:
                break
            position += 1
        return ret

    def convert_article(self, keys: Iterable[str]) -> Iterable[Word]:
        stack = []
        for key in keys:
            if key == 'enter' or key == 'esc':
                if stack:
                    stack.clear()
                elif key == 'enter':
                    yield Word.sign(key)
                continue
            if key in select_key:
                if stack:
                    code = ''.join(stack)
                    stack.clear()
                    yield self.select_th(code, key)
                else:
                    if key in number_key:
                        yield Word.number(key)
                    else:
                        yield Word.sign(key)
            elif key in sign_key:
                if stack:
                    yield self.select_th(''.join(stack), 'space')
                    stack.clear()
                yield Word.sign(key)
            elif key not in alphabet_key:
                continue
            elif len(stack) < 4:
                stack.append(key)
                if len(stack) == 4:
                    code = ''.join(stack)
                    words = self.match_exact_code(code, 2, False)
                    if len(words) == 1:
                        yield words[0]
                        stack.clear()
            else:
                code = ''.join(stack)
                words = self.match_exact_code(code, 1, False)
                if words:
                    yield words[0]
                    stack.clear()
                stack.append(key)

    def select_th(self, code, slt_key):
        slt_num = select_key[slt_key]
        words = self.match_exact_code(code, slt_num, False)
        if len(words) < slt_num + 1:
            return Word.undefine(code + slt_key)
        else:
            return words[slt_num]


_table: CodeTable = None


def get_table():
    global _table
    if _table is None:
        _table = CodeTable()
    if _table.need_load():
        _table.load_from()
    return _table
