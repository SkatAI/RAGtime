import re
import typing as t

class Rgx(object):
    # def roman(n): return chr(0x215F + n)

    @classmethod
    def format_number(cls, text: str) -> str:
        rgx     = r"(^[-]{0,1})(\d+)([a-z+-]{0,3}\d*)"
        match   = re.match(rgx, text)
        assert match is not None, "no number to be found"
        sign    = match.group(1).strip()
        num     = match.group(2).strip().zfill(3)
        letters = match.group(3).strip()

        return f"{num}{sign}{letters}"


    @classmethod
    def extract_section_title_number(cls, text: str) -> re.Match:
        rgx = r"^TITLE\s([I,X,V,A,b,c]+)\s*:.*$"
        return re.search(rgx, text)

    @classmethod
    def extract_annex_title_number(cls, text: str) -> re.Match:
        rgx = r"^ANNEX\s([I,X,V,A,b,c]+)\s*:.*$"
        return re.search(rgx, text, re.IGNORECASE)

    @classmethod
    def extract_chapter_title_number(cls, text: str) -> re.Match:
        # Chapter 1: CLASSIFICATION OF AI SYSTEMS AS HIGH-RISK
        # Part I: Section A. List of Union harmonisation
        # Section A: Information to be submitted
        rgx_chap = r"^Chapter\s*(\d+[a-zA-Z]{0,2})\s*:.*$"
        return re.search(rgx_chap, text)

    @classmethod
    def extract_annex_part_number(cls, text: str) -> re.Match:
        # Part I: Section A. List of Union harmonisation
        rgx_part = r"^Part\s([I,X,V,A,b,c]+)\s*:.*$"
        return re.search(rgx_part, text)

    @classmethod
    def extract_annex_section_number(cls, text: str) -> re.Match:
        # Part I: Section A. List of Union harmonisation
        rgx_sect = r"^Section\s([A-Z]+)\s*:.*$"
        return re.search(rgx_sect, text)

    @classmethod
    def extract_article_title_number(cls, text: str) -> re.Match:
        rgx = r"^Article\s(\d+[a-z]{0,2})\s*[:]{0,1}.*$"
        return re.search(rgx, text)

    @classmethod
    def extract_paragraph_number_from_title(cls, text: str) -> t.Optional[str]:
        # Article 3 - paragraph 1 - point 44c (new)
        rgx = r"^Article \d+ - paragraph (\d+).*$"
        return re.search(rgx,text)

    @classmethod
    def extract_subparagraph_number_from_title(cls, text: str) -> t.Optional[str]:
        # Article 3 - paragraph 1 - point 44c (new)
        rgx = r"^Article \d+[a-z]{0,2} - paragraph \d*[a-z]{0,2} - point (\d*[a-z]{0,2}).*$"
        return re.search(rgx,text)

    @classmethod
    def extract_paragraph_number(cls, text: str) -> re.Match:
        rgx = r"^([-]{0,1}\d+[a-z]{0,2})\..*$"
        return re.search(rgx, text)

    @classmethod
    def extract_subparagraph_number(cls, text: str) -> re.Match:
        rgx = r"^\(([a-z]{0,4})\).*$"
        return re.search(rgx, text)

    @classmethod
    def extract_bulletpoint_number(cls, text: str) -> re.Match:
        # rgx = r"^\((ⅰ|ii|iii|iiia|iv|v|vi|vii|viii|ix|x|xi|xii|xiii)\).*$"
        rgx = r"^\(([ivx]{1,3}[a]{0,1})\).*$"
        return re.search(rgx, text)

    @classmethod
    def extract_number_in_parenthesis(cls, text: str) -> re.Match:
        # (1) (12) (1a) (-12a) (80z+1)
        rgx = r"^\(([-]*\s*\d+\s*[a-z+-]{0,3}\d*)\).*$"
        return re.search(rgx, text)

    @classmethod
    def extract_first_number_from_title(cls, text: str) -> re.Match:
        # Recital 12a
        rgx = r"[-]{0,1}\d+[a-z]{0,3}"
        return re.search(rgx, text)

    @classmethod
    def starts_with(cls, start_str: str, text: str) -> re.Match:
        rgx = rf"^{start_str}"
        return re.search(rgx,text)

    @classmethod
    def is_annex_title(cls, text: str) -> re.Match:
        rgx = r"^## ANNEX"
        return re.search(rgx,text, re.IGNORECASE)

    @classmethod
    def is_section_title(cls, text: str) -> re.Match:
        rgx = r"^## TITLE"
        return re.search(rgx,text)

    @classmethod
    def is_chapter_title(cls, text: str) -> re.Match:
        rgx = r"^\*\* chapter"
        return re.search(rgx,text, re.IGNORECASE)

    @classmethod
    def is_annex_part(cls, text: str) -> re.Match:
        rgx = r"^\*\* Part"
        return re.search(rgx,text, re.IGNORECASE)

    @classmethod
    def is_annex_section(cls, text: str) -> re.Match:
        rgx = r"^\*\* Section"
        return re.search(rgx,text, re.IGNORECASE)

    @classmethod
    def is_article(cls, text: str) -> re.Match:
        rgx = r"^== Article"
        return re.search(rgx,text)

    @classmethod
    def is_paragraph(cls, text: str) -> re.Match:
        rgx = r"^([-]{0,1}\d+[a-z]{0,2})\."
        return re.search(rgx,text)

    @classmethod
    def is_subparagraph(cls, text: str) -> re.Match:
        rgx = r"^\(([a-z]{0,4})\).*$"
        return re.search(rgx,text)

    @classmethod
    def is_bulletpoint(cls, text: str) -> re.Match:
        # rgx = r"^\((ⅰ|ii|iii|iiia|iv|v|vi|vii|viii|ix|x|xi|xii|xiii)\).*$"
        rgx = r"^\(([ivx]{1,3}[a]{0,1})\).*$"
        return re.search(rgx,text)