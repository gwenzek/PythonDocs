from pathlib import Path
from typing import Dict, NamedTuple, List
import json
import functools
import datetime
import re
from typing import Optional

from more_itertools import peekable

ROOT = Path(__file__).resolve().parent.parent
RST = ROOT / "rst"
HELP = ROOT / "help"


class HelpTopic(NamedTuple):
    topic: str
    aliases: List[str] = []

    def as_json(self) -> dict:
        d: dict = {"topic": self.topic}
        if self.aliases:
            d["aliases"] = self.aliases
        return d


class HelpFile:
    def __init__(self, module: str, description: str):
        self.module = module
        self.description = description
        self.topics: List[HelpTopic] = []
        self.sources: Dict[str, HelpFile] = {}
        self._current_title_level: int = 0

    def as_json(self) -> list:
        return [self.description] + [t.as_json() for t in self.topics]  # type: ignore

    def add_topic(self, name: str) -> None:
        topic_name = ".".join((self.module, name))
        self.topics.append(HelpTopic(topic_name))

    def add_source(self, name: str) -> None:
        file = HelpFile("", name)
        file.topics.append(HelpTopic(name))
        self.sources[SOURCE_PREFIX_URL + name] = file


class HelpIndex(NamedTuple):
    package: str = "PythonDocs"
    description: str = "Browse docs.python.org inside Sublime"
    doc_root: Path = HELP
    help_files: Dict[str, HelpFile] = {}
    externals: Dict[str, HelpFile] = {}

    def as_json(self) -> dict:
        externals = {
            k: v.as_json()
            for hf in self.help_files.values()
            for k, v in hf.sources.items()
        }
        return {
            "package": self.package,
            "description": self.description,
            "doc_root": f"{self.doc_root.name}/",
            "help_files": {k: v.as_json() for (k, v) in self.help_files.items()},
            "externals": externals,
        }

    def save(self) -> Path:
        output = self.doc_root / "hyperhelp.json"
        output.write_text(json.dumps(self.as_json(), indent=2))
        return output


def rst2help(rst_file: Path, help_index: HelpIndex) -> Path:
    module = rst_file.stem
    output = HELP / module
    header = '%hyperhelp title="{title}" date="{date}"'
    write = functools.partial(print, file=open(output, "w"))

    lines = rst_file.read_text().split("\n")
    # parse title
    for i, l in enumerate(lines):
        if l.startswith("====="):
            title = lines[i - 1]
            lines = lines[i + 1 :]
            break
    title = title.replace(":mod:", "").replace("`", "")
    date = datetime.date.today().isoformat()
    print(title)
    write(header.format(title=title, date=date))

    help_file = HelpFile(module=module, description=title)
    help_index.help_files[help_file.module] = help_file
    iterator = peekable(lines)
    try:
        while True:
            help_line = _rst2help_line(iterator, help_file)
            if help_line is not None:
                write(help_line)
    except StopIteration:
        pass

    return output


TOPIC_RE = re.compile(r"^\.\. ([\w\d_-]+?):$")
LOCAL_REFERENCE_RE = re.compile(r":(?:class|meth|func):`([\w\d_]+?)`")
REFERENCE_RE = re.compile(r":(?:class|meth|func|mod):`([\w\d_\.]+?)`")
BOLD_RE = re.compile(r"\*\*?(.+?)\*\*?")
INLINE_CODE_RE = re.compile(r"``(.+?)``")
CODE_SAMPLE_RE = re.compile(r"^(   \s*)>>>")
TAGS = [".. class::", ".. classmethod::", ".. data::", ".. method::"]
UNDERLINE_RE = re.compile(r"^(\^+|\-+)$")
SOURCE_RE = re.compile(r"^(.* ):source:`([\w/]+\.py)`$")
SOURCE_PREFIX_URL = "https://github.com/python/cpython/blob/3.8/"

TITLE_LEVEL = {"=": 0, "-": 1, "^": 2}


def _rst2help_line(lines: peekable, help_file: HelpFile) -> Optional[str]:
    line: str = lines.__next__()
    if not line:
        return line

    underline: str = lines.peek("")
    if underline and UNDERLINE_RE.match(underline):
        lines.__next__()
        lvl = TITLE_LEVEL[underline[0]]
        help_file._current_title_level = lvl
        title = f"{'#' * lvl} {line}"
        line = title

    if line.startswith(".. index::"):
        # TODO: skip block
        return None

    for tag in TAGS:
        # Class/Fn definition
        if not line.startswith(tag):
            continue
        line = line[len(tag) :].strip()
        fn = line.split("(")[0].strip()
        help_file.add_topic(fn)
        lvl = help_file._current_title_level + 1
        return f"{'#' * lvl} {help_file.module}.{fn}: {line}"

    match = TOPIC_RE.match(line)
    if match:
        # .. _pure-paths:
        #
        # Pure paths
        # ----------
        topic = match.group(1)
        line = lines.__next__()
        while not line:
            line = lines.__next__()
        anchor_text = line
        underline = lines.__next__()
        lvl = TITLE_LEVEL[underline[0]]
        if lvl == 1:
            print(f"# {anchor_text}")
        help_file._current_title_level = lvl
        return f"{lvl * '#'} {help_file.module}.{topic}: {anchor_text}"

    match = CODE_SAMPLE_RE.match(line)
    if match:
        indent = match.group(1)
        indent_len = max(len(indent) - 3, 0)
        code_block = [" " * indent_len + "```", line[indent_len:]]
        while True:
            line = lines.__next__()
            if not line or not line.startswith(indent):
                break
            code_block.append(line[indent_len:])
        code_block.append(code_block[0])
        code_block.append("")
        return "\n".join(code_block)

    match = SOURCE_RE.match(line)
    if match:
        source_name = match.group(2)
        help_file.add_source(source_name)
        line = match.group(1) + f"|{source_name}|"

    line = LOCAL_REFERENCE_RE.sub(rf"|:{help_file.module}.\1:\1|", line)
    line = REFERENCE_RE.sub(r"|\1|", line)
    line = BOLD_RE.sub(r"<\1>", line)
    line = INLINE_CODE_RE.sub(r"`\1`", line)
    if line.startswith("# "):
        print(line)
    return line


def r2h(line: str) -> Optional[str]:
    return _rst2help_line(peekable([line]), HelpFile("test", "Testing"))


def test():
    match = SOURCE_RE.match("**Source code:** :source:`Lib/pathlib.py`")
    assert match
    assert match.groups() == ("**Source code:** ", "Lib/pathlib.py")
    assert r2h("**Source code**: pathlib.py") == "<Source code>: pathlib.py"


def main():
    print("ROOT:", ROOT.resolve())
    assert RST.is_dir()
    assert HELP.is_dir()

    test()
    help_index = HelpIndex()
    # for file in RST.glob("*.rst"):
    for file in [RST / "pathlib.rst"]:
        rst2help(file, help_index)
    help_index.save()


if __name__ == "__main__":
    main()
