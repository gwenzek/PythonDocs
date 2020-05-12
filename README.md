# PythonDocs

Browse [docs.python.org](https://docs.python.org) inside Sublime Text

**‼ This is a proof of concept ‼**

This package leverage [HyperHelp](https://github.com/STealthy-and-haSTy/hyperhelpcore)
to show Python documentation from Sublime.

##  TODO

[ ] make the `.rst` parser more robust
[ ] add proper keybinding so that we can jump in documentation from Python code
[ ] process all python documentation programmatically
[ ] add support for other libraries using sphinx documentation

## For the curious

- Install the package with `git clone`
- Open Command Pallette
- `HyperHelp: Browse available Help` > `PythonDocs` > `pathlib`

## For the intrepids

- Install [HyperHelpAuthor](https://github.com/STealthy-and-haSTy/HyperHelpAuthor)
- Grap a `.rst` file from https://github.com/python/cpython/tree/3.8/Doc
- Copy it to `rst` folder.
- Run `python convert/convert.py`
- Open `help/hyperhelp.json`
- `HyperHelpAuthor: reload index` (this command is a bit capricious, if it doesn't work try re-opening HyperHelp > PythonDocs > pathlib then retry.)
- `HyperHelp: Browse available Help` > `PythonDocs` > search the module you just added.
