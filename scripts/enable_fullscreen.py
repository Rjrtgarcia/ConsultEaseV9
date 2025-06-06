#!/usr/bin/env python3
"""
Script to enable fullscreen mode for ConsultEase deployment on Raspberry Pi
This modifies the base window classes to enable fullscreen by default
"""

import os
import sys
import re
import glob
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the base path of ConsultEase
if len(sys.argv) > 1:
    base_path = sys.argv[1]
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger.info(f"Using base path: {base_path}")

# Views directory
views_dir = os.path.join(base_path, 'central_system', 'views')

def find_window_files():
    """Find all window class files in the views directory."""
    return glob.glob(os.path.join(views_dir, '*_window.py'))

def enable_fullscreen(file_path):
    """Enable fullscreen for a window class file.
    
    Args:
        file_path: Path to the window class file
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Check for commented fullscreen line
    fullscreen_pattern = r'# *self\.showFullScreen\(\)'
    
    if re.search(fullscreen_pattern, content):
        # Replace commented fullscreen line with active line
        modified_content = re.sub(
            fullscreen_pattern,
            'self.showFullScreen()',
            content
        )
        
        # Write modified content back to file
        with open(file_path, 'w') as file:
            file.write(modified_content)
        
        return True
    
    # If no commented line was found, check if fullscreen is already enabled
    if 'self.showFullScreen()' in content:
        logger.info(f"Fullscreen already enabled in {os.path.basename(file_path)}")
        return False
    
    # Otherwise, add fullscreen after window initialization
    # Look for common setup patterns
    patterns = [
        r'(self\.setWindowTitle\([^)]+\))',
        r'(self\.resize\([^)]+\))',
        r'(self\.move\([^)]+\))',
        r'(self\.show\(\))'
    ]
    
    for pattern in patterns:
        if re.search(pattern, content):
            modified_content = re.sub(
                pattern,
                r'\1\n        self.showFullScreen()',
                content,
                count=1
            )
            
            # Write modified content back to file
            with open(file_path, 'w') as file:
                file.write(modified_content)
            
            return True
    
    logger.warning(f"Could not find a suitable place to add fullscreen in {os.path.basename(file_path)}")
    return False

def main():
    """Main function to enable fullscreen for all window classes."""
    logger.info("Enabling fullscreen mode for ConsultEase windows")
    
    window_files = find_window_files()
    if not window_files:
        logger.error(f"No window files found in {views_dir}")
        return 1
    
    logger.info(f"Found {len(window_files)} window files")
    
    modified_count = 0
    for file_path in window_files:
        filename = os.path.basename(file_path)
        if enable_fullscreen(file_path):
            logger.info(f"Enabled fullscreen mode in {filename}")
            modified_count += 1
        else:
            logger.info(f"No changes needed for {filename}")
    
    logger.info(f"Modified {modified_count} out of {len(window_files)} window files")
    
    if modified_count > 0:
        logger.info("Fullscreen mode has been enabled. Restart ConsultEase to apply changes.")
    else:
        logger.info("No changes were made. Fullscreen mode might already be enabled.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 