# Pdf Process
Comment extraire le textes du document pdf en 4 colonne de 892 paages

L'idée generale est de convertir le pdf en google doc pour pouvoir l'exporter ou en extraire le contenu.
A ce stade on pourrait exporter le google doc en plusieurs format rtf, html, ... de facon a avoir un document que l'on puisse parser plus facilement que le pdf.

Au final, j'ai trouvé plus "facile"  d'extraire le contenu textuel avec apps scripts, script javascript qui permet de modifier et de parser le contenu du google doc.

1) splitter en documents de 50 pages

- shell script https://github.com/SkatAI/RAGtime/blob/master/sh/split_pdf.sh

2) uploader les 18 pdf dans un folder google drive

3) convertir les pdf en google doc

- Etape manuel. click droit sur le fichier pdf et ouvrir en google doc.
- prendre les ID des docs google


4) faire tourner le script javascript.

dispo dans https://github.com/SkatAI/RAGtime/blob/master/script/pdfprocess/rm-strikethrough.js
le script
- enleve les textes barrés (strikethrough) du google doc
- extrait le conten restant en l'applatissant dans un fichier texte

Attention: pas besoin d'appeler la fonction main() dans le script. Apps script le fait par defaut.

5) parser les documents textes extraits des google docs

le script:https://github.com/SkatAI/RAGtime/blob/master/script/parsing/final_four.py

donne le fichier en json:

https://github.com/SkatAI/RAGtime/blob/master/data/json/final-four-2024-02-05.json


Notes:
- les scripts sont peu structurés. mode débroussaillage du problème.
- les choix de structure sont subjectifs. ne pas hesiter à les modifier. Il y a surement une façon de faire plus simple



