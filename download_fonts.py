import os
import requests

# Create webfonts directory if it doesn't exist
webfonts_dir = 'proj/static/proj/webfonts'
os.makedirs(webfonts_dir, exist_ok=True)

# Font Awesome GitHub raw URLs
font_urls = {
    'fa-solid-900.woff2': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-solid-900.woff2',
    'fa-solid-900.woff': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-solid-900.woff',
    'fa-solid-900.ttf': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-solid-900.ttf',
    'fa-brands-400.woff2': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-brands-400.woff2',
    'fa-brands-400.woff': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-brands-400.woff',
    'fa-brands-400.ttf': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-brands-400.ttf',
    'fa-regular-400.woff2': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-regular-400.woff2',
    'fa-regular-400.woff': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-regular-400.woff',
    'fa-regular-400.ttf': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.4.0/webfonts/fa-regular-400.ttf',
}

# Download each font file
for filename, url in font_urls.items():
    print(f'Downloading {filename}...')
    response = requests.get(url)
    if response.status_code == 200:
        filepath = os.path.join(webfonts_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f'Successfully downloaded {filename}')
    else:
        print(f'Failed to download {filename}. Status code: {response.status_code}')

print('\nDownload complete!') 