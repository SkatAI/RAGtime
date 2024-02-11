# Parsing Pipeline

for pdf files with one version of the AI-act

1. split file into N pages pdfs with N < 80>
2. upload to drive RAG-AI-Act
3. click right and open with google docs
4. use script apps to remove noise, markup, footnotes, etc
5. download as txt
6. rebuild in one txt file
7. clean up some more
7. 1.
    - remove footnotes
    - coherent line returns: none within paragraph
    - check order of paragraphs
    - remove consecutive spaces: \s{2,}
    - remove numbers attached to words
7. 2. split into sections: intro, recitals, regulation, annex
7. 3. markup the titles

* articles: ^=== Article (\d+)\s => === Article $1:
* paragraphs: ^\d+[a-z]{0,2}\. =>

8. export to json

# regexes
remove page number
\d+/\d+\sRB/ek\s\d+\sTREE\.2\.B EN

- in one line
TITLE I
GENERAL PROVISIONS

-> ## TITLE I: GENERAL PROVISIONS

^TITLE ([I,V,X]+)\n => ## TITLE $1:

- same for article

Article 1
Subject matter
-> \n== Article 1: Subject matter

^Article (\d+[a-z]{0,1})\n => == Article $1:

ANNEX I
ARTIFICIAL INTELLIGENCE TECHNIQUES AND APPROACHES

^ANNEX ([I,V,X]+)\n => ## ANNEX $1:

1.abcde => 1. abcde
^(\d+)\.([a-zA-Z]) => $1. $2