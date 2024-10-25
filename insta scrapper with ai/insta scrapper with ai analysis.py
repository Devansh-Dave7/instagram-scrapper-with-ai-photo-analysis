import requests
from apify_client import ApifyClient
import os
import json
from urllib.parse import urlparse
from pathlib import Path
from google.cloud import vision
from google.cloud.vision_v1 import types
from typing import Tuple, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstagramScraper:
    def __init__(self, apify_token: str, credentials_path: str):
        """
        Initialize the scraper with API tokens and credentials.
        
        Args:
            apify_token: Apify API token
            credentials_path: Path to Google Cloud credentials JSON
        """
        self.client = ApifyClient(apify_token)
        self.vision_client = vision.ImageAnnotatorClient.from_service_account_json(credentials_path)
        
    def download_media(self, url: str, save_path: Path) -> bool:
        """
        Download media from URL and save to specified path.
        
        Args:
            url: URL of the media to download
            save_path: Path where the media should be saved
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()      
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            return True
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            return False

    @staticmethod
    def get_file_extension(url: str) -> str:
        """Get file extension from URL."""
        parsed = urlparse(url)
        path = parsed.path
        return os.path.splitext(path)[1].lower() or '.jpg'

    @staticmethod
    def create_download_directory(username: str) -> Tuple[Path, Path, Path]:
        """Create directory structure for downloads."""
        base_dir = Path(f'instagram_downloads/{username}')
        images_dir = base_dir / 'images'
        videos_dir = base_dir / 'videos'
        
        for dir_path in [base_dir, images_dir, videos_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        return base_dir, images_dir, videos_dir

    def analyze_images(self, image_paths: List[Path]) -> List[dict]:
        """
        Analyze images using Google Vision API.
        
        Args:
            image_paths: List of paths to images to analyze
            
        Returns:
            List of analysis results for each image
        """
        results = []
        
        for image_path in image_paths:
            try:
                with open(image_path, 'rb') as file:
                    content = file.read()
                    image = types.Image(content=content)
                    
                # Perform multiple types of analysis
                face_response = self.vision_client.face_detection(image=image)
                label_response = self.vision_client.label_detection(image=image)
                safe_search_response = self.vision_client.safe_search_detection(image=image)
                
                analysis = {
                    'image_path': str(image_path),
                    'faces': [],
                    'labels': [],
                    'safe_search': {}
                }
                
                # Process face detection results
                for face in face_response.face_annotations:
                    face_data = {
                        'joy': face.joy_likelihood.name,
                        'sorrow': face.sorrow_likelihood.name,
                        'anger': face.anger_likelihood.name,
                        'surprise': face.surprise_likelihood.name,
                        'confidence': face.detection_confidence
                    }
                    analysis['faces'].append(face_data)
                
                # Process label detection results
                analysis['labels'] = [
                    {'description': label.description, 'score': label.score}
                    for label in label_response.label_annotations
                ]
                
                # Process safe search results
                safe_search = safe_search_response.safe_search_annotation
                analysis['safe_search'] = {
                    'adult': safe_search.adult.name,
                    'violence': safe_search.violence.name,
                    'racy': safe_search.racy.name
                }
                
                results.append(analysis)
                logger.info(f"Successfully analyzed {image_path}")
                
            except Exception as e:
                logger.error(f"Error analyzing {image_path}: {str(e)}")
                results.append({'image_path': str(image_path), 'error': str(e)})
                
        return results

    def scrape_and_analyze(self, username: str, limit = int(input("Enter the no. of posts you want to scrape : "))) -> dict:
        """
        Main method to scrape Instagram posts and analyze images.
        
        Args:
            username: Instagram username to scrape
            limit: Maximum number of posts to scrape
            
        Returns:
            Dict containing scraping and analysis results
        """
        logger.info(f"Starting to scrape posts from {username}'s Instagram...")
        
        # Create directories
        base_dir, images_dir, videos_dir = self.create_download_directory(username)
        
        # Set up scraping parameters
        run_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsType": "posts",
            "resultsLimit": limit,
        }
        
        try:
            # Run the Instagram Scraper actor
            run = self.client.actor("apify/instagram-scraper").call(run_input=run_input)
            
            # Get dataset
            dataset_url = f'https://api.apify.com/v2/datasets/{run["defaultDatasetId"]}/items?format=json'
            response = requests.get(dataset_url, timeout=30)
            response.raise_for_status()
            
            # Save metadata
            metadata_path = base_dir / 'metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as file:
                json.dump(json.loads(response.content), file, indent=2)
            
            posts = json.loads(response.content)
            downloaded_images = []
            
            # Process posts
            for i, post in enumerate(posts, 1):
                try:
                    # Handle videos
                    if post.get('videoUrl'):
                        ext = self.get_file_extension(post['videoUrl'])
                        save_path = videos_dir / f"post_{i}{ext}"
                        if self.download_media(post['videoUrl'], save_path):
                            logger.info(f"Downloaded video {i}")
                    
                    # Handle single images
                    if post.get('displayUrl') and not post.get('videoUrl'):
                        ext = self.get_file_extension(post['displayUrl'])
                        save_path = images_dir / f"post_{i}{ext}"
                        if self.download_media(post['displayUrl'], save_path):
                            logger.info(f"Downloaded image {i}")
                            downloaded_images.append(save_path)
                    
                    # Handle carousel posts
                    if post.get('sidecarItems'):
                        for j, item in enumerate(post['sidecarItems'], 1):
                            if item.get('displayUrl') and not item.get('videoUrl'):
                                ext = self.get_file_extension(item['displayUrl'])
                                save_path = images_dir / f"post_{i}_carousel_{j}{ext}"
                                if self.download_media(item['displayUrl'], save_path):
                                    logger.info(f"Downloaded carousel image {j} from post {i}")
                                    downloaded_images.append(save_path)
                            elif item.get('videoUrl'):
                                ext = self.get_file_extension(item['videoUrl'])
                                save_path = videos_dir / f"post_{i}_carousel_{j}{ext}"
                                if self.download_media(item['videoUrl'], save_path):
                                    logger.info(f"Downloaded carousel video {j} from post {i}")
                
                except Exception as e:
                    logger.error(f"Error processing post {i}: {str(e)}")
                    continue
            
            # Analyze downloaded images
            analysis_results = self.analyze_images(downloaded_images)
            
            # Save analysis results
            analysis_path = base_dir / 'analysis_results.json'
            with open(analysis_path, 'w', encoding='utf-8') as file:
                json.dump(analysis_results, file, indent=2)
            
            return {
                'status': 'success',
                'base_directory': str(base_dir),
                'posts_processed': len(posts),
                'images_analyzed': len(analysis_results),
                'metadata_path': str(metadata_path),
                'analysis_path': str(analysis_path)
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_and_analyze: {str(e)}")
            return {'status': 'error', 'error': str(e)}

def main():
    # Configuration
    APIFY_TOKEN = 'Your_apify_api_key'
    CREDENTIALS_PATH = '/path/to/your/google vision api/file.json'
    USERNAME = input("Enter Username to scrape: ")
    
    # Initialize and run scraper
    scraper = InstagramScraper(APIFY_TOKEN, CREDENTIALS_PATH)
    results = scraper.scrape_and_analyze(USERNAME)
    
    if results['status'] == 'success':
        logger.info("Scraping and analysis completed successfully!")
        logger.info(f"Results saved in: {results['base_directory']}")
    else:
        logger.error(f"Process failed: {results['error']}")

if __name__ == "__main__":
    main()