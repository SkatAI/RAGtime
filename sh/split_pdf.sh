#!/bin/bash

# Name of the large PDF file
PDF="./data/pdf/AIAct_final_four-column21012024.pdf"

# Page size for each split
PAGES_PER_CHUNK=50

# Total number of pages in the PDF
TOTAL_PAGES=$(pdftk "$PDF" dump_data | grep NumberOfPages | awk '{print $2}')

# Calculate the number of chunks
NUM_CHUNKS=$((TOTAL_PAGES / PAGES_PER_CHUNK))
if [ $((TOTAL_PAGES % PAGES_PER_CHUNK)) -ne 0 ]; then
   NUM_CHUNKS=$((NUM_CHUNKS + 1))
fi

# Split the PDF into chunks
for ((i=1; i<=NUM_CHUNKS; i++)); do
    START_PAGE=$(( (i - 1) * PAGES_PER_CHUNK + 1 ))
    END_PAGE=$(( i * PAGES_PER_CHUNK ))
    if [ $END_PAGE -gt $TOTAL_PAGES ]; then
        END_PAGE=$TOTAL_PAGES
    fi
    pdftk "$PDF" cat $START_PAGE-$END_PAGE output "${PDF%.pdf}-part$(printf "%03d" $i).pdf"
done

echo "Split completed: $NUM_CHUNKS parts."