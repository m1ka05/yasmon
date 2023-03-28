# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Yasmon'
copyright = '2023, Michał Ł. Mika'
author = 'Michał Ł. Mika'
release = '0.2.4'
version = release

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
sys.path.insert(0, os.path.abspath('../../'))


# sphinx-rtd-theme v1.2.0
# known issue: jQuery not loading (on Github-Pages)
# (https://github.com/readthedocs/readthedocs.org/pull/9654)
# fix: add 'sphinx_rtd_theme' to extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
    'sphinxemoji.sphinxemoji',
    #'sphinx_toolbox.shields',
]

templates_path = ['_templates']
#exclude_patterns = []

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': False,
    'exclude-members': '__weakref__, __dict__, __module__'
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'navigation_depth': -1,
    'collapse_navigation': False,
    'titles_only': False,
    'display_version': True,
}
