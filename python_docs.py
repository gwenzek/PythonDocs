import sublime
import sublime_plugin
import hyperhelpcore as hh

import re


def log(*args):
    print("[PythonDocs]", *args)


def plugin_loaded():
    hh.initialize()


class PythonDocsOpen(sublime_plugin.TextCommand):
    pkg = "PythonDocs"
    pkg_info = None

    def run(self, _: None, topic: str = None):
        if self.pkg_info is None:
            self.pkg_info = hh.core.load_help_index(
                "Packages/%s/help/hyperhelp.json" % self.pkg
            )
            log(self.pkg_info)
        if self.pkg_info is None:
            log("PythonDocs hasn't been correctly loaded by HyperHelp")
            return

        topic = topic or self.get_topic()
        topic_exists = hh.core.lookup_help_topic(self.pkg_info, topic)
        if topic_exists:
            return sublime.run_command(
                "hyperhelp_topic", {"package": self.pkg, "topic": topic}
            )

        sublime.run_command("hyperhelp_index", {"package": self.pkg})
        self.view.window().run_command("insert", {"characters": topic})

    def get_topic(self) -> str:
        """Uses the word under the cursor as topic.

        Extends the word to the left if possible:
            pathlib.Pa|th -> pathlib.Path
            path|lib.Path -> pathlib
            (foo / "readme.txt").exp|anduser -> expanduser
        """
        view = self.view
        selection = view.sel()[0]
        extend = selection.empty()
        selection = view.word(selection)
        while extend and view.substr(selection.begin() - 1) == ".":
            extended = selection.cover(view.word(selection.begin() - 2))
            if not re.match(r"^\w[\w\d_]+\.", self.view.substr(extended)):
                break
            selection = extended

        topic = self.view.substr(selection)
        return topic


# For testing
# pathlib.Path
# pathlib.Path("~/foo").expanduser()
# pathlib.Path.expanduser
