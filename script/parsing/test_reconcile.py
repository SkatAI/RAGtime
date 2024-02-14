'''
'''

# usual libs
import os, re, json, glob
import time, datetime
from datetime import timedelta
from tqdm import tqdm
import typing as t
from reconcile import Line, Rgx


if __name__ == "__main__":

    assert Line("(1) hello").number_in_parenthesis  == "1"
    assert Line("(1a) hello").number_in_parenthesis  == "1a"
    assert Line("(1 ) hello").number_in_parenthesis  == "1"
    assert Line("(12) hello").number_in_parenthesis  == "12"
    assert Line("(-12) hello").number_in_parenthesis  == "-12"
    assert Line("(80z+1) hello").number_in_parenthesis  == "80z+1"
    assert Line("(80-x) hello").number_in_parenthesis  == "80-x"
    assert Line("(60aa) hello").number_in_parenthesis  == "60aa"
    assert Line("hello (60aa) world").number_in_parenthesis  is None


    assert Line("Recital 1").first_number_from_title == '1'
    assert Line("Recital 10").first_number_from_title == '10'
    assert Line("Recital 2b").first_number_from_title == '2b'
    assert Line("Recital -12b").first_number_from_title == '-12b'


    assert Rgx.format_number('1') == '001'
    assert Rgx.format_number('1a') == '001a'
    assert Rgx.format_number('-1a') == '001-a'
    assert Rgx.format_number('-1') == '001-'
    assert Rgx.format_number('80z+1') == '080z+1'
    assert Rgx.format_number('80-x') == '080-x'



