import sublime
import sublime_plugin
import hyperhelpcore

import re


def plugin_loaded():
    hyperhelpcore.initialize()


class PythonDocsOpen(sublime_plugin.TextCommand):
    def run(self, _: None, key: str = None):
        if key is None:
            key = self.get_search_key()

        assert key, "No search term found"
        print("searching:", key)
        sublime.run_command("hyperhelp_topic", {"package": "PythonDocs", "topic": key})

    def get_search_key(self) -> str:
        view = self.view
        selection = view.sel()[0]
        if len(selection) == 0:
            selection = view.word(selection)
        # extend to the left, only capturing words
        #    pathlib.Pa|th -> pathlib.Path
        #    path|lib.Path -> pathlib
        #    (foo / "readme.txt").exp|anduser -> expanduser
        while view.substr(selection.begin() - 1) == ".":
            extended = selection.cover(view.word(selection.begin() - 2))
            if not re.match(r"^\w[\w\d_]+\.", self.view.substr(extended)):
                break
            selection = extended

        return self.view.substr(selection)


# For testing
# pathlib.Path
# pathlib.Path("~/foo").expanduser()
# pathlib.Path.expanduser
