"""Tests the functions within the module: interface"""
#from time import gmtime

from interface import random_words
#from interface import time_until_activate

def test_random_words():
    """Tests random_words"""
    random_words()
def test_time_until_activate():
    """Tests time_until_activate"""
    time_until_activate("00:00")
