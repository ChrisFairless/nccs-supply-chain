import os
def root_dir():
    """gets root directory"""
    return os.path.abspath(os.path.dirname(__file__) + "/..")

