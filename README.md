# PythonDocs

Browse [docs.python.org](https://docs.python.org) inside Sublime Text

This package leverage [HyperHelp](https://github.com/STealthy-and-haSTy/hyperhelpcore)
to show Python documentation from Sublime.
The conversion between reStructuredText (used for Python docs)
and HyperHelp format, is done using my own [Sphinx plugin](https://github.com/gwenzek/sphinx_hyperhelp).


## License

This plugin is released under the [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause).

This plugin is distributing a transformed version of cpython documentation.
The cpython documentation is distributed [under it's own license](./hyperhelp/license.txt),
which is also readable from Sublime Text.


## Get started

- Install the package with `git clone`
- Restart Sublime Text
- Open Command Palette
- `HyperHelp: Browse available Help` > `PythonDocs` > `pathlib`
- Open a python file. Type `pathlib`, press `F1`. It should open the pathlib HyperHelp.
- Type `F1` anywhere in your python code to open the HyperHelp search box prefilled with the text under cursor.
