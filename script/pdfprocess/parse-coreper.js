// that approach did not work. Instances of the regex were found, but the text  was not modified
//  switched to a paragraohn and sequence based approach
function rmFootnotes(docurl) {
    // 5662/24 RB/ek 210 TREE.2.B LIMITE EN
    // 5662/24 RB/ek 201 TREE.2.B LIMITE EN
    var doc = DocumentApp.openByUrl(docurl);
    var body = doc.getBody();
    // var text = body.getText();
    var text = body.editAsText();

    // Regex pattern to match the strings
    // Adjust the pattern as needed to match the specific format
    // var pattern = "\\d+/\\d+\\s+RB/ek\\s+\\d+\\s+TREE\\.2\\.B\\s+LIMITE\\s+EN";
    // var regexPattern = "\\d+/\\d+ rb/ek \\d+ tree\\.2\\.b limite en"; // Adjust this pattern as needed
    // var pattern = "\\d+/\\d+\\s+RB/ek\\s+\\d+\\s+TREE\\.2\\.B\\s+LIMITE\\s+EN";
    var pattern = "LIMITE EN";
    var regex = new RegExp(pattern, "g");

    // Find all matches
    var matches = text.match(regex);
    var count = matches ? matches.length : 0;

    // Log the count of matches found
    console.log("Found " + count + " instances of the pattern.");

    // Replace all instances of the pattern with an empty string
    if (count > 0) {
      body.replaceText(regex, "");
      doc.saveAndClose();
    } else {
      console.log("Pattern Not found");
    }
  }

  function removeSpecificStringUsingDeleteText(docurl) {
    var doc = DocumentApp.openByUrl(docurl);
    var body = doc.getBody();
    var paragraphs = body.getParagraphs();

    var pattern = new RegExp("\\d+/\\d+\\s+RB/ek\\s+\\d+\\s+TREE\\.2\\.B\\s+LIMITE\\s+EN", "g");

    paragraphs.forEach(function(paragraph) {
      var text = paragraph.getText();
      var matches;
      while ((matches = pattern.exec(text)) !== null) {
        // Calculate start and end positions for deletion
        var startOffset = matches.index;
        var endOffset = startOffset + matches[0].length - 1; // Adjust because deleteText uses inclusive end index

        // Delete the matched text
        paragraph.editAsText().deleteText(startOffset, endOffset);

        // Update the text variable to reflect the current state of the paragraph text
        text = paragraph.getText();
        // Reset the regex search index to avoid infinite loops
        pattern.lastIndex = 0;
      }
    });
  }

  function main() {
      // la liste des documents pdf en version google doc
      const documentsUrls = [
          "https://docs.google.com/document/d/183_V48xDHl8qyEHpbkgUcdoathzRWOsshLVORmfka2s/edit",
          "https://docs.google.com/document/d/1K4xK9bYWEdp_QNWZgxhyYyucRschD4BrD5ikNMN5UWw/edit",
          "https://docs.google.com/document/d/10GHR4Dd-yXqZ6iI2BnB8Fi2GXNkVhqCfrMk7HM1D6eM/edit",
          "https://docs.google.com/document/d/19IoqZqP9gR_BXTxMX11C3IWjcal83nGD4f2zcFvAWl4/edit",

      ];

      // const execrm = false;
      documentsUrls.forEach(function(docurl) {
          console.log("docurl: " + docurl);
          removeSpecificStringUsingDeleteText(docurl);

      });

  }

