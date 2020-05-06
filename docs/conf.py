import datetime

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

year = datetime.date.today().year
project = "PyAutoFit"
copyright = "2020, James Nightingale, Richard Hayes"
author = "James Nightingale, Richard Hayes"

# The full version, including alpha/beta/rc tags
release = "0.39.3"
master_doc = "index"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


sphinx_gallery_conf = {
    # Remove the "Download all examples" button from the top level gallery
    "download_all_examples": False,
    # directory where function granular galleries are stored
    "backreferences_dir": "api/generated/backreferences",
    # Modules for which function level galleries are created.
    "doc_module": "pyautofit",
    # Insert links to documentation of objects in the examples
    "reference_url": {"pyautofit": None},
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_last_updated_fmt = "%b %d, %Y"
html_title = "PyAutoFit"
html_short_title = "PyAutoFit"
pygments_style = "default"
add_function_parentheses = False
html_show_sourcelink = False
html_show_sphinx = True
html_show_copyright = True

html_context = {
    "menu_links_name": "Repository",
    # Custom variables to enable "Improve this page"" and "Download notebook"
    # links
    "doc_path": "docs",
    "github_project": "pyautofit",
    "github_repo": "pyautofit",
    "github_version": "development",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]