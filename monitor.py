"""Core monitoring service for website content checking."""
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

def check_website(job: Dict) -> Dict:
    """
    Perform a website check for a monitoring job.
    
    Args:
        job: Dictionary containing job configuration with keys:
            - id: Job ID
            - url: URL to check
            - match_type: 'string' or 'regex'
            - match_pattern: Pattern to search for
            - match_condition: 'contains' or 'not_contains'
    
    Returns:
        Dictionary with keys:
            - success: Boolean indicating if check succeeded
            - match_found: Boolean indicating if pattern was found
            - response_time: Time taken for request in seconds
            - error_message: Error message if check failed
            - content_length: Length of content checked
    """
    start_time = time.time()
    result = {
        'success': False,
        'match_found': False,
        'response_time': 0,
        'error_message': None,
        'content_length': 0
    }
    
    try:
        # Fetch the website
        headers = {
            'User-Agent': Config.USER_AGENT
        }
        
        response = requests.get(
            job['url'],
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text_content = soup.get_text()
        
        # Clean up whitespace
        text_content = ' '.join(text_content.split())
        
        result['content_length'] = len(text_content)
        result['success'] = True
        
        # Check for pattern match
        match_found = False
        
        if job['match_type'] == 'string':
            # Simple string search (case-insensitive)
            pattern = job['match_pattern'].lower()
            content_lower = text_content.lower()
            match_found = pattern in content_lower
        elif job['match_type'] == 'regex':
            # Regex pattern matching
            try:
                pattern = re.compile(job['match_pattern'], re.IGNORECASE | re.DOTALL)
                match_found = bool(pattern.search(text_content))
            except re.error as e:
                result['error_message'] = f"Invalid regex pattern: {str(e)}"
                result['success'] = False
                return result
        
        # Apply match condition
        if job['match_condition'] == 'contains':
            result['match_found'] = match_found
        elif job['match_condition'] == 'not_contains':
            result['match_found'] = not match_found
        
    except requests.exceptions.Timeout:
        result['error_message'] = f"Request timeout after {Config.REQUEST_TIMEOUT} seconds"
        logger.warning(f"Timeout checking {job['url']}")
    except requests.exceptions.ConnectionError as e:
        result['error_message'] = f"Connection error: {str(e)}"
        logger.warning(f"Connection error checking {job['url']}: {e}")
    except requests.exceptions.HTTPError as e:
        result['error_message'] = f"HTTP error {response.status_code}: {str(e)}"
        logger.warning(f"HTTP error checking {job['url']}: {e}")
    except Exception as e:
        result['error_message'] = f"Unexpected error: {str(e)}"
        logger.error(f"Error checking {job['url']}: {e}", exc_info=True)
    finally:
        result['response_time'] = time.time() - start_time
    
    return result
