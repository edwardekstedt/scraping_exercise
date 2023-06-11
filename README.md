# scrape.py

scrape.py is a python program which scrapes and downloads all the content from [books.toscrape](http://books.toscrape.com). The program parses the given root URL and notes all css, js, html, and images. These are all downloaded and put in the same folder structure as the website uses.
The program recursively traverses all the html links until there are no links which remain unparsed and undownloaded. By use of the multiprocessing library several parts of the page can be traversed simultaneously, significantly speeding up the process. 

The program outputs the current iteration and the amounts of links found, as well as how many of the found links that have been parsed.

## Requirements
The code depends on the packages requests, beautifulsoup, urllib, and multiprocessing.

```python
pip install requests
pip install urllib3
pip install beautifulsoup4
```
## Installation

Clone this git repository.
```bash
https://github.com/edwardekstedt/scraping_exercise.git
```
## Usage

```python
python3 scrape.py
```

## Known issues
The program does not manage to get the html tag <i> to properly display in the downloaded page. 

## Future work
The functions that parse the css and js pages can be combined into a single help function with slightly different calls. 