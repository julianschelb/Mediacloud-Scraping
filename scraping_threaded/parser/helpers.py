import parser.exceptions as e
import json
import re
from lxml import etree


def check_scrapability(url: str):
    # For urls that will never be able to be scraped
    error = True  # returns true if the url is not any of the ones listed below

    for item in e.n_scrapable_url_errors['Website is no longer maintained']:
        if item in url:
            error = 'ERROR: Website is no longer maintained'

    for elt in e.n_scrapable_url_errors['Video/ Image content only']:
        if elt in url:
            error = 'ERROR: Video/ Image content only'

    if url.endswith('.jpg'):
        error = 'ERROR: Video/ Image content only'

    for obj in e.n_scrapable_url_errors['Not scrapable content']:
        if obj in url:
            error = 'ERROR: Not scrapable content'

    if 'msnbc' in url and 'watch' in url:
        error = 'ERROR: Video/ Image content only'
    if 'ir.voanews' in url or 'paper.li' in url or "hani.co.kr" in url or 'destentor.nl' in url or 'thenewsdoctors.com' in url:
        error = 'ERROR: Not in English'
    if '.pdf' in url:
        error = 'ERROR: Content is a pdf'

    if 'calciomercato.com' in url or 'shadowandact.com' in url:
        error = 'ERROR: Must enable cookies to access site'
    return error


def check_soup_validity(low_soup_text: str) -> str:
    # Check for explicit error messages in the soup contents
    error = True
    if '401 authorization required' in low_soup_text or 'user is not authorized to perform this action' in low_soup_text:
        error = 'ERROR: 401 Authorization Required'

    for f in e.soup_contents_text_errors['403 Forbidden']:
        if f in low_soup_text:
            error = 'ERROR: 403 Forbidden'
    if low_soup_text == 'forbidden' or low_soup_text == '403':
        error = 'ERROR: 403 Forbidden'

    if 'Looks like something went wrong.'.lower() == low_soup_text or 'Something went wrong. Wait a moment and try again.'.lower() == low_soup_text:
        error = 'ERROR: 404 Page not found'
    if ' BLACKLISTED NEWS FAVORITES'.lower() == low_soup_text:
        error = 'ERROR: 404 Page not found'
    for n in e.soup_contents_text_errors['404 Page not found']:
        if n in low_soup_text:
            error = 'ERROR: 404 Page not found'
    if low_soup_text == 'not found':
        error = 'ERROR: 404 Page not found'

    if low_soup_text == 'not acceptable':
        error = 'ERROR: 406 Not Acceptable'
    if '406 not acceptable' in low_soup_text:
        error = 'ERROR: 406 Not Acceptable'

    if '410 deleted by author' in low_soup_text:
        error = 'ERROR: 410 Deleted'

    for elt in e.soup_contents_text_errors['451 Unavailable for legal reasons']:
        if elt in low_soup_text:
            error = 'ERROR: 451 Unavailable for legal reasons'

    if 'reported a bad gateway error' in low_soup_text or '502 bad gateway' in low_soup_text:
        error = 'ERROR: 502 gateway error'

    if 'this content has been removed' in low_soup_text:
        error = "ERROR: Article has been archived"

    for obj in e.soup_contents_text_errors['Article behind a paywall or login page']:
        if obj in low_soup_text:
            error = "ERROR: Article behind a paywall or login page"

    for item in e.soup_contents_text_errors['Article not found']:
        if item in low_soup_text:
            error = "ERROR: Article not found"

    if 'blocked your ip' in low_soup_text or low_soup_text == 'too many requests':
        error = 'ERROR: Blocked from website'
    for b in e.soup_contents_text_errors['Blocked from website']:
        if b in low_soup_text:
            error = 'ERROR: Blocked from website'

    if 'client-side exception' in low_soup_text:
        error = "ERROR: Client-Side Exception"

    if 'an unknown connection issue between Cloudflare and the origin web server'.lower() in low_soup_text:
        error = 'ERROR: Connection Issue'

    if 'internal server error' in low_soup_text:
        error = 'ERROR: Internal Server Error'

    if 'This error was generated by Mod_Security'.lower() in low_soup_text:
        error = 'ERROR: Mod_Security server-side error'

    for j in e.soup_contents_text_errors['Must enable cookies to access site']:
        if j in low_soup_text:
            error = 'ERROR: Must enable cookies to access site'

    if 'The provided host name is not valid for this server.'.lower() in low_soup_text:
        error = 'ERROR: Provided host name is not valid for this server'

    if 'server temporarily unavailable' in low_soup_text:
        error = "ERROR: Server side connection error"

    if '\nvia youtube' in low_soup_text:
        error = 'ERROR: Video/ Image content only'

    return error


def do_alternative_scraping(url, response, soup):
    app_json_art_body = ['qz.com', 'newtimes.com.rw',
                         'newtimes.co.rw', 'newsweek.com', 'scmp.com']
    for a in app_json_art_body:
        if a in url:
            if 'Forbidden' in response:
                return 'ERROR: 403 Forbidden'
            tree = etree.HTML(response)
            json_type_elts = tree.xpath(
                '//script[@type="application/ld+json"]')
            for jte in json_type_elts:
                if 'articleBody' in jte.text:
                    json_obj = json.loads(jte.text)
                    try:
                        article_text = json_obj['articleBody']
                        return article_text
                    except KeyError:
                        return 'ERROR: No text gathered'
            paragraphs = soup.find_all('p')
            stripped_paragraph = [tag.get_text().strip() for tag in paragraphs]
            if len(stripped_paragraph) > 0:
                return " ".join(stripped_paragraph)
            return 'ERROR: No text gathered'
    if 'miamiherald.typepad.com' in url:
        div_elts = soup.find_all('div', attrs={'id': "story-content"})
        stripped = [tag.get_text().strip() for tag in div_elts]
        return " ".join(stripped)
    if 'dailywire.com' in url:
        div_elts = soup.find_all('div', attrs={'id': 'post-body-text'})
        stripped = [tag.get_text().strip() for tag in div_elts]
        return " ".join(stripped)
    if 'nationalreview.com' in url:
        # Try with tree
        tree = etree.HTML(response)
        json_type_elts = tree.xpath('//script[@type="text/javascript"]')

        # Original version: This has worked at least three times
        js_var = re.findall(
            r'nr.headless.preloadedData = .*;', response)  # debug
        if len(js_var) > 0:
            js_var_data = js_var[0].replace(
                'nr.headless.preloadedData = ', '')[:-1]
            json_obj = json.loads(js_var_data)
            first_key = list(json_obj.keys())[0]
            content = json_obj[first_key]['body']['queried_object']['content']['rendered']
            js_soup = bs(content, 'html.parser')
            text = js_soup.get_text().strip()
            return text
        return 'ERROR: No text fathered'
    if 'columbiaspectator.com' in url:
        # Try tree version #debug
        tree = etree.HTML(response)

        # Old version
        fusion_global_content = re.findall(r'Fusion\.globalContent=.*?};',
                                           response)  # find the data given the variable name
        fg_contents = fusion_global_content[0].replace('Fusion.globalContent=', '')[
            :-1]  # get the contents of the variables
        json_vers = json.loads(fg_contents)  # make it a json obj
        # get the relevant section of the json obj
        content_elts = json_vers['content_elements']
        text = []
        for item in content_elts:
            if item['type'] == 'text':
                text.append(item['content'])
        return " ".join(text)

    if 'toledoblade' in url:
        tree = etree.HTML(response)
        json_type_elts = tree.xpath('//script[contains(text(),"JSON")]')
        for jte in json_type_elts:
            if 'pgStoryZeroJSON' in jte.text:
                cleaned_json = jte.text.replace(
                    'pgStoryZeroJSON = ', '').replace('\n', '')
                try:
                    json_version = json.loads(cleaned_json)
                    article_body = json_version['articles'][0]['body']
                    soup_obj = bs(article_body, 'html.parser')
                    text = soup_obj.get_text().strip()
                    return text  # works, 11
                except json.decoder.JSONDecodeError:
                    article_regex = re.findall(r'body": ".*?",', cleaned_json)
                    cleaned_article_regex = article_regex[0].replace(
                        'body": "', '').replace('"', '')
                    soup_obj = bs(cleaned_article_regex, 'html.parser')
                    text = soup_obj.get_text().strip()
                    return text

    if 'blacknews.com/news' in url:
        div_elts = soup.find_all(
            'div', attrs={'class': "post-body entry-content"})
        stripped = [tag.get_text().strip() for tag in div_elts]
        return " ".join(stripped)

    if 'thepoliticalinsider' in url:
        blog_div_elts = soup.find_all(
            'div', attrs={'class': 'text article-body font-default font-size-med'})
        stripped = [tag.get_text().strip() for tag in blog_div_elts]
        if len(stripped) > 0:
            return " ".join(stripped)
        script_variable = re.findall(
            r'class="yoast-schema-graph">[\S\s]*?<\/script>', response)
        try:
            script_data = script_variable[0].replace(
                'class="yoast-schema-graph">', '').replace('</script>', '')
            json_option = json.loads(script_data)
            dv = True  # Todo: finsih this
        except IndexError:
            return "ERROR: Scraping error during JSON conversion"

    if 'ibtimes.com' in url or 'ibtimes.co' in url:
        if 'Forbidden' in response:
            return 'ERROR: 403 Forbidden'
        tree = etree.HTML(response)
        json_type_elts = tree.xpath('//script[contains(@type,"json")]')
        # json_obj = json.loads(json_type_elts[-1].text)
        # contents = json_obj['props']['pageProps']['pageContent']['parsedBody']
        # text = [content for content in contents if isinstance(content, str)]
        # return " ".join(text)
        return 'ERROR: No text gathered'
    if 'tampabay.com' in url:
        tree = etree.HTML(response)
        json_elts = tree.xpath('//script[contains(@type,"json")]')
        return 'ERROR: No text gathered'  # Doesnt seem to work
    if 'newsday.com' in url:
        tree = etree.HTML(response)
        json_elts = tree.xpath('//script[contains(@type,"json")]')
        try:
            for elt in json_elts:
                if 'bodyText' in elt.text:
                    json_version = json.loads(elt.text)
                    text = json_version['props']['pageProps']['data']['page']['leaf']['bodyText']
                    return text
            return 'ERROR: No text gathered'
        except IndexError:
            return 'ERROR: No text gathered'
        except KeyError:
            return 'ERROR: No text gathered'

    if 'timesofindia' in url:
        if 'videoshow' in url or '/photostory' in url:
            return "ERROR: Video/ Image content only"
        alt_elts = soup.find_all('div', attrs={'data-articlebody': '1'})
        stripped = [tag.get_text().strip() for tag in alt_elts]
        if len(stripped) < 1:
            blog_div_elts = soup.find_all(
                'div', attrs={'class': 'main-content single-article-content'})
            stripped = [tag.get_text().strip() for tag in blog_div_elts]
            if len(stripped) < 1:
                return 'ERROR: No text gathered'
            return " ".join(stripped)
        return " ".join(stripped)

    if 'newsmax.com' in url.lower():
        div_elts = soup.find_all('div', id='mainArticleDiv')
        stripped = [tag.get_text().strip() for tag in div_elts]
        return " ".join(stripped)

    if 'sbs.com.au' in url:
        tree = etree.HTML(response)
        json_type_elts = tree.xpath('//script[contains(@type,"json")]')
        json_obj = json.loads(json_type_elts[-1].text)
        contents = json_obj['props']['pageProps']['pageContent']['parsedBody']
        text = [content for content in contents if isinstance(content, str)]
        return " ".join(text)

    if 'NDTV-LatestNews' in url:
        div_elts = soup.find_all('div', id='ins_storybody')
        stripped = [tag.get_text().strip() for tag in div_elts]
        return " ".join(stripped)

    return None


def handle_errors_in_empty_ptags(url, soup_text):
    # If there's not content in the ptags, check the soup.text for error handling
    # Also checks the url in some cases
    text = True
    if 'pantsonfirenews.com' in url:
        text = 'ERROR: 403 Forbidden'
    if 'fox2now.com/news' in url or 'ktla.com/news/' in url:
        text = 'ERROR: 451 Unavailable for legal reasons'
    if soup_text == ' ':
        text = 'ERROR: 404 Page not found'
    if 'mediamatters.org' in url and 'clips' in url:
        text = "ERROR: Video/ Image content only"
    if 'theepochtimes.com' in url and 'epoch video' in soup_text.lower():
        text = "ERROR: Video/ Image content only"
    if 'chinadaily.com.cn' in url:
        text = soup_text
    if 'gmanetwork.com' in url or 'ecowatch' in url:
        text = 'ERROR: Not scrapable content'

    for n in e.empty_ptag_url_errors['404 Page not found']:
        if n in url:
            text = 'ERROR: 404 Page not found'

    for obj in e.empty_ptag_url_errors['Article has been archived']:
        if obj in url:
            text = "ERROR: Article has been archived"

    for nf in e.empty_ptag_text_errors['Article not found']:
        if nf in soup_text.lower():
            text = "ERROR: Article not found"

    for item in e.empty_ptag_url_errors['Article not found']:
        if item in url:
            text = "ERROR: Article not found"

    for elt in e.empty_ptag_text_errors['Blocked from website']:
        if elt in soup_text.lower():
            text = 'ERROR: Blocked from website'

    for x in e.empty_ptag_url_errors['Video/ Image content only']:
        if x in url:
            text = "ERROR: Video/ Image content only"

    return text


def try_alt_scrape_method(url, soup, response):
    if 'ynetnews.com' in url:
        span_elts = soup.find_all('span', attrs={'data-text': 'true'})
        stripped = [tag.get_text().strip() for tag in span_elts]
        return " ".join(stripped)
    if 'refinery29' in url:
        alt_elts = soup.find_all('div', attrs={'class': 'section-text'})
        stripped = [tag.get_text().strip() for tag in alt_elts]
        return " ".join(stripped)
    if 'cnbctv18.com' in url:
        tree = etree.HTML(response)
        elts = tree.xpath('//script[contains(@type,"application/ld+json")]')
        body_elts = [x for x in elts if 'articleBody' in x.text][0]
        json_vers = json.loads(str(body_elts.text))
        return json_vers['articleBody']
    if 'wral.com' in url:
        return 'ERROR: 404 Page not found'
    if 'kake' in url:
        return "ERROR: Video/ Image content only"
    if 'post-gazette.com' in url:
        return "ERROR: Article behind a paywall or login page"
    if 'grabien' in url:
        return "ERROR: Video/ Image content only"
    if 'israelnationalnews' in url:
        return 'ERROR: Article not found'
    if 'avoiceformen' in url:
        return "ERROR: Article not found"
    return "ERROR: No text gathered"


def handle_empty_ptags(url, soup, response):
    handled_errors = handle_errors_in_empty_ptags(url, soup.text)
    if handled_errors is not True:
        return handled_errors

    handle_text = try_alt_scrape_method(url, soup, response)
    return handle_text
