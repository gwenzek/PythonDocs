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

- First make this package and dependencies visible to Package Control
  - Open Command Palette
  - `Package Control: Add Repository`
  - Paste in the URL https://raw.githubusercontent.com/STealthy-and-haSTy/SublimePackages/master/unreleased-packages.json 
- Install this package
  - Command Palette: `Package Control: Install Package` > `PythonDocs`
  - Restart Sublime Text
- Test it through Command Palette
  - Command Palette: `HyperHelp: Browse available Help` > `PythonDocs` > `pathlib`
  - This should open a new view showing pathlib documentation
  - Try navigating by using `tab`, `enter`
- Add keybindings
  - !!! Command is currently broke, need fix !!!
  - Command Palette: `Preferences: Key Bindings`
  - Insert `{"keys": ["f1"], "command": "python_docs_open", "context": [{"key": "selector", "operator": "equal", "operand": "source.python"}]},`
  - Save and exit the key bindings view
  - Open a python file. Type `pathlib`, press `F1`. It should open the pathlib HyperHelp.
  - Type `F1` anywhere in your python code to open the HyperHelp search box prefilled with the text under cursor.
