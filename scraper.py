import os
import requests
from bs4 import BeautifulSoup
import zipfile
import json

# Default settings
DEFAULT_NUM_PAGES = 10
DEFAULT_OUTPUT_FOLDER = './allfonts/'
DEFAULT_TAGS = ['sans-serif']  # Default tag is 'sans-serif'

def setup_output_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def download_and_unzip(url, font_name, output_folder):
    response = requests.get(url)
    zip_path = os.path.join(output_folder, f"{font_name}.zip")

    # Write the zip file to the folder
    with open(zip_path, 'wb') as zip_file:
        zip_file.write(response.content)

    # Unzip the contents directly into the allfonts folder
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        extracted_files = []
        for file in zip_ref.namelist():
            # Avoid overwriting by prefixing the font_name to the filename
            extracted_filename = f"{font_name}_{os.path.basename(file)}"
            extracted_path = os.path.join(output_folder, extracted_filename)
            with open(extracted_path, 'wb') as output_file:
                output_file.write(zip_ref.read(file))
            extracted_files.append(extracted_filename)

    return extracted_files

def scrape_font_page(font_url):
    response = requests.get(font_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract font name, tags, and download link
    font_name = soup.find('h1', class_='font-name').text
    download_link = soup.find('a', class_='btn-download')['href']

    # Extract tags
    tags = [tag.text.strip() for tag in soup.select('.react-tag-root .tags__list-item')]

    # Extract legal use type
    if soup.find('a', class_='badge--license-yes'):
        legal_use_type = 'free for commercial use'
    else:
        legal_use_type = 'free for personal use'

    return {
        'font_name': font_name,
        'download_link': download_link,
        'tags': tags,
        'legal_use_type': legal_use_type
    }

def scrape_fonts(tags=DEFAULT_TAGS, num_pages=DEFAULT_NUM_PAGES, output_folder=DEFAULT_OUTPUT_FOLDER):
    setup_output_folder(output_folder)
    fonts_collection = {'fonts': []}

    # Iterate over each specified tag
    for tag in tags:
        print(f"Scraping tag: {tag}")
        for page in range(1, num_pages + 1):
            # Construct the URL based on the tag and page number
            url = f"https://www.1001fonts.com/{tag}-fonts.html?page={page}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Scrape all font links
            font_links = [a['href'] for a in soup.select('.preview-link.txt-preview-wrapper')]

            for font_link in font_links:
                font_data = scrape_font_page(f"https://www.1001fonts.com{font_link}")
                font_name = font_data['font_name']

                # Download font and unzip it (store directly in /allfonts folder)
                font_files = download_and_unzip(font_data['download_link'], font_name, output_folder)
                font_data['files'] = font_files
                font_data['custom_tags'] = []

                # Add the font data to the collection
                fonts_collection['fonts'].append(font_data)

    # Save the collection to a JSON file
    with open(os.path.join(output_folder, 'collection.json'), 'w') as json_file:
        json.dump(fonts_collection, json_file, indent=4)

# Run the scraper with default settings
if __name__ == '__main__':
    scrape_fonts()