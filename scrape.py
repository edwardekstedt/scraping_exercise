"""
Author: Edward Ekstedt"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlsplit
import os
from multiprocessing.pool import ThreadPool



def get_response(url: str):
    """
    response wrapper to catch HTTP status code errors

    Parameters:
        url (str): URL to be requested

    Returns:
        response (requests.Response): the response object from the website
    """
    response = s.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Status code error: {str(response.status_code)} when trying to access : {url}"
        )
    return response



def download_html_page(soup: BeautifulSoup, url: str):
    """
    downloads a html-file to disk and creates a directory for it if it doesn't exist.

    Parameters:
        soup (BeatuifulSoup): soup object of the page
        url (str): url for the html page
    """
    if url.endswith("html"):
        filename = directory + urlsplit(url).path
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(soup.prettify())



def download(filename: str, response: requests.Response):
    """
    downloads a non-HTML file to disk

    Parameters:
        filename (str): filename of the file
        response (requests.Response): response containing the content to be saved
    """
    with open(filename, "wb") as f:
        f.write(response.content)



def parse_image(img_src: str, url: str):
    """
    parse the image, breaking the url up into the components necessary to save it at the proper relative path

    Parameters:
        img_src (str): image "src" object from html
        url (str): base url
    """
    absolute_url = urljoin(url, img_src)
    url_path = urlsplit(absolute_url).path
    relative_path = directory + url_path
    img_name = os.path.abspath(relative_path)
    img_path = os.path.dirname(img_name)
    if not os.path.exists(img_path):
        os.makedirs(img_path, exist_ok=True)
    if not os.path.isfile(img_name):
        download(img_name, get_response(absolute_url))



def parse_images(soup: BeautifulSoup, url: str):
    """
    wrapper for parsing images with multiple threads in a pool

    Parameters:
        soup (BeautifulSoup): soup object for the current page
        url (str): URL of the page
    """
    with ThreadPool() as pool:
        pool.starmap(
            parse_image, [(img["src"], url) for img in soup.find_all("img")]
        )



def parse_css(soup: BeautifulSoup, url: str):
    """
    parse the css files and download them to the local relative directory, so that all pages can access them

    Parameters:
        soup (BeautifulSoup): soup object for the current page
        url (str): URL of the page
    """
    for link in soup.find_all("link"):
        if not link.get("rel") or (
            link.get("rel")[0] != "stylesheet" and link.get("rel")[0] != "shortcut"
        ):
            #not interested if there's no rel tag, or if the rel tag is not a stylesheet or an icon
            continue
        css_src = link.get("href")
        absolute_url = urljoin(url, css_src)
        url_path = urlsplit(absolute_url).path
        relative_path = directory + url_path
        css_name = os.path.abspath(relative_path)
        css_path = os.path.dirname(css_name)
        if not os.path.exists(css_path):
            os.makedirs(css_path)
        if not os.path.isfile(css_name):
            download(css_name, get_response(absolute_url))



def parse_js(soup: BeautifulSoup, url: str):
    """
    Parse the javascript used in the html-page and download it. We are only interested in local links and will skip external libraries

    Parameters:
        soup (BeautifulSoup): soup object for the current page
        url (str): URL of the page
    """
    for script in soup.select("script"):
        if not script.get("src") or "http" in script.get("src"):
            #not interested if there's no src tag
            continue 
        js_src = script.get("src")
        absolute_url = urljoin(url, js_src)
        url_path = urlsplit(absolute_url).path
        relative_path = directory + url_path
        js_name = os.path.abspath(relative_path)
        js_path = os.path.dirname(js_name)
        if not os.path.exists(js_path):
            os.makedirs(js_path)
        if not os.path.isfile(js_name):
            download(js_name, get_response(absolute_url))


 
def get_links(link: dict, url: str):
    """
    Check if the link has already been found, if it hasn't add it to the dictionary and return the list of found links
    Parameters:
        link (dict): links to be checked
        url (str): URL of the page

    Returns:
        links (list): list of the links found
    """
    links = []
    link_str = link["href"]
    absolute_link = urljoin(url, link_str)
    if absolute_link not in dict_links_found:
        dict_links_found[absolute_link] = None
        links.append(absolute_link)
    return links



def get_links_of_page(url: str):
    """
    Get the HTML contents of the page, call the download function, parse the css, images and js files linked and find all links inside the HTML using a thread pool wrapper.

    Parameters:
        url (str): url of the page to be checked

    
    Returns:
        local_links (dict) dictionary of the local links found
    """
    response = get_response(url)
    soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
    links = []
    download_html_page(soup,url)
    parse_css(soup, url)
    parse_images(soup, url)
    parse_js(soup, url)
    with ThreadPool() as pool:
        for result in pool.starmap(
            get_links, [(link, url) for link in soup.find_all("a")]
        ):
            links += result
    local_links = dict.fromkeys(links, "Not parsed")

    return local_links



def crawl_thread(links: dict, current_link:str):
    """
    Crawl through pages that have not been parsed, then get the local links of the page and adds them to the dictionary


    Parameters:
        links (dict) : dictionary of links
        current_link (str) : current link to be checked

    Returns:
        links (dict) : dictionary of links updated with the found links in the local file
    """
    if links[current_link] == "Not parsed":
        local_links = get_links_of_page(current_link)
        links[current_link] = "Parsed"
    else:
        local_links = {}
    links = {**local_links, **links} #add the dictionaries together
    return links



def crawl(links: dict):
    """
    Wrapping the crawl method to be able to run it in a threadpool

    Parameters:
        links (dict) : Links that are already known to exist

    Returns:
        links (dict): Updated dictionary of links.
    """
    with ThreadPool() as pool:
        for result in pool.starmap(
            crawl_thread, [(links, link) for link in links]
        ):
            links = {**result, **links}

    return links


if __name__ == "__main__":
    s = requests.Session()
    website = "http://books.toscrape.com/"
    directory = "books"
    dict_links = {website: "Not parsed"}
    dict_links_found = {}
    unparsed_count, iterations = None, 0
    try:
        while unparsed_count != 0:
            iterations += 1
            dict_links_temp = crawl(dict_links)
            unparsed_count = sum(
                value == "Not parsed" for value in dict_links_temp.values()
            )
            print("")
            print(f"Loop iteration: {iterations}")
            print(f"Number of found links = {len(dict_links_temp)}")
            print(f"Number of found links currently not parsed = {unparsed_count}")
            print(("Percentage of found links parsed = {:2.2%} ").format((len(dict_links_temp)-unparsed_count)/len(dict_links_temp)))
            print("")
            dict_links = dict_links_temp
    except Exception as e:
        print(f"caught {e.args}")
    else:
        print(f"Scraping successful, located at {os.path.abspath(directory)}")
