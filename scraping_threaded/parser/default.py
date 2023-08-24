# ===========================================================================
#                            Default Parser
# ===========================================================================

from bs4 import BeautifulSoup as bs
from .parser import Parser
from .helpers import *


class DefaultParser(Parser):
    """Extract webpage content"""

    def extractText(self, url, response):
        """Parse the article content from the response object"""

        soup = bs(response, "html.parser")
        error = ""

        # Check to see if the soup contains explicit errors
        valid_soup = check_soup_validity(soup.text.lower())
        if valid_soup is not True:
            error = valid_soup  # return the error if it is found

        # Check if an alternative form of article text extraction is necessary
        alt_scraping = do_alternative_scraping(url, response, soup)
        if alt_scraping is not None:
            error = alt_scraping  # Return the extracted text if alt scraping was necessary

        # Get contents of the page in the standard way
        paragraphs = soup.find_all('p')
        stripped_paragraph = [tag.get_text().strip()
                              for tag in paragraphs]

        # If the standard way to scrape returned empty, try a different handling
        if len(stripped_paragraph) == 0 or stripped_paragraph == [""]:
            error = handle_empty_ptags(url, soup, response)

        text = " ".join(stripped_paragraph)

        return text, error
