from flask import Flask, render_template, request, Response, send_file, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import io
import pandas as pd

app = Flask(__name__)
results = []  # Declare a global variable to store results
cancel_crawl = False  # Flag to cancel the crawl

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

        # Extract from <img> tags with src attributes
        for tag in soup.find_all('img', src=True):
            links.append(urljoin(url, tag['src']))

        # Extract from <iframe> tags with src attributes
        for tag in soup.find_all('iframe', src=True):
            links.append(urljoin(url, tag['src']))

        return links, response.status_code

    except requests.RequestException as e:
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    global results, cancel_crawl
    results = []  # Reset results for each crawl
    cancel_crawl = False  # Reset the cancel flag

    base_url = request.form['url']
    visited_pages = set()
    queue = [base_url]

    def generate():
        global cancel_crawl
        while queue:
            if cancel_crawl:
                break  # Stop the crawl if cancel_crawl flag is True

            current_page = queue.pop(0)
            if current_page in visited_pages:
                continue

            visited_pages.add(current_page)
            links, page_status = extract_links_from_page(current_page)
            page_info = (current_page, page_status, [])  # Store page URL, status, and list for links
            yield f"data:Page: {current_page} - Status: {page_status}\n\n"
            
            if page_status == 200:
                for link in links:
                    if cancel_crawl:
                        break  # Stop processing links if cancelled

                    link_status = check_link_status(link)
                    link_info = (link, link_status if link_status else 'Could not retrieve')
                    yield f"data:    {link} - Status: {link_info[1]}\n"
                    page_info[2].append(link_info)

                    # Add internal links to the queue
                    if link_status == 200 and is_internal_link(link, base_url) and link not in visited_pages:
                        queue.append(link)

            results.append(page_info)  # Append the page info to results

        # Signal the end of crawling
        yield f"data:done\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/results_table')
def results_table():
    global results

    # Flatten the results into a list of dictionaries, so each row has a 'Source', 'URL', and 'Status'
    data = []
    for page_url, page_status, links in results:
        # Add the page itself as a row
        data.append({'Source': 'Page', 'URL': page_url, 'Status': page_status})
        
        # Add each link found on the page
        for link_url, link_status in links:
            data.append({'Source': f'Link from {page_url}', 'URL': link_url, 'Status': link_status})

    # Return data as JSON
    return jsonify(data)


@app.route('/download')
def download():
    global results
    output = io.BytesIO()
    
    # Prepare the text output with the structure: page -> links found on page
    for page_url, page_status, links in results:
        output.write(f"Page: {page_url} - Status: {page_status}\n".encode('utf-8'))
        for link_url, link_status in links:
            output.write(f"    {link_url} - Status: {link_status}\n".encode('utf-8'))
        output.write("\n".encode('utf-8'))  # Add a blank line after each page block
    
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='results.txt', mimetype='text/plain')

@app.route('/cancel', methods=['POST'])
def cancel():
    global cancel_crawl
    cancel_crawl = True  # Set the cancel flag to True
    return "Crawl cancelled", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009)
