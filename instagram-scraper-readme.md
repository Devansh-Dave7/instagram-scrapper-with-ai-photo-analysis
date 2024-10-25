# Instagram Media Scraper and Analyzer

A Python-based tool that scrapes Instagram posts, downloads media (images and videos), and performs image analysis using Google Cloud Vision API. This tool can analyze faces, detect labels, and perform safe search detection on downloaded images.

## Features

- Scrapes Instagram posts from specified user profiles
- Downloads both images and videos from posts
- Handles carousel posts (multiple media items)
- Performs comprehensive image analysis using Google Cloud Vision API:
  - Face detection with emotion analysis
  - Label detection
  - Safe search detection
- Saves all metadata and analysis results in JSON format
- Organized directory structure for downloaded media
- Detailed logging system

## Prerequisites

- Python 3.6+
- Apify API token
- Google Cloud Vision API credentials

## Required Libraries

```bash
pip install requests
pip install apify-client
pip install google-cloud-vision
```

## Configuration

Before running the script, you need to set up:

1. Apify API token
2. Google Cloud Vision API credentials

Update these values in the `main()` function:

```python
APIFY_TOKEN = 'Your_apify_api_key'
CREDENTIALS_PATH = '/path/to/your/google vision api/file.json'
```

## Directory Structure

The script creates the following directory structure for each scraped profile:

```
instagram_downloads/
└── {username}/
    ├── images/
    │   └── post_*.{extension}
    ├── videos/
    │   └── post_*.{extension}
    ├── metadata.json
    └── analysis_results.json
```

## Usage

1. Run the script:
```bash
python code_red.py
```

2. Enter the Instagram username when prompted
3. Specify the number of posts to scrape when prompted

## Output Files

- `metadata.json`: Contains raw data from Instagram posts
- `analysis_results.json`: Contains Google Vision API analysis results for downloaded images
- Downloaded media files are saved in their respective directories with sequential naming

## Analysis Features

### Face Detection
- Joy likelihood
- Sorrow likelihood
- Anger likelihood
- Surprise likelihood
- Detection confidence

### Label Detection
- Object and scene labels
- Confidence scores

### Safe Search Detection
- Adult content detection
- Violence detection
- Racy content detection

## Error Handling

- Comprehensive error handling for network issues
- Detailed logging system for debugging
- Graceful handling of failed downloads and analysis

## Limitations

- Requires valid Instagram profile URLs
- Subject to Instagram's rate limiting and access restrictions
- Depends on Apify's Instagram scraper functionality
- Image analysis costs may apply (Google Cloud Vision API usage)

## Security Notes

- Store API credentials securely
- Do not commit API tokens to version control
- Follow Instagram's terms of service and usage guidelines
- Respect user privacy and data protection regulations

## Contributing

Feel free to submit issues and enhancement requests.

## License

[Add your chosen license here]

## Disclaimer

This tool is for educational purposes only. Ensure you have the right to download and analyze the content you're targeting. Follow Instagram's terms of service and respect copyright and privacy rights.
