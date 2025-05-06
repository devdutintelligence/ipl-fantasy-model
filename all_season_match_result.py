# -*- coding: utf-8 -*-
import time
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver # For type hinting
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)
from bs4 import BeautifulSoup, Tag
import pandas as pd
import traceback
from datetime import datetime
import logging
import os
import random
import re # Needed for parsing

# --- Configuration for Season Match Results ---
# Define the list of seasons to scrape
SEASONS_TO_SCRAPE = [
    '2007/08', '2009', '2009/10', '2011', '2012', '2013', '2014',
    '2015', '2016', '2017', '2018', '2019', '2020/21', '2021',
    '2022', '2023', '2024', '2025'
]
TROPHY_ID = '117' # Assuming IPL trophy ID

# Output directory and filename for combined results
OUTPUT_DIR = "All_Seasons_Match_Results_Output" # General directory name
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV_FILENAME = "all_season_match_results.csv" # General filename
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, OUTPUT_CSV_FILENAME)

# Base URL template for season records
BASE_URL_TEMPLATE = 'https://www.espncricinfo.com/records/season/team-match-results/{season_url_part}-{season_url_part}?trophy={trophy_id}'

# --- Selectors (VERIFY THESE AGAINST LIVE PAGES if issues occur on specific seasons) ---
# Wait for a container holding the table.
WAIT_CONTAINER_SELECTOR = '#main-container div.ds-relative div div.ds-grow > div:nth-child(2) > div > div:nth-child(1)'
# Find the table within the container using BeautifulSoup
TABLE_SELECTOR_IN_SOUP = 'div.ds-overflow-x-auto > table'

# Column indices (1-based) for match results table - Assumed consistent
COL_INDICES = {
    'Team 1': 1, 'Team 2': 2, 'Winner': 3, 'Margin': 4,
    'Ground': 5, 'Match Date': 6, 'Scorecard': 7,
}

WAIT_TIME = 30  # Seconds

# --- Logging Setup ---
log_filename = os.path.join(OUTPUT_DIR, f"all_seasons_match_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log") # General log filename
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)

current_time_system = datetime.now()
current_time_str = current_time_system.strftime('%Y-%m-%d %H:%M:%S %Z')

logging.info(f"Log file: {log_filename}")
logging.info(f"Script started at: {current_time_str}")
logging.info(f"Targeting Match Results for Seasons: {SEASONS_TO_SCRAPE}, Trophy: {TROPHY_ID}") # Log list of seasons
logging.info(f"Output CSV will be saved to: {OUTPUT_CSV_PATH}") # Log combined output path
logging.info(f"Waiting for container: {WAIT_CONTAINER_SELECTOR}")
logging.warning("Selectors assumed consistent across seasons. Failures on specific seasons might require selector adjustments for that year.")


# --- Helper Functions (Identical to previous script) ---

def safe_get_text(element, default=pd.NA):
    """Safely extracts stripped text from a BS Tag or returns default (pd.NA)."""
    if isinstance(element, Tag):
        text = element.get_text(strip=True)
        return text if text else default
    elif isinstance(element, str):
        text = element.strip()
        return text if text else default
    return default

def format_season_string(season):
    """Converts 'YYYY' or 'YYYY/YY' to URL format 'YYYY' or 'YYYYtoYY'."""
    if '/' in season: return season.replace('/', 'to')
    return season

def parse_margin(margin_string):
    """Parses margin string like '5 wickets' or '23 runs'."""
    if pd.isna(margin_string) or margin_string == '-': return pd.NA, pd.NA
    match = re.match(r"(\d+)\s+(runs|wickets|wicket|run)", margin_string, re.IGNORECASE)
    if match:
        net_margin = int(match.group(1))
        margin_type = match.group(2).lower()
        if margin_type == 'wicket': margin_type = 'wickets'
        elif margin_type == 'run': margin_type = 'runs'
        return net_margin, margin_type
    else:
        logging.debug(f"Margin '{margin_string}' did not match expected format.")
        return pd.NA, margin_string

def extract_id_from_href(element, id_type):
    """Extracts Ground ID or Match ID from an href found within an element."""
    if not isinstance(element, Tag): return pd.NA, pd.NA
    link_tag = element.find('a', href=True)
    if not link_tag: return pd.NA, pd.NA
    href = link_tag['href']
    match = None
    try:
        if id_type == 'Ground': match = re.search(r"-(\d+)$", href)
        elif id_type == 'Match': match = re.search(r"-(\d+)/[^/]+$", href)
    except Exception as e:
        logging.error(f"Regex error extracting {id_type} ID from {href}: {e}")
        return href, pd.NA
    if match: return href, match.group(1)
    else:
        logging.warning(f"Could not extract {id_type} ID pattern from href: {href}")
        return href, pd.NA

# --- Driver Setup (Identical to previous script) ---
def setup_driver(driver_path=None, browser_path=None):
    """Sets up undetected_chromedriver with options, retries, optional paths."""
    driver = None
    retries = 3
    last_exception = None

    for attempt in range(retries):
        logging.info(f"Attempting to initialize WebDriver (Attempt {attempt + 1}/{retries})...")
        try:
            options = uc.ChromeOptions()
            # options.add_argument('--headless=new') # Uncomment for headless
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument('--log-level=3')
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

            driver_kwargs = {'options': options, 'enable_cdp_events': True}
            if driver_path and os.path.exists(driver_path):
                driver_kwargs['driver_executable_path'] = driver_path
                logging.info(f"Using specified ChromeDriver: {driver_path}")
            elif driver_path:
                 logging.warning(f"Specified ChromeDriver path not found: {driver_path}. Using auto-detection.")

            if browser_path and os.path.exists(browser_path):
                driver_kwargs['browser_executable_path'] = browser_path
                logging.info(f"Using specified Chrome Browser: {browser_path}")
            elif browser_path:
                 logging.warning(f"Specified Chrome Browser path not found: {browser_path}. Using auto-detection.")

            driver = uc.Chrome(**driver_kwargs)
            logging.info("Browser driver setup successful.")
            return driver # Success

        except Exception as e:
            last_exception = e
            logging.warning(f"WebDriver init attempt {attempt + 1} failed: {e}", exc_info=(attempt == 0))
            if attempt < retries - 1: time.sleep(5)
            else: logging.error("Max retries reached for WebDriver init."); raise last_exception

    if driver is None and last_exception: raise last_exception
    return driver


# --- Main Scraping Function (Identical structure to previous script) ---
def scrape_season_match_results(driver: WebDriver, season_str: str, season_url_part: str) -> list:
    """
    Scrapes match results data for a specific season page.
    Returns a list of dictionaries, each representing a match row.
    """
    target_url = BASE_URL_TEMPLATE.format(season_url_part=season_url_part, trophy_id=TROPHY_ID)
    logging.info(f"Navigating to URL for season {season_str}: {target_url}")
    match_results_list = []
    max_col_index = max(COL_INDICES.values()) if COL_INDICES else 0

    try:
        driver.get(target_url)
        logging.info(f"Waiting up to {WAIT_TIME}s for container: '{WAIT_CONTAINER_SELECTOR}'")
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, WAIT_CONTAINER_SELECTOR))
        )
        logging.info("Container element located. Allowing brief pause and parsing...")
        time.sleep(random.uniform(1.5, 3.0))

        page_soup = BeautifulSoup(driver.page_source, 'lxml')
        container_div = page_soup.select_one(WAIT_CONTAINER_SELECTOR)
        if not container_div:
             logging.error(f"Container selector '{WAIT_CONTAINER_SELECTOR}' failed in BeautifulSoup for season {season_str}.")
             return []

        results_table = container_div.select_one(TABLE_SELECTOR_IN_SOUP)
        if not results_table:
            logging.error(f"Could not find table using '{TABLE_SELECTOR_IN_SOUP}' within the container for season {season_str}.")
            logging.debug(f"Container HTML snippet: {str(container_div)[:500]}")
            return []

        table_body = results_table.find('tbody')
        if not table_body:
            logging.warning(f"No 'tbody' found within the table for season {season_str}.")
            return []

        match_rows = table_body.find_all('tr', recursive=False)
        logging.info(f"Found {len(match_rows)} rows in table body for season {season_str}.")
        processed_count = 0
        for i, row in enumerate(match_rows):
            row_data = {'Season': season_str}
            try:
                cols = row.find_all('td', recursive=False)
                if len(cols) < max_col_index:
                    logging.warning(f"Skipping row {i+1}: Expected {max_col_index} cells, found {len(cols)}.")
                    continue

                row_data['Team 1'] = safe_get_text(cols[COL_INDICES['Team 1'] - 1])
                row_data['Team 2'] = safe_get_text(cols[COL_INDICES['Team 2'] - 1])
                row_data['Winner'] = safe_get_text(cols[COL_INDICES['Winner'] - 1])
                margin_text = safe_get_text(cols[COL_INDICES['Margin'] - 1])
                net_margin, margin_type = parse_margin(margin_text)
                row_data['Net Margin'] = net_margin
                row_data['Margin Type'] = margin_type
                row_data['Margin Raw'] = margin_text
                ground_cell = cols[COL_INDICES['Ground'] - 1]
                row_data['Ground Name'] = safe_get_text(ground_cell.find('a'), default=safe_get_text(ground_cell))
                _, row_data['Ground ID'] = extract_id_from_href(ground_cell, 'Ground')
                row_data['Match Date'] = safe_get_text(cols[COL_INDICES['Match Date'] - 1])
                scorecard_cell = cols[COL_INDICES['Scorecard'] - 1]
                scorecard_href, row_data['Match ID'] = extract_id_from_href(scorecard_cell, 'Match')
                row_data['Scorecard Link'] = scorecard_href

                match_results_list.append(row_data)
                processed_count += 1
            except IndexError as e:
                logging.error(f"Error processing row {i+1} data (IndexError) for season {season_str}: {e}.", exc_info=False)
            except Exception as e:
                logging.error(f"Unexpected error processing row {i+1} for season {season_str}: {e}.", exc_info=True)
        logging.info(f"Successfully processed {processed_count} matches for season {season_str}.")
    except TimeoutException:
        logging.error(f"Timed out waiting for container element for season {season_str} at {target_url}")
    except Exception as e_page:
        logging.error(f"Unexpected error scraping page for season {season_str}: {e_page}", exc_info=True)
    return match_results_list

# --- Main Execution Logic (Modified for Multiple Seasons) ---
if __name__ == "__main__":
    overall_start_time = time.time()
    driver = None
    all_match_data = [] # List to hold data from ALL specified seasons

    try:
        driver = setup_driver()
        total_seasons = len(SEASONS_TO_SCRAPE)

        # Loop through each season in the list
        for i, season in enumerate(SEASONS_TO_SCRAPE):
            season_url_part = format_season_string(season)
            logging.info(f"\n>>> Processing Season {i+1}/{total_seasons}: {season} (URL part: {season_url_part}) <<<\n")

            # Scrape data for the current season
            season_data = scrape_season_match_results(driver, season, season_url_part)

            if season_data:
                all_match_data.extend(season_data) # Add this season's data to the main list
                logging.info(f"Added {len(season_data)} match records for season {season}.")
            else:
                logging.warning(f"No data retrieved or processed for season {season}.")

            # Add a delay between scraping seasons to be polite to the server
            if i < total_seasons - 1: # Don't sleep after the last season
                sleep_duration = random.uniform(4.0, 8.0) # Random delay between 4 and 8 seconds
                logging.info(f"--- Delaying for {sleep_duration:.2f} seconds before next season ---")
                time.sleep(sleep_duration)

    except Exception as e:
        logging.critical(f"A critical error occurred during driver setup or the main season loop: {e}", exc_info=True)
    finally:
        if driver:
            try:
                logging.info("Quitting WebDriver...")
                driver.quit()
                logging.info("Browser closed.")
            except Exception as quit_err:
                logging.error(f"Error occurred while closing the browser: {quit_err}")

    # --- Process and Save Combined DataFrame to CSV ---
    logging.info(f"\n--- Processing and Saving Combined Match Results for All Seasons ---") # Updated log message

    if all_match_data: # Check if the combined list is not empty
        try:
            summary_df = pd.DataFrame(all_match_data) # Create DataFrame from combined data
            logging.info(f"Created combined DataFrame with {len(summary_df)} total match rows from {summary_df['Season'].nunique()} seasons.")

            # Define and Apply Final Column Order (same as before)
            final_cols_ordered = [
                'Season', 'Team 1', 'Team 2', 'Winner', 'Net Margin', 'Margin Type',
                'Ground Name', 'Ground ID', 'Match Date', 'Match ID', 'Scorecard Link',
                'Margin Raw'
            ]
            for col in final_cols_ordered:
                if col not in summary_df.columns: summary_df[col] = pd.NA
            summary_df = summary_df[final_cols_ordered]
            logging.info(f"Final columns ordered: {final_cols_ordered}")

            # Data Cleaning/Type Conversion (same as before)
            try:
                summary_df['Match Date'] = pd.to_datetime(summary_df['Match Date'], errors='coerce')
                logging.info("Converted 'Match Date' to datetime.")
            except Exception as date_err:
                logging.warning(f"Could not convert 'Match Date': {date_err}")
            numeric_cols = ['Net Margin', 'Ground ID', 'Match ID']
            for col in numeric_cols:
                if col in summary_df.columns:
                     summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')
            logging.info("Attempted numeric conversion for Net Margin and IDs.")

            # Save to CSV
            logging.info(f"Saving combined results to CSV: {OUTPUT_CSV_PATH}") # Use combined path
            summary_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
            logging.info(f"Successfully saved combined data to {OUTPUT_CSV_PATH}")
            print(f"\n*** Combined match results for all seasons saved to: {OUTPUT_CSV_PATH} ***") # Updated message
            print(f"      Contains {len(summary_df)} matches from {summary_df['Season'].nunique()} seasons.")

            # Console Print of DataFrame Head
            print("\n--- First 15 Rows of Combined Data ---")
            pd.set_option('display.max_rows', 25); pd.set_option('display.max_columns', None); pd.set_option('display.width', 2500)
            print(summary_df.head(15).to_string(index=False))
            print("--- End of Head ---")

        except Exception as e_proc:
            logging.error(f"Error creating combined DataFrame or saving to CSV: {e_proc}", exc_info=True)
            print(f"\n--- Error processing or saving final combined data. Check logs: {log_filename} ---")

    else:
        logging.warning("No match data collected for any season. Cannot generate CSV.") # Updated message
        print(f"\n--- No match data retrieved for any of the specified seasons. No CSV file generated. ---")
        print(f"--- Check log file ({log_filename}) for errors (e.g., Timeouts, Selector issues on specific seasons). ---")

    # --- Final Summary ---
    overall_end_time = time.time(); total_duration = overall_end_time - overall_start_time
    logging.info(f"\nScript finished in {total_duration:.2f} seconds.")
    processed_seasons_count = 0
    if 'summary_df' in locals() and isinstance(summary_df, pd.DataFrame):
         processed_seasons_count = summary_df['Season'].nunique()
    logging.info(f"Attempted processing for {len(SEASONS_TO_SCRAPE)} seasons. Data found for {processed_seasons_count} seasons.") # Updated summary
    logging.info("--- Script End ---")