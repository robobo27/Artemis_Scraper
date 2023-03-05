#! /usr/bin/env python

import requests
import bs4
from bs4 import BeautifulSoup
import csv
import re

class Blog():
    def __init__(self, title=None, header=None, content=None, footer=None, externalLink=None, datePublished=None, dateUpdated=None):
        self.title = title
        self.header = header
        self.content = content
        self.footer = footer
        self.externalLink = externalLink
        self.datePublished = datePublished
        self.dateUpdated = dateUpdated

"""
site contents are:
<div id="content" class="site-content">
    <div id="primary" class="content-area">
        <main id="main" class="site-main">
            <article id="post-1993" class="post-1993...>
                <header class="entry-header">
                    <h2 class="entry-title">
                    </h2>
                </header>
                <div class="entry-content">
                    <p>
                    </p>
                </div>
                <footer class="entry-footer">
                    <span class="posted-on">
                        <a> href="https://blogs.nasa.gov/artemis/2023/02/09/title/"
                </footer>
            </article>
    </div>
</div>
"""
# Parses the artemis URL give. Returns the blogs and the next page URL to parse, if there is one
# Returns Blogs, nextUrl
def parse_artemis(url=None):
    nextUrl = None
    entryTitle = None
    entryContent = None
    entryExternalLink = None
    entryPublishDate = None
    entryUpdateDate = None
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    mainContent = soup.find_all(id="main")
    articles = mainContent[0].contents
    blogs = []
    for entry in articles:
        # find just the article entries, the nav tag is for the next url page
        if type(entry) is bs4.element.Tag and entry.name != 'nav':
            if entry.find(class_="entry-title"):
                # Make this more human readable and allow csv output ot happen without yelling about formatting
                entryTitle = re.sub('[^A-Za-z0-9]+.* \\n.*\(\).*\..*-.*,.*"+', '', entry.find(class_="entry-title").text)
                # Weird formatting csv doesn't like
                entryTitle = entryTitle.replace('\u202f',' ')
                if entry.find(class_="entry-title").find("a"):
                    entryExternalLink = entry.find(class_="entry-title").find("a").attrs["href"]
            if entry.find(class_="entry-content"):
                # Make this more human readable and allow csv output ot happen without yelling about formatting
                entryContent = re.sub('[^A-Za-z0-9]+.* \\n.*\(\).*\..*-.*,.*"+', '', entry.find(class_="entry-content").text.strip())
                # Weird formatting csv doesn't like
                entryContent = entryContent.replace('\u202f',' ')
            if entry.find(class_="entry-footer"):
                if entry.find(class_="entry-footer").find(class_="posted-on"):
                    entryPublishDate = entry.find(class_="entry-footer").find(class_="posted-on").text
                    if entry.find(class_="entry-footer").find(class_="posted-on").find(class_="entry-date published"):
                        entryPublishDate = entry.find(class_="entry-footer").find(class_="posted-on").find(class_="entry-date published").text
                        if entry.find(class_="entry-footer").find(class_="posted-on").find(class_="updated"):
                            entryUpdateDate = entry.find(class_="entry-footer").find(class_="posted-on").find(class_="updated").text
            if entryTitle and entryContent and entryExternalLink:
                blogs.append(Blog(title=entryTitle, content=entryContent, externalLink=entryExternalLink, datePublished=entryPublishDate, dateUpdated=entryUpdateDate))
            else:
                print("did not find everything. Currently have\n Title %s\nContent: %s\nExternalLink: %s" %(entryTitle,entryContent,entryExternalLink))
        # find the next page to process
        if type(entry) is bs4.element.Tag and entry.name == 'nav':
            pages = []
            navSection = entry.find(class_="nav-links")
            currentPage = navSection.find(class_="page-numbers current").text.strip("Page ")
            for i in navSection.find_all("a", class_="page-numbers"):
                if("Next" not in i.text):
                    pages.append(i)
            print("Current Page %s Last page %s" % (currentPage,pages[-1].text.strip("Page ")))
            if int(currentPage) < int(pages[-1].text.strip("Page ")):
                nextUrl = "https://blogs.nasa.gov/artemis/page/%s/" % (int(currentPage) + 1)

    print("found %s blogs on page %s" % (len(blogs), currentPage))
    return blogs, nextUrl

if __name__ == "__main__":
    url = "https://blogs.nasa.gov/artemis/"
    blogs = []
    while url != None:
        blog, url = parse_artemis(url)
        for entry in blog:
            blogs.append(entry)
    with open("results.csv", "w", newline="") as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=",")
        csvWriter.writerow(["Title","Content","Date Published","Date Updated","Link"])
        for entry in blogs:
            csvWriter.writerow([entry.title,entry.content,entry.datePublished,entry.dateUpdated,entry.externalLink])
