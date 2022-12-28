#!/usr/bin/env python
import os

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
]

autodoc_member_order = 'bysource'
autosectionlabel_prefix_document = True
nitpicky = True
nitpick_ignore = [
    ('py:obj', 'typing.Union'),
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = 'ningen'
copyright = "2022, Oren Ben-Kiki"
author = "Oren Ben-Kiki"

version = "0.1.0"
release = version

language = None

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'sphinx'

todo_include_todos = True
todo_link_only = True

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]