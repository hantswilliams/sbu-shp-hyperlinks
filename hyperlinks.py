import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import sys
import os

def extract_links_from_page(url):
    """Extracts all hyperlinks from a given page's HTML content."""
    try:
        response = requests.get(url)
        # Only proceed if the page returned a 200 status
        if response.status_code != 200:
            return [], response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')
        links = []

        # Extract from <a> tags with href attributes
        for tag in soup.find_all('a', href=True):
            links.append(urljoin(url, tag['href']))

        # Extract from <link> tags with href attributes
        for tag in soup.find_all('link', href=True):
            links.append(urljoin(url, tag['href']))

        # Extract from <script> tags with src attributes
        for tag in soup.find_all('script', src=True):
            links.append(urljoin(url, tag['src']))

        # Extract from <img> tags with src attributes
        for tag in soup.find_all('img', src=True):
            links.append(urljoin(url, tag['src']))

        # Extract from <iframe> tags with src attributes
        for tag in soup.find_all('iframe', src=True):
            links.append(urljoin(url, tag['src']))

        return links, response.status_code

    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [], None

def is_internal_link(link, base_url):
    """Checks if the link is within the same domain as the base URL."""
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    return link_domain == base_domain

def check_link_status(url):
    """Checks the status of an individual link."""
    try:
        response = requests.get(url)
        return response.status_code
    except requests.RequestException:
        return None

def crawl_website(base_url, output_file):
    """Crawls the website starting from the base URL, checks status, and follows internal links."""
    visited_pages = set()
    links_checked = set()
    queue = deque([base_url])
    results = []
    dead_links = []  # List to store dead links

    # Crawl and collect data
    while queue:
        current_page = queue.popleft()

        # Skip already visited pages
        if current_page in visited_pages:
            continue

        visited_pages.add(current_page)

        # Extract links if page is accessible
        links, page_status = extract_links_from_page(current_page)
        page_info = f"Page: {current_page} - Status: {page_status}"
        print(page_info)
        results.append(page_info + "\n")

        # Only proceed to link checks if page status is 200
        if page_status == 200:
            for link in links:
                if link not in links_checked:
                    link_status = check_link_status(link)
                    link_info = f"    {link} - Status: {link_status if link_status else 'Could not retrieve'}"
                    print(link_info)
                    results.append(link_info + "\n")
                    links_checked.add(link)

                    # Track dead links separately
                    if link_status != 200:
                        dead_links.append(link_info + "\n")

                    # Queue new internal pages for crawling
                    if link_status == 200 and is_internal_link(link, base_url):
                        queue.append(link)

        results.append("\n")

    # Write results to the output file, starting with dead links summary
    with open(output_file, 'w') as file:
        if dead_links:
            file.write("Dead Links:\n")
            file.writelines(dead_links)
            file.write("\n\n")

        file.writelines(results)

def main():
    # Check for URL argument
    if len(sys.argv) != 2:
        print("Usage: python link_checker.py <URL>")
        sys.exit(1)

    base_url = sys.argv[1]
    # Generate filename based on the base URL's hostname
    parsed_url = urlparse(base_url)
    output_file_name = f"{parsed_url.netloc.replace('.', '_')}_results.txt"

    print(f"Starting crawl on {base_url}...\n")
    print(f"Results will be saved to {output_file_name}\n")

    crawl_website(base_url, output_file_name)

if __name__ == "__main__":
    main()
