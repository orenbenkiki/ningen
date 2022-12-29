#!/usr/bin/env python
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

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
    ('py:obj', 'typing.Optional'),
    ('py:obj', 'typing.Union'),
    ('py:class', 'collections.abc.Sequence'),
    ('py:class', 're.Pattern'),
    ('py:class', 'TextIO'),
    ('py:class', 'typing.TextIO'),
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = 'ningen'
copyright = "2022, Oren Ben-Kiki"
author = "Oren Ben-Kiki"

version = "0.2.0"
release = version

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'sphinx'

todo_include_todos = True
todo_link_only = True

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


def run_apidoc(_):
    from sphinx.ext.apidoc import main
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    module = os.path.join(cur_dir, "..", "ningen")
    main(['-e', '-o', cur_dir, module, '--force'])


def setup(app):
    app.connect('builder-inited', run_apidoc)
