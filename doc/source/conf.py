import sys
from os.path import abspath
from wxfrog import __version__ as _release

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


# -- Path setup --------------------------------------------------------------
sys.path.insert(0, abspath('.'))

project = 'WxFrog'
copyright = '2025, Volker Siepmann'
author = 'Volker Siepmann'
release = _release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.todo',
    'sphinx.ext.autosummary',
    'sphinx_copybutton',
    'custom_directives',
    'sphinx.ext.intersphinx'
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pint': ('https://pint.readthedocs.io/en/stable/', None),
    'wxpython': ('https://docs.wxpython.org/', None)
}

# autoclass_content = 'both'
autodoc_member_order = 'bysource'
autodoc_class_signature = 'separated'
autodoc_typehints = 'signature'

# copy-button config
copybutton_prompt_text = r'>>> |\.\.\. '
copybutton_prompt_is_regexp = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

exclude_patterns = []

maximum_signature_line_length = 90

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'
html_static_path = ['_static']

html_sidebars = {
    '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
    'using/windows': ['windowssidebar.html', 'searchbox.html'],
}

html_css_files = ["custom.css"]

html_static_path = ['_static']
html_show_sourcelink = False
# html_favicon = "_static/goose.png"
todo_include_todos = True

rst_epilog = r"""
.. _Pint: https://pint.readthedocs.io
.. _PyYAML: https://pyyaml.org/
"""