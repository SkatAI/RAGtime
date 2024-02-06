function rmStrikethrough(docurl, execrm) {
    var body = DocumentApp.openByUrl(docurl).getBody();
    var paragraphs = body.getParagraphs();
    var strikethroughSequences = []; // Array to store the start and end positions of strikethrough sequences

    paragraphs.forEach(function(paragraph, paragraphIndex) {
        var text = paragraph.editAsText();
        var textLength = text.getText().length;
        var inStrikethrough = false;
        var strkStartIndex = -1;

        for (var i = 0; i < textLength; i++) {
            if (text.isStrikethrough(i)) {
                if (!inStrikethrough) {
                    inStrikethrough = true;
                    strkStartIndex = i;
                }
            } else {
                if (inStrikethrough) {
                    strikethroughSequences.push({
                        paragraphIndex: paragraphIndex,
                        start: strkStartIndex,
                        end: i - 1
                        });
                    inStrikethrough = false;
                }
            }
        }

        if (inStrikethrough) {
            strikethroughSequences.push({
                paragraphIndex: paragraphIndex,
                start: strkStartIndex,
                end: textLength - 1
            });
        }
    });

    // Log for verification
    strikethroughSequences.forEach(function(seq) {
        console.log(`Paragraph ${seq.paragraphIndex + 1}: Strikethrough starts at ${seq.start}, ends at ${seq.end}`);
    });

    // Reverse the array to start inserting tags from the end of the document
    if (execrm) {
        console.log("==> deleting " + strikethroughSequences.length + " characters")
        strikethroughSequences.reverse().forEach(function(seq) {
            var paragraph = paragraphs[seq.paragraphIndex];
            var text = paragraph.editAsText();
            text.deleteText(seq.start, seq.end);
        });
    } else {
        console.log("-- found " + strikethroughSequences.length + " characters")
    }
}


function main() {
    // la liste des documents pdf en version google doc
    const documentsUrls = [
        "https://docs.google.com/document/d/1nVkXtNnmaDGnQCbeJIUYFUq4DFRxqngrBPLyFy22u84/edit",
        "https://docs.google.com/document/d/1kn9MqftWIbQv6HFETmWzBAp6kBayZInej1hyRGvJjLI/edit",
        "https://docs.google.com/document/d/19l1kuA-Z59LBzmhWJg6SHXdUH5ZJ_GK87LCAl00_iZQ/edit",
        "https://docs.google.com/document/d/1ZUnXQ4yHt2QfZXvndgnBWwZWWKWkCeMqXQ5S3O7QUeQ/edit",
        "https://docs.google.com/document/d/1gICSorV9VckpQRn3zZ5dVuNa7xYYo86wYFMKyyNCQvM/edit",
        "https://docs.google.com/document/d/1IzCum2NhiU1dDU6OlANR03RWArUqMRYl1vUz021swls/edit",
        "https://docs.google.com/document/d/1cTkxc8UIeqDVniBp82AEX42VXCvpMPFmDmOPdJCHyfg/edit",
        "https://docs.google.com/document/d/1x0g-t6kqnnx70CmBmhuhlxb_jNkDVhgUCe1UVmrSNiQ/edit",
        "https://docs.google.com/document/d/1jiNuTFEZg6hpL2fQKhJYUyHj9lk8tNhKCLq1V52N2Rk/edit",
        "https://docs.google.com/document/d/1TOoujctT_9eWvJS2Sm3ZC9t_B03htyuGffDASb_qA3c/edit",
        "https://docs.google.com/document/d/1twcKAXSYLlkS4WOcq_Z4vimLQHKQRjXMGJ7gT0wMlKc/edit",
        "https://docs.google.com/document/d/17wZwcgeiXJ8Kmm1XigAvJWtSvOV1rerNPPs-FblPN5A/edit",
        "https://docs.google.com/document/d/1Hs6FlS9WpQDCeKFdysP9k0j1BmPDjm3rgXUWVxYFc-4/edit",
        "https://docs.google.com/document/d/1u3sKubI9ewmiPQM18ra0LIqb8XXzsbVPJiy8pfZhf6U/edit",
        "https://docs.google.com/document/d/157PLKEdzrWFsL5bAqQ4LC_dxsju0Bnrm_uhwx1skWvk/edit",
        "https://docs.google.com/document/d/1Kr_QfFihEaNoi7fdsQGvPUkeZCkMa4q3sgWYLM35WVg/edit",
        "https://docs.google.com/document/d/1xezyWxISYCPc3oHnY_KVQ-wyScfs9dqy5UasI1YsC1M/edit",
        "https://docs.google.com/document/d/10XkpOoCe4TZh8QnFSJsiaXzDHpHbkTeYGNwu9uJsL6Q/edit"
    ];

    const execrm = false;
    documentsUrls.forEach(function(docurl) {
        console.log("docurl: " + docurl);

        rmStrikethrough(docurl,execrm );
    });

}


// Execute the main function to run the script
main();


//  good to extract text from tables

// const docurl = "https://docs.google.com/document/d/1esi4t7p4zhm8eCqMTdWzgTmDknM0wyCfME62GBrsfzE/edit";
function extractAndExportText() {
    var current_doc = DocumentApp.openByUrl(docurl);
    var doc_title = current_doc.getName();

    var body = current_doc.getBody();
    var tables = body.getTables();
    var extractedTexts = []; // Array to store extracted texts
    var table_count = 0
    tables.forEach(function(table) {
        var numRows = table.getNumRows();
        table_count += 1
        extractedTexts.push('' );
        extractedTexts.push('TTTXX TABLE: ' + table_count + ' XXTTT' );
        Logger.log('numRows: ' + numRows)

        for (var i = 0; i < numRows; i++) {
            extractedTexts.push('== ROW ' + table_count + '.' + i + ' ==');

            var row = table.getRow(i);
            var numCells = row.getNumCells();
            Logger.log('numCells: ' + numCells)
            for (var j = 0; j < numCells; j++) {
                extractedTexts.push('-- COL ' + table_count + '.' + i + '.' + j +  ' --');
                var text = row.getCell(j).getText();
                Logger.log('text: ' + text)
                extractedTexts.push(text);
            }
        }
    });

    // Combine all extracted texts into a single string, separated by new lines
    var combinedText = extractedTexts.join('\n');
    Logger.log('--------')
    Logger.log(combinedText)
    // Create and write to a text file on Google Drive
    var fileName = doc_title + '.txt';
    var folder = DriveApp.getFolderById('1_1G_D_mm33fBzmo1ppcp3vpEvOpIN-1-');
    var file = folder.createFile(fileName, combinedText);

    // var file = DriveApp.createFile(fileName, combinedText);

    Logger.log('Text file created: ' + fileName);
    Logger.log('File ID: ' + file.getId());
}



// // good to remove strikethrough in paragraphs
// 1cNd1RN4AujTiRJQerTxZYch682JGsefH
// https://docs.google.com/document/d/1cNd1RN4AujTiRJQerTxZYch682JGsefH/

// https://drive.google.com/file/d/1cNd1RN4AujTiRJQerTxZYch682JGsefH/view
// const docurl = "https://docs.google.com/document/d/1esi4t7p4zhm8eCqMTdWzgTmDknM0wyCfME62GBrsfzE/edit";

// function logAndStoreStrikethroughPositions() {
//   var body = DocumentApp.openByUrl(docurl).getBody();
//   var paragraphs = body.getParagraphs();
//   var strikethroughSequences = []; // Array to store the start and end positions of strikethrough sequences

//   paragraphs.forEach(function(paragraph, paragraphIndex) {
//     var text = paragraph.editAsText();
//     var textLength = text.getText().length;
//     var inStrikethrough = false;
//     var strkStartIndex = -1;

//     for (var i = 0; i < textLength; i++) {
//       if (text.isStrikethrough(i)) {
//         if (!inStrikethrough) {
//           inStrikethrough = true;
//           strkStartIndex = i;
//         }
//       } else {
//         if (inStrikethrough) {
//           strikethroughSequences.push({
//             paragraphIndex: paragraphIndex,
//             start: strkStartIndex,
//             end: i - 1
//           });
//           inStrikethrough = false;
//         }
//       }
//     }

//     if (inStrikethrough) {
//       strikethroughSequences.push({
//         paragraphIndex: paragraphIndex,
//         start: strkStartIndex,
//         end: textLength - 1
//       });
//     }
//   });

//   // Log for verification
//   strikethroughSequences.forEach(function(seq) {
//     console.log(`Paragraph ${seq.paragraphIndex + 1}: Strikethrough starts at ${seq.start}, ends at ${seq.end}`);
//   });

//   // Reverse the array to start inserting tags from the end of the document
//   strikethroughSequences.reverse().forEach(function(seq) {
//     var paragraph = paragraphs[seq.paragraphIndex];
//     var text = paragraph.editAsText();
//     text.deleteText(seq.start, seq.end);
//   });
// }


// function logStrikethroughPositions() {
//   const docurl = "https://docs.google.com/document/d/1esi4t7p4zhm8eCqMTdWzgTmDknM0wyCfME62GBrsfzE/edit";
//   var body = DocumentApp.openByUrl(docurl).getBody();
//   var paragraphs = body.getParagraphs();

//   paragraphs.forEach(function(paragraph, paragraphIndex) {
//     var text = paragraph.editAsText();
//     var textLength = text.getText().length;
//     console.log('textLength: ' +textLength )
//     var inStrikethrough = false;
//     var strkStartIndex = -1;

//     for (var i = 0; i < textLength; i++) {
//       if (text.isStrikethrough(i)) {
//         if (!inStrikethrough) {
//           // Start of a new strikethrough section
//           inStrikethrough = true;
//           strkStartIndex = i;
//         }
//       } else {
//         if (inStrikethrough) {
//           // End of a strikethrough section
//           console.log(`Paragraph ${paragraphIndex + 1}: Strikethrough starts at ${strkStartIndex}, ends at ${i - 1}`);
//           inStrikethrough = false;
//         }
//       }
//     }

//     // Check if the last character of the paragraph is strikethrough
//     if (inStrikethrough) {
//       console.log(`Paragraph ${paragraphIndex + 1}: Strikethrough starts at ${strkStartIndex}, ends at ${textLength - 1}`);
//     }
//   });
// }



// function tagStrikethroughText() {
//     var docurl = "https://docs.google.com/document/d/1_r6fJJ0nDscA6fO8mWOcTBYMIwJgoKpVkMu2PU-usag/edit"
//     var body = DocumentApp.openByUrl(docurl).getBody();
//     var paragraphs = body.getParagraphs();

//     paragraphs.forEach(function(paragraph) {
//       var text = paragraph.editAsText();
//       var textLength = text.getText().length;
//       var inStrikethrough = false;
//       var strkStartIndex = -1;

//       for (var i = 0; i < textLength; i++) {
//         if (text.isStrikethrough(i)) {
//           if (!inStrikethrough) {
//             // Start of a new strikethrough section
//             inStrikethrough = true;
//             strkStartIndex = i;
//           }
//         } else {
//           if (inStrikethrough) {
//             // End of a strikethrough section
//             // text.insertText(strkStartIndex, "<strk>");
//             // Adjust current index and length due to insertion
//             i += "<strk>".length;
//             // textLength += "<strk>".length;
//             text.insertText(i, "</strk>");
//             // Adjust length due to insertion
//             textLength += "</strk>".length;
//             inStrikethrough = false;
//           }
//         }
//       }

//       // Check if the last character of the paragraph is strikethrough
//       if (inStrikethrough) {
//         text.insertText(strkStartIndex, "<strk>");
//         text.appendText("</strk>");
//       }
//     });
//   }




// function findItalicCharacters() {
//     var docurl = "https://docs.google.com/document/d/1_r6fJJ0nDscA6fO8mWOcTBYMIwJgoKpVkMu2PU-usag/edit"
//     var body = DocumentApp.openByUrl(docurl).getBody();
//     var paragraphs = body.getParagraphs();
//     var italicChars = []; // Array to hold positions of italic characters

//     paragraphs.forEach(function(paragraph, paragraphIndex) {
//       var text = paragraph.getText();
//       for (var i = 0; i < text.length; i++) {
//         if (paragraph.getAttributes(i).ITALIC) {
//           italicChars.push(`Paragraph ${paragraphIndex + 1}, Position ${i + 1}: '${text[i]}'`);
//         }
//       }
//     });

//     // Log the italic characters, if any
//     if (italicChars.length > 0) {
//       Logger.log("Italic characters found:\n" + italicChars.join("\n"));
//     } else {
//       Logger.log("No italic characters found.");
//     }
// }



// function findItalicWords() {
//   var docurl = "https://docs.google.com/document/d/1_r6fJJ0nDscA6fO8mWOcTBYMIwJgoKpVkMu2PU-usag/edit"
//   var body = DocumentApp.openByUrl(docurl).getBody();
//   var text = body.getText();
//   var words = text.match(/\b[\w']+\b/g); // Regular expression to match words

//   if (words) {
//     var strikeWords = []; // Array to hold words that are in strikethrough
//     for (var i = 0; i < words.length; i++) {
//       var word = words[i];
//       var searchResult = body.findText(word); // Find the word in the document body

//       while (searchResult) {
//         var foundText = searchResult.getElement().asText();
//         var startOffset = searchResult.getStartOffset();
//         var endOffset = searchResult.getEndOffsetInclusive();

//         // Check if the word (or part of it) is in italic
//         for (var offset = startOffset; offset <= endOffset; offset++) {
//           const strk = foundText.isStrikethrough(offset);
//           console.log(startOffset + ' ' + word);
//           if (strk) {
//             strikeWords.push(word);
//             console.log('     '+strk);
//             break; // Break the inner loop if any part of the word is in italic
//           }
//           else{
//             console.log('--');
//           }
//         }

//         // Find next occurrence of the word
//         searchResult = body.findText(word, searchResult);
//       }
//     }

//     if (strikeWords.length > 0) {
//         Logger.log("strikeWords words found: " + strikeWords.join(", "));
//       } else {
//         Logger.log("No strikeWords words found.");
//       }

//   } else {
//     Logger.log("No words found in the document.");
//   }
// }
