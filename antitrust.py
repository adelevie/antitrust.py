# -*- coding: utf-8 -*-

import re
import os
import requests
import vcr
from bs4 import BeautifulSoup
from PyPDF2 import PdfFileWriter, PdfFileReader
import StringIO

index_url = "http://www.justice.gov/atr/cases/index.html"

@vcr.use_cassette('fixtures/vcr_cassettes/main.yaml', record_mode='new_episodes')
def case_urls_from_index_url(index_url):
    print index_url
    page = requests.get(index_url)
    soup = BeautifulSoup(page.text)
    case_urls = soup.find_all(
        "a", attrs={"href":re.compile("^/atr/cases/")})
    case_urls.pop(0)
    return case_urls

case_urls = case_urls_from_index_url(index_url)

@vcr.use_cassette('fixtures/vcr_cassettes/main.yaml', record_mode='new_episodes')
def case_filings_from_case_url(case_url):
    url = "http://www.justice.gov%s" % case_url.attrs["href"]
    print url
    page = requests.get(url)
    soup = BeautifulSoup(page.text)
    div = soup.find(
        "div", attrs={"class":"atr-bottom-left"})
    case_filings = div.find_all("a")
    return case_filings

def text_from_pdf_page(page):
    print page
    output = StringIO.StringIO()
    output.write(page.content)
    reader = PdfFileReader(output)
    pages = reader.pages
    text = map(lambda p: p.extractText(), pages)
    output.close()
    result = "".join(text)
    return "From a PDF"

@vcr.use_cassette('fixtures/vcr_cassettes/main.yaml', record_mode='new_episodes')
def case_filing_text_from_url(url):
    print url
    page = requests.get(url)
    page_text = None
    if url.endswith(".htm") or url.endswith(".html"):
        soup = BeautifulSoup(page.text)
        page_text = soup.body.text#.encode('utf-8')
    elif url.endswith(".pdf"):
        page_text = text_from_pdf_page(page)
    return page_text

def case_filing_text_to_xml(**kwargs):
    title = kwargs.get('title', "")
    case_name = kwargs.get('case_name', "")
    text = kwargs.get('text', "")
    result = """
    <document>
        <title>%s</title>
        <case_name>%s</case_name>
        <text>%s</text>
    </document>
    """ % (
        title, 
        case_name, 
        text
        )
    return result

@vcr.use_cassette('fixtures/vcr_cassettes/main.yaml', record_mode='new_episodes')
def save_text_from_case_filing(case_filing, **kwargs):
    case_name = kwargs.get('case_name', "No-Case-Name")
    filename = "%s-%s.xml" % (case_name.replace(" ", "-"), case_filing.text.replace(" ", "-"))
    path = os.path.join("documents", filename)
    with open(path, "w") as text_file:
        url = "http://www.justice.gov/atr/cases/%s" % case_filing.attrs["href"]
        case_filing_text = case_filing_text_from_url(url)
        title = case_filing.text
        xml = case_filing_text_to_xml(
            title=title, case_name=case_name, text=case_filing_text)
        text_file.write(xml.encode('utf-8'))

def scrape():
    for case_url in case_urls:
        case_filings = case_filings_from_case_url(case_url)
        case_name = case_url.text
        for case_filing in case_filings:
            save_text_from_case_filing(case_filing, case_name=case_name)

scrape()
