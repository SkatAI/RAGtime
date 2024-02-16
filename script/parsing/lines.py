import os, re, json, glob
import time, datetime
from datetime import timedelta
import pandas as pd
import argparse
from tqdm import tqdm
import numpy as np
import typing as t
from regex_utils import Rgx

class Line(object):
    def __init__(self, line):
        self.text = line

    def starts_with(self, start_str: str) -> re.Match:
        return Rgx.starts_with(start_str, self.text)

    def has_text(self) -> bool:
        return len(self.text) > 0

    def extract_first_number_from_title(self) -> t.Optional[str]:
        match  = Rgx.extract_first_number_from_title(self.text)
        return match.group(0).strip() if match else None

    def extract_number_in_parenthesis(self) -> t.Optional[str]:
        match = Rgx.extract_number_in_parenthesis(self.text)
        return match.group(1).strip() if match else None

    def is_subparagraph(self) -> t.Optional[str]:
        match = Rgx.is_subparagraph(self.text)
        return match.group(0).strip() if match else None

    def is_bulletpoint(self) -> t.Optional[str]:
        match = Rgx.is_bulletpoint(self.text)
        return match.group(0).strip() if match else None

    def get_line_type(self) -> None:
        if self.is_section_title():
            self.line_type = 'section_title'
            self.text = self.text.replace('##','').strip()
            self.number = self.extract_section_title_number()
        elif self.is_article_title():
            self.line_type = 'article_title'
            self.text = self.text.replace('==','').strip()
            self.number = self.extract_article_title_number()
        elif self.is_chapter_title():
            self.line_type = 'chapter_title'
            self.text = self.text.replace('**','').strip()
            self.number = self.extract_chapter_title_number()
        elif self.is_paragraph():
            self.line_type = 'paragraph'
            self.text = self.text.strip()
            self.number = self.extract_paragraph_number()
        elif self.is_subparagraph():
            self.line_type = 'subparagraph'
            self.text = self.text.strip()
            self.number = self.extract_subparagraph_number()

            if self.is_bulletpoint():
                    self.line_type = 'bulletpoint'
                    self.text = self.text.strip()
                    self.number = self.extract_bulletpoint_number()
        else:
            self.line_type = 'in_paragraph'
            self.text = self.text.strip()
            self.number = ''


    def is_section_title(self) -> t.Optional[str]:
        match = Rgx.is_section_title(self.text)
        return match.group(0).replace('##','').strip() if match else None

    def is_chapter_title(self) -> t.Optional[str]:
        match = Rgx.is_chapter_title(self.text)
        return match.group(0).replace('**','').strip() if match else None

    def is_article_title(self) -> t.Optional[str]:
        match = Rgx.is_article(self.text)
        return match.group(0).strip() if match else None

    def is_paragraph(self) -> t.Optional[str]:
        match = Rgx.is_paragraph(self.text)
        return match.group(0).strip() if match else None

    def extract_section_title_number(self) -> t.Optional[str]:
        match = Rgx.extract_section_title_number(self.text)
        return match.group(1).strip() if match else None

    def extract_article_title_number(self) -> t.Optional[str]:
        match = Rgx.extract_article_title_number(self.text)
        return match.group(1).strip() if match else None

    def extract_chapter_title_number(self) -> t.Optional[str]:
        match = Rgx.extract_chapter_title_number(self.text)
        return match.group(1).strip() if match else None

    def extract_paragraph_number(self) -> t.Optional[str]:
        match = Rgx.extract_paragraph_number(self.text)
        return match.group(1).strip() if match else None

    def extract_paragraph_number_from_title(self) -> t.Optional[str]:
        match = Rgx.extract_paragraph_number_from_title(self.text)
        return match.group(1).strip() if match else None

    def extract_subparagraph_number(self) -> t.Optional[str]:
        match = Rgx.extract_subparagraph_number(self.text)
        return match.group(1).strip() if match else None

    def extract_subparagraph_number_from_title(self) -> t.Optional[str]:
        match = Rgx.extract_subparagraph_number_from_title(self.text)
        return match.group(1).strip() if match else None

    def extract_bulletpoint_number(self) -> t.Optional[str]:
        match = Rgx.extract_bulletpoint_number(self.text)
        return match.group(1).strip() if match else None

class RecitalLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.first_number_from_title = self.extract_first_number_from_title()
        self.number_in_parenthesis = self.extract_number_in_parenthesis()


class RegulationLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.get_line_type()