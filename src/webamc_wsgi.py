"""Provides application."""

# update default configuration parameters
from webamc import config
config.load("/path/to/config.json")

# and launch the application
from webamc.www.app import application
