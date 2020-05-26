import datetime
import functools
import json
import re
import warnings
import typing as tp
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence
from urllib import request

from more_itertools import peekable

ROOT = Path(__file__).resolve().parent.parent
RST = ROOT / "rst"
HELP = ROOT / "help"
CPYTHON_SRC = "https://raw.githubusercontent.com/python/cpython"


class HelpTopic(tp.NamedTuple):
    topic: str
    caption: str
    aliases: List[str] = []

    def as_json(self) -> dict:
        d: dict = {"topic": self.topic, "caption": self.caption}
        if self.aliases:
            d["aliases"] = self.aliases
        return d


class HelpFile:
    def __init__(self, rst_file: Path, description: str):
        self.rst_file = rst_file
        if rst_file.parent.name:
            self.module = "/".join((rst_file.parent.name, rst_file.stem))
        else:
            self.module = rst_file.stem
        self.output = HELP / self.module
        self.description = description
        self.topics: List[HelpTopic] = []
        self.sources: Dict[str, HelpFile] = {}
        self.toctree: List[Path] = []
        self._current_title_level: int = 0

    def as_json(self) -> list:
        if not self.description and not self.topics:
            return []
        return [self.description] + [t.as_json() for t in self.topics]  # type: ignore

    def add_topic(self, name: str) -> None:
        topic_name = ".".join((self.module, name))
        self.topics.append(HelpTopic(topic_name, name))

    def add_source(self, name: str) -> None:
        file = HelpFile(Path(""), name)
        # file.topics.append(HelpTopic(name))
        self.sources[SOURCE_PREFIX_URL + name] = file


class HelpIndex(tp.NamedTuple):
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
        help_files = {k: v.as_json() for (k, v) in self.help_files.items() if v.description}
        return {
            "package": self.package,
            "description": self.description,
            "doc_root": f"{self.doc_root.name}/",
            "help_files": help_files,
            "externals": externals,
            "help_contents": list(self.help_files.keys()),
        }

    def save(self) -> Path:
        output = self.doc_root / "hyperhelp.json"
        output.write_text(
            json.dumps(self.as_json(), indent=None, separators=(",\n", ": "))
        )
        return output


def rst2help(rst_file: Path, help_index: HelpIndex, version: str) -> HelpFile:
    module = rst_file.stem
    lines = get_doc(rst_file, version)
    # parse title
    for i, l in enumerate(lines):
        if l.startswith("====="):
            title = lines[i - 1]
            lines = lines[i + 1 :]
            break
    else:
        title = ""
    title = title.replace(":mod:", "").replace("`", "")
    date = datetime.date.today().isoformat()
    print(title)

    help_file = HelpFile(rst_file, description=title)
    help_index.help_files[help_file.module] = help_file

    header = '%hyperhelp title="{title}" date="{date}"'
    help_file.output.parent.mkdir(exist_ok=True, parents=True)
    write = functools.partial(print, file=open(help_file.output, "w"))
    write(header.format(title=title, date=date))

    for l in rst2help_body(lines, help_file):
        write(l)
    return help_file


def rst2help_body(lines: Iterable[str], help_file: HelpFile) -> Iterator[str]:
    iterator = peekable(lines)
    try:
        while True:
            help_line = parse_line(iterator, help_file)
            if help_line is not None:
                yield help_line
    except StopIteration:
        pass


TOPIC_RE = re.compile(r"^\.\. _([\w\d_-]+?):$")
LOCAL_REFERENCE_RE = re.compile(r":(?:class|data|func|meth):`~?([\w\d_]+?)`")
LOCAL_LINK_REF_RE = re.compile(r":(?:ref):`(.+?) <([\w-]+?)>`")
REFERENCE_RE = re.compile(r":(?:class|data|func|meth|mod):`~?([\w\d_\.]+?)`")
BOLD_RE = re.compile(r"\*\*?(.+?)\*\*?")
INLINE_CODE_RE = re.compile(r"``(.+?)``")
# TODO: code blocks seem to be prefixed by "::". Use that instead.
CODE_SAMPLE_RE = re.compile(r"^(   \s*)>>>")
UNDERLINE_RE = re.compile(r"^(\^+|\-+)$")
SOURCE_RE = re.compile(r"^(.* ):source:`([\w/]+\.py)`$")
BULLET_POINT_RE = re.compile(r"^#\. ")
SOURCE_PREFIX_URL = "https://github.com/python/cpython/blob/3.8/"

TAGS = [
    f".. {t}::"
    for t in [
        "attribute",
        "class",
        "classmethod",
        "attribute",
        "data",
        "function",
        "method",
    ]
]

TITLE_LEVEL = {"=": 0, "#": 0, "-": 1, "^": 2, "~": 3, "*": 1}


def parse_line(lines: peekable, help_file: HelpFile) -> Optional[str]:
    line: str = next(lines)
    if not line:
        return line

    next_line: str = lines.peek("")
    if next_line and UNDERLINE_RE.match(next_line):
        next(lines)
        lvl = TITLE_LEVEL[next_line[0]]
        help_file._current_title_level = lvl
        title = f"{'#' * lvl} {line}"
        line = title

    if line.startswith(".. index::"):
        # TODO: skip block
        return None

    if line.startswith(".. toctree::"):
        return parse_toctree(lines, help_file)

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
        line = next(lines)
        while not line or line.startswith(".. "):
            line = next(lines)
        anchor_text = line
        # this is too complicated
        next_lines = lines[:2]
        underline = "_"
        sandwich = False
        if len(next_lines) >= 1:
            underline = next_lines[0] or "_"
        if len(next_lines) >= 2:
            sandwich = next_lines[1] == anchor_text and next_lines[1] in TITLE_LEVEL
        if underline[0] not in TITLE_LEVEL and sandwich:
            anchor_text = underline
            underline = next(lines)
        elif underline[0] in TITLE_LEVEL:
            # valid underline, skip it.
            next(lines)
        lvl = TITLE_LEVEL.get(underline[0], 100)
        if lvl <= 1:
            print(f"# {anchor_text}")
        if lvl == 0:
            # TODO: handle case
            lvl = 1
        if lvl == 100:
            # anchor without heading
            start_text = anchor_text.split()[0]
            following_text = anchor_text[len(start_text) :]
            return f"*{help_file.module}.{topic}: {start_text}*{following_text}"

        help_file._current_title_level = lvl
        help_file.add_topic(topic)
        return f"{lvl * '#'} {help_file.module}.{topic}: {anchor_text}"

    match = CODE_SAMPLE_RE.match(line)
    if match:
        indent = match.group(1)
        indent_len = max(len(indent) - 3, 0)
        code_block = [" " * indent_len + "```py", line[indent_len:]]
        while True:
            line = next(lines)
            if not line or not line.startswith(indent):
                break
            code_block.append(line[indent_len:])
        code_block.append(code_block[0].strip("py"))
        code_block.append("")
        return "\n".join(code_block)

    match = SOURCE_RE.match(line)
    if match:
        source_name = match.group(2)
        help_file.add_source(source_name)
        line = match.group(1) + f"|{source_name}|"

    line = LOCAL_REFERENCE_RE.sub(rf"|:{help_file.module}.\1:\1|", line)
    line = LOCAL_LINK_REF_RE.sub(rf"|:{help_file.module}.\2: \1|", line)
    line = REFERENCE_RE.sub(r"|:library/\1:\1|", line)
    # Keep 3 chars to not break the 3 spaces indentation.
    line = BULLET_POINT_RE.sub(" - ", line)
    line = BOLD_RE.sub(r"<\1>", line)
    line = INLINE_CODE_RE.sub(r"`\1`", line)
    if line.startswith("# "):
        print(line)
    return line


def parse_toctree(lines: peekable, help_file: HelpFile) -> str:
    toc = []
    while True:
        line = next(lines)
        if line and not line.startswith("   "):
            break
        line = line.strip()
        if not line:
            continue
        if line.startswith(":"):
            continue
        if not line.endswith(".rst"):
            warnings.warn(f"weird toc line '{line}' in {help_file.rst_file}")
        file = help_file.rst_file.parent / line
        help_file.toctree.append(file)
        toc.append(f"- |{file.stem}|")

    return "\n".join(toc)


def r2h(text: Iterable[str]) -> List[str]:
    if isinstance(text, str):
        text = text.split("\n")
    res = list(rst2help_body(text, HelpFile(Path("test.rst"), "Testing")))
    if len(res) == 1:
        return res[0]  # type: ignore
    return res


def test():
    match = SOURCE_RE.match("**Source code:** :source:`Lib/pathlib.py`")
    assert match
    assert match.groups() == ("**Source code:** ", "Lib/pathlib.py")
    assert r2h("**Source code**: pathlib.py") == "<Source code>: pathlib.py"
    assert r2h(":class:`os.PathLike`") == "|:library/os.PathLike:os.PathLike|"
    assert r2h(":class:`PathLike`") == "|:test.PathLike:PathLike|"
    assert r2h(".. attribute:: returncode") == "# test.returncode: returncode"
    assert r2h(":ref:`pure paths <pure-paths>`") == "|:test.pure-paths: pure paths|"
    assert (
        r2h([".. _pure-paths:", "", "Pure paths", "----------"])
        == "# test.pure-paths: Pure paths"
    )
    assert (
        r2h([".. _distutils-build-ext-inplace:", "", "For example, say you want"])
        == "*test.distutils-build-ext-inplace: For* example, say you want"
    )


def get_doc(file: Path, version: str) -> Sequence[str]:
    local = RST / file
    if local.exists():
        return local.read_text().splitlines()

    remote_bin = request.urlopen(f"{CPYTHON_SRC}/{version}/Doc/{file}")
    remote = [b.decode("utf-8").rstrip("\n") for b in remote_bin]
    local.parent.mkdir(parents=True, exist_ok=True)
    with open(local, "w") as o:
        for l in remote:
            print(l, file=o)
    return remote


def fetch_toc(version: str) -> List[str]:
    return [
        f.strip()
        for f in get_doc(Path("contents.rst"), version)
        if f.strip().endswith(".rst")
    ]


def main():
    version = "3.8"
    print("ROOT:", ROOT.resolve())
    assert RST.is_dir()
    assert HELP.is_dir()

    test()
    help_index = HelpIndex()
    queue = {Path("contents.rst")}
    processed = set()
    while queue:
        new_help_files = [rst2help(file, help_index, version) for file in queue]
        processed |= queue
        queue = set(
            rst for hf in new_help_files for rst in hf.toctree if rst not in processed
        )
    help_index.save()


if __name__ == "__main__":
    main()
