# -*- coding: utf-8 -*-
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException
)
from bs4 import BeautifulSoup, Tag
import pandas as pd
from urllib.parse import urljoin, urlparse, parse_qs # Ensure parse_qs is imported
import traceback
from datetime import datetime
import re
import logging
import os # Ensure os is imported

# --- Configuration ---
TARGET_URL = 'https://www.espncricinfo.com/records/trophy/indian-premier-league-117'

# Output directory for logs and CSV file
OUTPUT_DIR = "Team_code_output" # Directory to save output files
os.makedirs(OUTPUT_DIR, exist_ok=True) # Create directory if it doesn't exist

# CSV file name
CSV_FILENAME = os.path.join(OUTPUT_DIR, 'team_code.csv') # Construct full path for CSV

# --- Logging Setup ---
log_filename = os.path.join(OUTPUT_DIR, f"ipl_team_list_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)

logging.info(f"Log file: {log_filename}")
logging.info(f"CSV Output file: {CSV_FILENAME}") # Log the CSV filename
logging.info(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Target URL: {TARGET_URL}")

# --- Helper Functions ---
def safe_get_text(element, default='N/A'):
    """Safely extracts text from a BeautifulSoup Tag or returns the string itself."""
    if isinstance(element, Tag):
        text = element.get_text(strip=True)
        return text if text else default
    elif isinstance(element, str):
        return element.strip()
    return default

def extract_team_id_from_url(url_str):
    """Extracts the 'team' query parameter value from a URL string."""
    team_id = 'N/A'
    if not isinstance(url_str, str) or url_str == 'N/A':
        return team_id
    try:
        parsed_url = urlparse(url_str)
        query_params = parse_qs(parsed_url.query)
        team_id_list = query_params.get('team', []) # Get list of values for 'team'
        if team_id_list:
            team_id = team_id_list[0] # Take the first value
    except Exception as e:
        logging.warning(f"Could not parse team ID from URL '{url_str}': {e}")
    return team_id

# --- Driver Setup ---
def setup_driver():
    """Sets up and returns the undetected_chromedriver instance."""
    driver = None
    retries = 3
    last_exception = None
    for attempt in range(retries):
        logging.info(f"Attempting to initialize WebDriver (Attempt {attempt + 1}/{retries})...")
        try:
            options = uc.ChromeOptions()
            # options.add_argument('--headless=new') # Uncomment for headless mode
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument('--log-level=3') # Suppress console logs from Chrome/WebDriver
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--window-size=1920,1080")
            # Common user agent string
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

            driver = uc.Chrome(options=options, enable_cdp_events=True, version_main=None) # version_main=None lets uc detect version
            logging.info("Browser driver setup successful.")
            return driver
        except Exception as e:
            last_exception = e
            logging.warning(f"Failed WebDriver init attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                logging.info("Retrying after 5 seconds...")
                time.sleep(5)
            else:
                logging.error("Max retries reached for WebDriver init.")
                raise last_exception # Re-raise the last exception if all retries fail
    # This part should ideally not be reached if setup succeeds or raises an exception
    if driver is None and last_exception:
        raise last_exception
    return driver # Should return the driver if successful

# --- Main Scraping Logic ---
if __name__ == "__main__":
    overall_start_time = time.time()
    driver = None
    team_data_list = []

    try:
        driver = setup_driver()
        logging.info(f"Navigating to target URL: {TARGET_URL}")
        driver.get(TARGET_URL)

        # --- Wait for the specific list container element ---
        # Using the user-provided selector (might be fragile)
        list_selector = "#main-container > div.ds-relative > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-grid.ds-grid-cols-3.ds-gap-2 > div:nth-child(2) > div:nth-child(1) > div.ds-p-0 > div:nth-child(1) > div > div.ReactCollapse--collapse > div > div > ul"
        # Consider more robust selectors if possible (e.g., using data-testid attributes if they exist)
        # list_selector = "div[data-testid='some-unique-id-for-list'] ul" # Example

        wait_time = 30
        logging.info(f"Waiting up to {wait_time}s for team list UL ('{list_selector}')...")

        try:
            # Wait for the UL element to be present in the DOM
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, list_selector))
            )
            logging.info("Team list UL found in DOM.")
            # Add a small delay in case content loads slightly after the element appears
            time.sleep(2)
        except TimeoutException:
            logging.error(f"Timed out waiting for the team list UL using selector: {list_selector}")
            # Save page source for debugging if the element is not found
            debug_filename = os.path.join(OUTPUT_DIR, f"debug_team_list_timeout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            try:
                with open(debug_filename, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logging.info(f"Saved page HTML for debugging list timeout to {debug_filename}")
            except Exception as save_err:
                logging.error(f"Failed to save debug HTML: {save_err}")
            raise # Re-raise the exception to stop the script if the list isn't found

        # --- Parse the page and extract data ---
        page_soup = BeautifulSoup(driver.page_source, 'lxml') # Using lxml parser
        team_list_ul = page_soup.select_one(list_selector)

        if not team_list_ul:
            logging.error(f"Could not select team list UL ('{list_selector}') from parsed HTML even after waiting.")
            # Optionally save HTML again if parsing failed after successful wait
            debug_filename_parse = os.path.join(OUTPUT_DIR, f"debug_team_list_parse_fail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            try:
                with open(debug_filename_parse, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                logging.info(f"Saved page HTML for debugging parse failure to {debug_filename_parse}")
            except Exception as save_err:
                logging.error(f"Failed to save debug HTML on parse fail: {save_err}")
        else:
            # Find all direct list item children (li) of the UL
            list_items = team_list_ul.find_all('li', recursive=False)
            logging.info(f"Found {len(list_items)} list items in the UL.")

            processed_count = 0
            for item in list_items:
                link_tag = item.find('a', href=True) # Find the anchor tag within the list item
                if link_tag:
                    try:
                        # Extract Team Name (look for a span first, fallback to link text)
                        team_name_span = link_tag.find('span')
                        team_name = safe_get_text(team_name_span if team_name_span else link_tag, 'Unknown Team')

                        # Extract href attribute
                        href = link_tag.get('href')
                        # Make URL absolute (useful for context, though not strictly needed for ID)
                        absolute_url = urljoin(TARGET_URL, href)

                        # Extract Team ID from the href using the helper function
                        team_id = extract_team_id_from_url(href)

                        # Validate extracted data before adding
                        if team_name != 'Unknown Team' and team_id != 'N/A':
                            team_data_list.append({
                                'Team Name': team_name,
                                'Team ID': team_id
                                # 'URL': absolute_url # Optional: uncomment to include URL
                            })
                            processed_count += 1
                            # logging.info(f"Extracted: Name='{team_name}', ID='{team_id}'") # Verbose logging if needed
                        else:
                            logging.warning(f"Skipping entry: Could not extract valid name/ID. Name='{team_name}', ID='{team_id}', URL='{href}'")

                    except Exception as e_item:
                        logging.error(f"Error processing list item: {e_item}", exc_info=True)
                        logging.debug(f"Problematic list item HTML: {item}") # Log the HTML of the failing item
                else:
                    logging.warning(f"List item found without an anchor tag (<a>): {item}")

            logging.info(f"Successfully extracted data for {processed_count} teams.")

    except WebDriverException as e_wd:
        logging.critical(f"A WebDriver error occurred: {e_wd}", exc_info=True)
    except Exception as e_main:
        logging.critical(f"An unexpected error occurred during scraping: {e_main}", exc_info=True)
    finally:
        # --- Quit Driver ---
        if driver:
            try:
                logging.info("Quitting WebDriver...")
                driver.quit()
                logging.info("Browser closed.")
            except Exception as quit_err:
                logging.error(f"Error closing browser: {quit_err}")

        # --- Process Data, Print, and Save to CSV ---
        logging.info("\n" + "="*20 + " Processing and Saving Data " + "="*20)
        if team_data_list:
            try:
                # Create DataFrame
                team_df = pd.DataFrame(team_data_list)

                # --- Print DataFrame to console ---
                print(f"\n--- Extracted Team Data ({len(team_df)} entries) ---")
                pd.set_option('display.max_rows', None)    # Show all rows
                pd.set_option('display.max_columns', None) # Show all columns
                pd.set_option('display.width', 2000)     # Set wide display for console
                print(team_df.to_string(index=False)) # Use to_string for better console output without index

                # --- Save DataFrame to CSV ---
                try:
                    logging.info(f"Attempting to save data to CSV: {CSV_FILENAME}")
                    # Save the DataFrame to CSV, without the index, using UTF-8 encoding
                    team_df.to_csv(CSV_FILENAME, index=False, encoding='utf-8')
                    logging.info(f"Successfully saved team data to {CSV_FILENAME}")
                except IOError as e_io:
                    logging.error(f"Error saving data to CSV file '{CSV_FILENAME}': {e_io}", exc_info=True)
                except Exception as e_csv:
                    logging.error(f"An unexpected error occurred while saving to CSV: {e_csv}", exc_info=True)

            except Exception as e_df:
                logging.error(f"Error creating or processing DataFrame: {e_df}", exc_info=True)
        else:
            logging.warning("No team data collected, CSV file will not be created.")

        overall_end_time = time.time()
        total_duration = overall_end_time - overall_start_time
        logging.info(f"\nScript finished in {total_duration:.2f} seconds.")
        logging.info(f"Total Teams Found and processed: {len(team_data_list)}")
        logging.info("="*60) # Wider separator for end log