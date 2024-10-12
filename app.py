from flask import Flask, render_template, request, Response, send_file
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import io

app = Flask(__name__)
results = []  # Declare a global variable to store results

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

        # # Extract from <script> tags with src attributes
        # for tag in soup.find_all('script', src=True):
        #     links.append(urljoin(url, tag['src']))

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
    global results
    results = []  # Reset results for each crawl
    dead_links = []  # List to store dead links

    base_url = request.form['url']
    visited_pages = set()
    links_checked = set()
    queue = [base_url]

    def generate():
        while queue:
            current_page = queue.pop(0)

            if current_page in visited_pages:
                continue

            visited_pages.add(current_page)
            links, page_status = extract_links_from_page(current_page)
            page_info = f"Page: {current_page} - Status: {page_status}\n"
            yield f"data:{page_info}\n\n"
            results.append(page_info)

            if page_status == 200:
                for link in links:
                    if link not in links_checked:
                        link_status = check_link_status(link)
                        link_info = f"    {link} - Status: {link_status if link_status else 'Could not retrieve'}\n"
                        yield f"data:{link_info}\n\n"
                        results.append(link_info)
                        links_checked.add(link)

                        if link_status != 200:
                            dead_links.append(link_info)

                        if link_status == 200 and is_internal_link(link, base_url):
                            queue.append(link)

        # Add dead links summary at the beginning of the results
        if dead_links:
            dead_links_summary = "Dead Links:\n" + "".join(dead_links) + "\n\n"
            results.insert(0, dead_links_summary)

        # Signal the end of crawling
        yield f"data:done\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/download')
def download():
    global results
    output = io.BytesIO()
    output.write("".join(results).encode('utf-8'))  # Encode the text to bytes
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='results.txt', mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5009)
