# -*- coding: utf-8 -*-
import time
import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver
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
import re
from urllib.parse import urljoin
import sys # Import sys to use sys.exit() more reliably

# --- Configuration ---
# !!! UPDATE THIS FOR THE DESIRED SEASON !!!
TARGET_SEASON = '2011' # <--- UPDATED FOR 2025
# !!! CRITICAL: YOU MUST UPDATE THIS TROPHY ID FOR THE SPECIFIC 2025 TOURNAMENT !!!
# Find the correct ID by browsing ESPNcricinfo for the 2025 tournament records page.
# Example URL: https://www.espncricinfo.com/records/season/team-match-results/2025-2025?trophy=XXXX <-- Find XXXX
TROPHY_ID = '117' # Placeholder - Almost certainly incorrect for 2025. UPDATE THIS!
RETRY_FAILED_SCORECARDS = True # Flag to enable retry mechanism

# --- Directory and File Naming ---
# Base prefix for files/dirs based on season
season_file_prefix = TARGET_SEASON.replace('/', '-') # Results in '2025'

# Main output directory
MAIN_OUTPUT_DIR = f"{season_file_prefix}_Scorecard"

# Subdirectories for logs and data
LOG_DIR = os.path.join(MAIN_OUTPUT_DIR, f"{season_file_prefix}_scorecard_log")
DATA_DIR = os.path.join(MAIN_OUTPUT_DIR, f"{season_file_prefix}_scorecard_data")

# Create directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# --- Output File Paths ---
SEASON_SUMMARY_CSV_FILENAME = f"{season_file_prefix}_All_matches.csv"
SEASON_SUMMARY_CSV_PATH = os.path.join(DATA_DIR, SEASON_SUMMARY_CSV_FILENAME)
BATTING_CSV_FILENAME = f"{season_file_prefix}_All_matches_batting.csv"
BOWLING_CSV_FILENAME = f"{season_file_prefix}_All_matches_bowling.csv"
BATTING_CSV_PATH = os.path.join(DATA_DIR, BATTING_CSV_FILENAME)
BOWLING_CSV_PATH = os.path.join(DATA_DIR, BOWLING_CSV_FILENAME)

# --- URLs ---
BASE_CRICINFO_URL = 'https://www.espncricinfo.com'
SEASON_URL_TEMPLATE = '/records/season/team-match-results/{season_url_part}-{season_url_part}?trophy={trophy_id}'

# --- Selectors (!!! CRITICAL: THESE NEED VERIFICATION/UPDATING FOR 2025 PAGES !!!) ---
# The selectors below MIGHT FAIL for 2025. Website structure changes often.
# You MUST inspect the 2025 pages and update these selectors if necessary.
SEASON_WAIT_CONTAINER_SELECTOR = '#main-container div.ds-relative div div.ds-grow > div:nth-child(2) > div > div:nth-child(1)' # LIKELY NEEDS VERIFICATION for 2025
SEASON_TABLE_SELECTOR_IN_SOUP = 'div.ds-overflow-x-auto > table' # LIKELY NEEDS VERIFICATION for 2025
SEASON_TABLE_SELECTOR_SELENIUM = SEASON_TABLE_SELECTOR_IN_SOUP # LIKELY NEEDS VERIFICATION for 2025
SEASON_COL_INDICES = {'Team 1': 1, 'Team 2': 2, 'Winner': 3, 'Margin': 4, 'Ground': 5, 'Match Date': 6, 'Scorecard': 7} # Verify column order for 2025
SCORECARD_WAIT_SELECTOR = '#main-container' # Might be okay, but verify

# Scorecard selectors - VERY LIKELY WRONG/DIFFERENT for 2025 - MUST BE UPDATED
INNINGS_1_BATTING_TEAM_SELECTOR = '#main-container > div.ds-relative > div > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div:nth-child(1) > div:nth-child(2) > div > div.ds-flex.ds-px-4.ds-border-b.ds-border-line.ds-py-3.ds-bg-ui-fill-translucent-hover > div > span > span.ds-text-title-xs.ds-font-bold.ds-capitalize'
INNINGS_1_BATTING_TABLE_SELECTOR = '#main-container > div.ds-relative > div > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div:nth-child(1) > div:nth-child(2) > div > div.ds-p-0 > table.ci-scorecard-table'
INNINGS_1_BOWLING_TABLE_SELECTOR = '#main-container > div.ds-relative > div > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div:nth-child(1) > div:nth-child(2) > div > div.ds-p-0 > table:nth-child(2)'

INNINGS_2_BATTING_TEAM_SELECTOR = '#main-container > div.ds-relative > div > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div:nth-child(1) > div:nth-child(3) > div > div.ds-flex.ds-px-4.ds-border-b.ds-border-line.ds-py-3.ds-bg-ui-fill-translucent-hover > div > span > span.ds-text-title-xs.ds-font-bold.ds-capitalize'
INNINGS_2_BATTING_TABLE_SELECTOR = '#main-container > div.ds-relative > div > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div:nth-child(1) > div:nth-child(3) > div > div.ds-p-0 > table.ci-scorecard-table'
INNINGS_2_BOWLING_TABLE_SELECTOR = '#main-container > div.ds-relative > div > div > div.ds-flex.ds-space-x-5 > div.ds-grow > div.ds-mt-3 > div:nth-child(1) > div:nth-child(3) > div > div.ds-p-0 > table:nth-child(2)'

DISMISSAL_DETAIL_SELECTOR = 'td > div > span > i'  # Verify dismissal structure for 2025
BATTING_COL_INDICES = {'Batter': 1, 'Dismissal': 2, 'Runs': 3, 'Balls': 4, 'Mins': 5, '4s': 6, '6s': 7, 'SR': 8} # Verify column order for 2025
BOWLING_COL_INDICES = {'Bowler': 1, 'Overs': 2, 'Mdns': 3, 'Runs': 4, 'Wkts': 5, 'Econ': 6, 'Dots': 7, '4s': 8, '6s': 9, 'WD': 10, 'NB': 11} # Verify column order for 2025
BOWLING_WICKET_SELECTOR = 'span > strong' # Verify wicket element for 2025
# --- End Selectors to Verify ---

WAIT_TIME = 40 # May need adjustment based on 2025 page load times
TABLE_FIND_RETRIES = 3
TABLE_FIND_DELAY = 2
SCORECARD_SLEEP_MIN = 6.0
SCORECARD_SLEEP_MAX = 12.0

# --- Logging Setup ---
log_filename = os.path.join(LOG_DIR, f"{season_file_prefix}_scorecard_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
# Use INFO level for production, DEBUG for development
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s [%(funcName)s:%(lineno)d] - %(message)s', handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()])
logging.getLogger("selenium").setLevel(logging.WARNING); logging.getLogger("urllib3").setLevel(logging.WARNING); logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)

logging.info(f"Log file: {log_filename}")
logging.info(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info(f"Targeting Scorecard Details for Season: {TARGET_SEASON}, Trophy: {TROPHY_ID}") # Updated log message
logging.info(f"Processing ALL matches found in season summary.")
logging.info(f"Retry failed scorecards enabled: {RETRY_FAILED_SCORECARDS}")
logging.info(f"Main Output Directory: {MAIN_OUTPUT_DIR}")
logging.info(f"Season Summary Output CSV: {SEASON_SUMMARY_CSV_PATH}")
logging.info(f"Detailed Batting Output CSV: {BATTING_CSV_PATH}")
logging.info(f"Detailed Bowling Output CSV: {BOWLING_CSV_PATH}")
logging.warning("!!! CRITICAL: Selectors in this script MAY NEED UPDATING for the {} season. Verify them by inspecting the website HTML structure !!!".format(TARGET_SEASON)) # Updated warning
logging.warning(f"!!! CRITICAL: YOU MUST Verify TROPHY_ID '{TROPHY_ID}' is correct for the desired {TARGET_SEASON} tournament !!!") # Updated warning


# --- Helper Functions ---
# (Helper functions remain the same for now, but may need tweaks based on 2025 data formats)
def safe_get_text(element, default=pd.NA):
    """Safely extracts text from a BeautifulSoup element or string, handling None and whitespace."""
    if isinstance(element, Tag):
        text = element.get_text(strip=True)
        return text if text else default
    elif isinstance(element, str):
        text = element.strip()
        return text if text else default
    return default

def format_season_string(season):
    """Formats the season string for URLs. Handles single year and year/year formats."""
    if '/' in season:
        # For '2020/21', format as '2020to21'
        return season.replace('/', 'to')
    # For single year like '2025', format as '2025-2025'
    return f"{season}-{season}"

def parse_margin(margin_string):
    """Parses the margin string to extract numeric value and type (runs/wickets)."""
    if pd.isna(margin_string) or margin_string == '-':
        return pd.NA, pd.NA
    # Updated regex to be slightly more flexible with wording
    match = re.match(r"(.+?)\s+won by\s+(\d+)\s+(runs|wickets|wicket|run)", margin_string, re.IGNORECASE)
    if match:
         net_margin = int(match.group(2));
         margin_type = match.group(3).lower()
         if margin_type == 'wicket': margin_type = 'wickets'
         elif margin_type == 'run': margin_type = 'runs'
         return net_margin, margin_type
    else:
         # Fallback for just number and type
         match = re.match(r"(\d+)\s+(runs|wickets|wicket|run)", margin_string, re.IGNORECASE)
         if match:
             net_margin = int(match.group(1));
             margin_type = match.group(2).lower()
             if margin_type == 'wicket': margin_type = 'wickets'
             elif margin_type == 'run': margin_type = 'runs'
             return net_margin, margin_type
         else:
             # Handle other cases like "tied", "no result" etc.
             return pd.NA, margin_string # Return original string if not runs/wickets

def extract_id_from_href(element, id_type):
    """Extracts an ID (Ground, Match, Player) from an <a> tag's href attribute using regex.
       Can handle being passed the <a> tag directly or a parent element containing it."""
    href, extracted_id = pd.NA, pd.NA
    link_tag = None
    if not isinstance(element, Tag): logging.warning(f"Invalid element type passed to extract_id_from_href: {type(element)}"); return href, extracted_id
    if element.name == 'a' and element.get('href'): link_tag = element
    else:
        link_tag = element.find('a', href=True)
        if not link_tag:
            link_tags = element.find_all('a', href=True)
            if link_tags: link_tag = link_tags[0]; logging.debug(f"Found link tag deeper within parent {element.name}")
            else: logging.debug(f"No <a> tag with href found within element: {element.name}"); return href, extracted_id
    href = link_tag.get('href');
    if not href: logging.warning(f"<a> tag found but has no href attribute: {link_tag.prettify()}"); return href, extracted_id
    match = None
    try:
        # --- ID Extraction Logic (Verify patterns based on 2025 URLs) ---
        if id_type == 'Ground': match = re.search(r'[/-](\d+)/?$', href)
        elif id_type == 'Player': match = re.search(r'/cricketers/.*?-(\d+)', href)
        elif id_type == 'Match':
             match = re.search(r'-(\d+)/[^/]*$', href)
             if not match: logging.debug(f"Primary match ID regex failed for {href}, trying fallback..."); match = re.search(r'[/-](\d+)/?$', href)
    except Exception as e: logging.error(f"Regex error extracting {id_type} ID from {href}: {e}"); return href, pd.NA
    if match: extracted_id = match.group(1)
    else: logging.warning(f"Could not extract {id_type} ID pattern from href: {href}")
    return href, extracted_id


def extract_player_info(cell_element):
    """Extracts player name, ID, and href from a table cell, handling different name formats."""
    # (This function likely needs verification based on 2025 scorecard structure)
    name, player_id, href = pd.NA, pd.NA, pd.NA
    if not isinstance(cell_element, Tag): logging.warning(f"Invalid cell_element passed to extract_player_info: {type(cell_element)}"); return name, player_id, href
    link_tag = cell_element.find('a', href=re.compile(r'/cricketers/'))
    if not link_tag:
        nested_div = cell_element.find('div')
        if nested_div: link_tag = nested_div.find('a', href=re.compile(r'/cricketers/'))
    if link_tag:
        href, p_id = extract_id_from_href(link_tag, 'Player')
        player_id = p_id
        name = link_tag.get('title', None)
        if name and ('View full profile' in name or 'profile' in name.lower()):
            name = name.replace('View full profile of', '').strip()
            if name.lower().endswith(' profile'): name = name[:-len(' profile')].strip()
        if pd.isna(name) or not name:
            name_span = link_tag.find('span', class_=lambda x: x and 'ds-text-tight-s' in x and 'ds-font-medium' in x)
            if not name_span: name_span = link_tag.find('span')
            name = safe_get_text(name_span if name_span else link_tag)
        if isinstance(name, str):
            name = re.sub(r'\s*\(c\)\s*', '', name).replace('†', '').strip(); name = re.sub(r'\s+', ' ', name)
    else:
        name = safe_get_text(cell_element); logging.debug(f"No player link/ID found in cell. Text: '{name}'")
    if pd.isna(player_id) and link_tag: logging.debug(f"Failed to extract Player ID for name '{name}' from href '{href}'")
    return name, player_id, href

def parse_dismissal(dismissal_string):
    """Parses dismissal strings to extract dismissal type, fielder, and bowler."""
    # (This function likely needs verification based on 2025 scorecard structure/notation)
    raw_text = safe_get_text(dismissal_string);
    dismissal_type, fielder, bowler = raw_text, pd.NA, pd.NA
    if pd.isna(raw_text) or not isinstance(raw_text, str): return pd.NA, pd.NA, pd.NA
    text = raw_text.strip(); lower_text = text.lower()
    if lower_text == 'not out': dismissal_type = 'not out'; fielder, bowler = pd.NA, pd.NA
    elif lower_text.startswith('c & b '): dismissal_type = 'caught and bowled'; bowler = safe_get_text(text[6:]); fielder = bowler
    elif lower_text.startswith('st '):
        dismissal_type = 'stumped'; match_st = re.match(r"st\s+†?([\w\s'-]+)\s+b\s+([\w\s'-]+)", text, re.IGNORECASE);
        if match_st: fielder = match_st.group(1).strip(); bowler = match_st.group(2).strip()
        elif ' b ' in lower_text: parts = text.split(' b ', 1); bowler = safe_get_text(parts[1]); fielder = safe_get_text(text[3:len(parts[0])])
        else: fielder = safe_get_text(text[3:])
    elif lower_text.startswith('c '):
        dismissal_type = 'caught'; match_c = re.match(r"c\s+†?([\w\s'-]+)\s+b\s+([\w\s'-]+)", text, re.IGNORECASE);
        if match_c: fielder = match_c.group(1).strip(); bowler = match_c.group(2).strip()
        elif ' b ' in lower_text: parts = text.split(' b ', 1); bowler = safe_get_text(parts[1]); fielder = safe_get_text(text[2:len(parts[0])])
        else: fielder = safe_get_text(text[2:])
    elif lower_text.startswith('run out'):
        dismissal_type = 'run out'; match_ro = re.search(r'\((.*?)\)', text);
        if match_ro: fielder = safe_get_text(match_ro.group(1))
        else:
             if '(' in text and ')' in text: fielder_text = text[text.find('(')+1:text.rfind(')')]; fielder = safe_get_text(fielder_text)
             else: fielder = pd.NA
    elif lower_text.startswith('lbw b '): dismissal_type = 'lbw'; bowler = safe_get_text(text[6:]); fielder = pd.NA
    elif lower_text.startswith('b '): dismissal_type = 'bowled'; bowler = safe_get_text(text[2:]); fielder = pd.NA
    elif lower_text == 'retired hurt': dismissal_type = 'retired hurt'; fielder, bowler = pd.NA, pd.NA
    elif lower_text == 'retired out': dismissal_type = 'retired out'; fielder, bowler = pd.NA, pd.NA
    elif lower_text.startswith('hit wicket'):
        dismissal_type = 'hit wicket'; fielder = pd.NA;
        if ' b ' in lower_text: parts = text.split(' b ', 1); bowler = safe_get_text(parts[1])
    elif dismissal_type not in ['caught and bowled', 'stumped', 'caught', 'lbw', 'bowled', 'hit wicket']: bowler = pd.NA
    if isinstance(fielder, str): fielder = fielder.replace('†', '').strip()
    if isinstance(bowler, str): bowler = bowler.strip()
    return dismissal_type, fielder, bowler

# --- Driver Setup ---
def setup_driver(driver_path=None, browser_path=None):
    """Sets up the Selenium WebDriver with retries and undetected_chromedriver."""
    driver = None; retries = 3; last_exception = None
    for attempt in range(retries):
        logging.info(f"WebDriver Init Attempt {attempt + 1}/{retries}...")
        try:
            options = uc.ChromeOptions(); # options.add_argument('--headless=new') # Enable for headless run
            options.add_argument("--start-maximized"); options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage");
            options.add_argument('--log-level=3'); options.add_argument("--disable-gpu"); options.add_argument("--disable-extensions");
            options.add_argument("--disable-infobars"); options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36") # Example, update if needed
            driver_kwargs = {'options': options, 'enable_cdp_events': True}
            if driver_path and os.path.exists(driver_path): driver_kwargs['driver_executable_path'] = driver_path; logging.info(f"Using ChromeDriver: {driver_path}")
            elif driver_path: logging.warning(f"Driver path not found: {driver_path}. Using auto.")
            if browser_path and os.path.exists(browser_path): driver_kwargs['browser_executable_path'] = browser_path; logging.info(f"Using Chrome Browser: {browser_path}")
            elif browser_path: logging.warning(f"Browser path not found: {browser_path}. Using auto.")
            driver = uc.Chrome(**driver_kwargs); logging.info("Browser driver setup successful."); return driver
        except Exception as e:
            last_exception = e; logging.warning(f"WebDriver init attempt {attempt + 1} failed: {e}", exc_info=(attempt == 0))
            if attempt < retries - 1: time.sleep(5)
            else: logging.error("Max retries for WebDriver init."); raise last_exception
    if driver is None and last_exception: raise last_exception
    return driver

# --- Scraping Functions ---

def scrape_season_summary(driver: WebDriver, season_str: str, season_url_part: str) -> list:
    """Scrapes the summary data for all matches in a season, handling potential ads."""
    target_url = urljoin(BASE_CRICINFO_URL, SEASON_URL_TEMPLATE.format(season_url_part=season_url_part, trophy_id=TROPHY_ID))
    logging.info(f"Getting match summary list for season {season_str} from: {target_url}")
    season_summary_list = []
    # !!! Verify column indices for 2025 season summary table !!!
    max_col_index = max(SEASON_COL_INDICES.values()) if SEASON_COL_INDICES else 0
    try:
        driver.get(target_url);
        logging.info(f"Waiting up to {WAIT_TIME}s for season summary table to be visible: '{SEASON_TABLE_SELECTOR_SELENIUM}'")
        try:
            WebDriverWait(driver, WAIT_TIME).until(EC.visibility_of_element_located((By.CSS_SELECTOR, SEASON_TABLE_SELECTOR_SELENIUM)))
            logging.info("Season summary table is visible.")
        except TimeoutException:
            logging.warning(f"Timed out waiting for table visibility. Waiting for container: '{SEASON_WAIT_CONTAINER_SELECTOR}'")
            WebDriverWait(driver, WAIT_TIME).until(EC.visibility_of_element_located((By.CSS_SELECTOR, SEASON_WAIT_CONTAINER_SELECTOR)))
            logging.info("Season summary container is visible.")
        time.sleep(random.uniform(3.0, 5.0))
        page_soup = BeautifulSoup(driver.page_source, 'lxml')
        container_div = page_soup.select_one(SEASON_WAIT_CONTAINER_SELECTOR)
        results_table = None
        for attempt in range(TABLE_FIND_RETRIES):
             table_search_area = container_div if container_div else page_soup
             results_table = table_search_area.select_one(SEASON_TABLE_SELECTOR_IN_SOUP) # !!! Verify selector for 2025 !!!
             if results_table: logging.info(f"Found season summary table in BeautifulSoup on attempt {attempt + 1}."); break
             elif attempt < TABLE_FIND_RETRIES - 1:
                 logging.warning(f"Season summary table not found in soup on attempt {attempt + 1}. Retrying in {TABLE_FIND_DELAY}s..."); time.sleep(TABLE_FIND_DELAY)
                 page_soup = BeautifulSoup(driver.page_source, 'lxml'); container_div = page_soup.select_one(SEASON_WAIT_CONTAINER_SELECTOR)
             else: logging.error(f"Season Summary: Results table not found in BeautifulSoup after {TABLE_FIND_RETRIES} attempts."); return []
        table_body = results_table.find('tbody');
        if not table_body: logging.warning(f"Season Summary: Table body (tbody) not found {season_str}"); return []
        match_rows = table_body.find_all('tr', recursive=False); logging.info(f"Found {len(match_rows)} rows in season summary table.")
        for i, row in enumerate(match_rows):
            summary_data = {'Season': season_str}
            try:
                cols = row.find_all('td', recursive=False)
                # Check if the number of columns is sufficient before trying to access them by index
                if len(cols) < max_col_index:
                    logging.debug(f"Skipping summary row {i + 1}: Found {len(cols)} cols, expected at least {max_col_index}. Likely header/footer/message row.")
                    continue

                # Check if the first cell indicates a non-data row (e.g., "No results found") - adjust text if needed
                first_cell_text = safe_get_text(cols[0]).lower()
                if "no result" in first_cell_text or len(cols) < max_col_index: # Added explicit check again
                    logging.warning(f"Skipping summary row {i + 1} as it appears to be a non-data row. First cell: '{safe_get_text(cols[0])}'")
                    continue

                # !!! Verify column indices for 2025 !!!
                summary_data['Team 1'] = safe_get_text(cols[SEASON_COL_INDICES['Team 1'] - 1])
                summary_data['Team 2'] = safe_get_text(cols[SEASON_COL_INDICES['Team 2'] - 1])
                summary_data['Winner'] = safe_get_text(cols[SEASON_COL_INDICES['Winner'] - 1])
                margin_text = safe_get_text(cols[SEASON_COL_INDICES['Margin'] - 1])
                net_margin, margin_type = parse_margin(margin_text)
                summary_data['Net Margin'] = net_margin; summary_data['Margin Type'] = margin_type; summary_data['Margin Raw'] = margin_text
                ground_cell = cols[SEASON_COL_INDICES['Ground'] - 1]
                summary_data['Ground Name'] = safe_get_text(ground_cell.find('a'), default=safe_get_text(ground_cell))
                _, summary_data['Ground ID'] = extract_id_from_href(ground_cell, 'Ground')
                summary_data['Match Date'] = safe_get_text(cols[SEASON_COL_INDICES['Match Date'] - 1])
                scorecard_cell = cols[SEASON_COL_INDICES['Scorecard'] - 1]
                scorecard_href, match_id = extract_id_from_href(scorecard_cell, 'Match')
                summary_data['Match ID'] = match_id; summary_data['Scorecard Link'] = scorecard_href
                if pd.isna(match_id) or pd.isna(scorecard_href):
                    logging.warning(f"Skipping row {i + 1} summary: Missing Match ID ('{match_id}') or Scorecard Link ('{scorecard_href}'). Check selectors/structure.")
                    continue
                season_summary_list.append(summary_data)
            except IndexError:
                 logging.error(f"Error processing season summary row {i + 1} due to IndexError. Found {len(cols)} columns. Row HTML: {row.prettify()}", exc_info=True)
            except Exception as e:
                 logging.error(f"Error processing season summary row {i + 1}: {e}", exc_info=True)
        logging.info(f"Extracted {len(season_summary_list)} match summaries for season {season_str}.")
        return season_summary_list
    except TimeoutException: logging.error(f"Timed out waiting for season summary elements.")
    except Exception as e: logging.error(f"Error getting season summary list {season_str}: {e}", exc_info=True)
    return []

def _process_batting_table(table_body: Tag, match_id: str, innings_num: int, batting_team: str) -> list:
    """Processes batting table BODY tag using paired-row logic, handling dismissal details."""
    # (!!! This function likely needs verification/updates based on 2025 scorecard structure !!!)
    batting_details = []
    if not table_body: logging.warning(f"Match {match_id} Inn {innings_num}: Batting tbody is None."); return batting_details
    rows = table_body.find_all('tr', recursive=False)
    logging.debug(f"Match {match_id} Inn {innings_num}: Processing {len(rows)} rows in batting tbody.")
    row_iterator = iter(enumerate(rows))
    for i, stat_row in row_iterator:
        first_cell = stat_row.find('td');
        first_cell_text_raw = safe_get_text(first_cell)
        first_cell_text = first_cell_text_raw.lower() if isinstance(first_cell_text_raw, str) else ""
        row_classes = stat_row.get('class', [])
        is_footer_row = not first_cell or any(cls in ["ds-text-tight-s", "ds-opacity-40", "!ds-border-b-0", "ds-font-regular", "ds-bg-fill-content-alternate"] for cls in row_classes) or "extras" in first_cell_text or "total" in first_cell_text or "did not bat" in first_cell_text or "fall of wickets" in first_cell_text
        if is_footer_row:
            if "fall of wickets" in first_cell_text: logging.debug(f"Match {match_id} Inn {innings_num}: FOW row found, stopping."); break
            logging.debug(f"Match {match_id} Inn {innings_num}: Skipping batting row {i + 1} (footer/header). Text:'{first_cell_text_raw}', Classes:{row_classes}"); continue
        batter_data = {'Match ID': match_id, 'Innings': innings_num, 'Batting Team': batting_team}; dismissal_processed = False
        try:
            stat_cols = stat_row.find_all('td', recursive=False)
             # !!! Verify BATTING_COL_INDICES for 2025 !!!
            max_expected_bat_col = max(BATTING_COL_INDICES.values()) if BATTING_COL_INDICES else 0
            if len(stat_cols) < BATTING_COL_INDICES.get('Batter', 1): # Basic check
                 logging.warning(f"Bat Row {i + 1}: Found only {len(stat_cols)} cells. Skipping potentially invalid row.")
                 continue
            batter_cell = stat_cols[BATTING_COL_INDICES.get('Batter', 1) - 1]
            is_valid_player_row = len(stat_cols) >= max_expected_bat_col and batter_cell and batter_cell.find('a', href=re.compile(r'/cricketers/'))
            if not is_valid_player_row:
                 if len(stat_cols) == 1: logging.debug(f"Bat Row {i + 1}: Skipping potential dismissal detail row (1 cell).")
                 else: logging.warning(f"Bat Row {i + 1}: Found {len(stat_cols)} cells or missing player link. Expected >= {max_expected_bat_col} cells with link. Skipping row.");
                 continue
            name, p_id, href = extract_player_info(batter_cell)
            batter_data['Batter'] = name; batter_data['Batter id'] = p_id;
            dismissal_text_main_row = safe_get_text(stat_cols[BATTING_COL_INDICES.get('Dismissal', 2) - 1]) # Verify index
            batter_data['Run Scored'] = safe_get_text(stat_cols[BATTING_COL_INDICES.get('Runs', 3) - 1]) # Verify index
            batter_data['Ball faced'] = safe_get_text(stat_cols[BATTING_COL_INDICES.get('Balls', 4) - 1]) # Verify index
            batter_data['Fours'] = safe_get_text(stat_cols[BATTING_COL_INDICES.get('4s', 6) - 1]) # Verify index
            batter_data['Sixes'] = safe_get_text(stat_cols[BATTING_COL_INDICES.get('6s', 7) - 1]) # Verify index
            batter_data['Strike rate'] = safe_get_text(stat_cols[BATTING_COL_INDICES.get('SR', 8) - 1]) # Verify index
            next_row_idx = i + 1
            if next_row_idx < len(rows): # Paired row logic may differ in 2025
                 potential_dismissal_row = rows[next_row_idx]; potential_dismissal_cells = potential_dismissal_row.find_all('td', recursive=False)
                 if len(potential_dismissal_cells) == 1 and not potential_dismissal_row.find('table'): # Check if this condition holds for 2025
                     dismissal_detail_cell = potential_dismissal_cells[0]
                     # !!! Verify dismissal element structure for 2025 !!!
                     dismissal_element_i = dismissal_detail_cell.select_one('div > span > i'); dismissal_element_span = dismissal_detail_cell.select_one('div > span'); dismissal_element_div = dismissal_detail_cell.select_one('div')
                     dismissal_raw_detail = pd.NA; temp_text = pd.NA
                     if dismissal_element_i: dismissal_raw_detail = safe_get_text(dismissal_element_i)
                     elif dismissal_element_span: dismissal_raw_detail = safe_get_text(dismissal_element_span)
                     elif dismissal_element_div: temp_text = safe_get_text(dismissal_element_div);
                     if isinstance(temp_text, str) and temp_text.lower() == 'not out': dismissal_raw_detail = temp_text
                     else: temp_text = safe_get_text(dismissal_detail_cell);
                     if isinstance(temp_text, str) and temp_text.lower() == 'not out': dismissal_raw_detail = temp_text
                     if not pd.isna(dismissal_raw_detail):
                         d_type, d_fielder, d_bowler = parse_dismissal(dismissal_raw_detail) # parse_dismissal may need updates
                         batter_data['Dismissal Type'] = d_type; batter_data['Dismissal Player'] = d_fielder; batter_data['Dismissal Bowler'] = d_bowler
                         try: next(row_iterator); dismissal_processed = True; logging.debug(f"Processed paired dismissal row {next_row_idx + 1} for {name}")
                         except StopIteration: pass
            if not dismissal_processed:
                 logging.debug(f"No paired dismissal row found for {name}, using main row text: '{dismissal_text_main_row}'")
                 d_type, d_fielder, d_bowler = parse_dismissal(dismissal_text_main_row) # parse_dismissal may need updates
                 batter_data['Dismissal Type'] = d_type; batter_data['Dismissal Player'] = d_fielder; batter_data['Dismissal Bowler'] = d_bowler
            batting_details.append(batter_data)
        except IndexError:
            logging.error(f"Match {match_id} Inn {innings_num}: IndexError processing batting row {i + 1} for {batter_data.get('Batter', 'UNKNOWN')}. Found {len(stat_cols)} cells. Row HTML: {stat_row.prettify()}", exc_info=True)
        except Exception as e:
            logging.error(f"Match {match_id} Inn {innings_num}: Error processing batting row {i + 1} for {batter_data.get('Batter', 'UNKNOWN')}. Row HTML: {stat_row.prettify()}", exc_info=True)
    return batting_details

def _process_bowling_table(table_body: Tag, match_id: str, innings_num: int, bowling_team: str) -> list:
    """Processes bowling table BODY tag rows."""
    # (!!! This function likely needs verification/updates based on 2025 scorecard structure !!!)
    bowling_details = []
    if not table_body: logging.warning(f"Match {match_id} Inn {innings_num}: Bowling tbody is None."); return bowling_details
    bowler_rows = table_body.find_all('tr', recursive=False)
    logging.debug(f"Match {match_id} Inn {innings_num}: Processing {len(bowler_rows)} rows in bowling tbody.")
    for j, bowler_row in enumerate(bowler_rows):
        first_cell = bowler_row.find('td')
        if not first_cell or not first_cell.find('a', href=re.compile(r'/cricketers/')) or any(c in bowler_row.get('class', []) for c in ['ds-bg-fill-content-alternate', 'ds-text-tight-s']):
            logging.debug(f"Skipping bowl row {j + 1} (likely not a bowler stats row)."); continue
        bowler_data = {'Match ID': match_id, 'Innings': innings_num, 'Bowling Team': bowling_team}
        try:
            bowl_cols = bowler_row.find_all('td', recursive=False)
             # !!! Verify BOWLING_COL_INDICES for 2025 !!!
            max_expected_bowl_col = max(BOWLING_COL_INDICES.values()) if BOWLING_COL_INDICES else 0
            if len(bowl_cols) < max_expected_bowl_col: logging.warning(f"Bowl Row {j + 1}: Need >= {max_expected_bowl_col} cells, found {len(bowl_cols)}. Skipping."); continue
            bowler_cell = bowl_cols[BOWLING_COL_INDICES.get('Bowler', 1) - 1]
            name, p_id, href = extract_player_info(bowler_cell)
            bowler_data['Bowler'] = name; bowler_data['Bowler id'] = p_id;
            bowler_data['Over bowled'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('Overs', 2) - 1]) # Verify index
            bowler_data['Maiden Over'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('Mdns', 3) - 1]) # Verify index
            bowler_data['Run given'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('Runs', 4) - 1]) # Verify index
            wicket_cell = bowl_cols[BOWLING_COL_INDICES.get('Wkts', 5) - 1] # Verify index
            # !!! Verify wicket element selector for 2025 !!!
            wicket_element = wicket_cell.select_one(BOWLING_WICKET_SELECTOR) if wicket_cell else None
            bowler_data['Wicket taken'] = safe_get_text(wicket_element if wicket_element else wicket_cell)
            bowler_data['Economy rate'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('Econ', 6) - 1]) # Verify index
            bowler_data['Dot balls'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('Dots', 7) - 1]) # Verify index
            bowler_data['Fours'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('4s', 8) - 1]) # Verify index
            bowler_data['Sixes'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('6s', 9) - 1]) # Verify index
            bowler_data['Wides'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('WD', 10) - 1]) # Verify index
            bowler_data['No balls'] = safe_get_text(bowl_cols[BOWLING_COL_INDICES.get('NB', 11) - 1]) # Verify index
            bowling_details.append(bowler_data)
        except IndexError:
             logging.error(f"Match {match_id} Inn {innings_num}: IndexError processing bowling row {j + 1} for {bowler_data.get('Bowler', 'UNKNOWN')}. Found {len(bowl_cols)} cells. Row HTML: {bowler_row.prettify()}", exc_info=True)
        except Exception as e:
            logging.error(f"Match {match_id} Inn {innings_num}: Error processing bowling row {j + 1} for {bowler_data.get('Bowler', 'UNKNOWN')}: {e}", exc_info=True)
    return bowling_details

def scrape_scorecard_details(driver: WebDriver, scorecard_rel_url: str, match_id: str) -> (list, list, bool): # Added success flag
    """Scrapes scorecard details using the specific table body selectors. Returns (batting_list, bowling_list, success_flag)."""
    # (!!! This function likely needs verification/updates based on 2025 scorecard structure !!!)
    full_url = urljoin(BASE_CRICINFO_URL, scorecard_rel_url)
    logging.info(f"Scraping scorecard Match ID {match_id} from: {full_url}")
    all_batting, all_bowling = [], []
    team1_name, team2_name = "Team_1_Unknown", "Team_2_Unknown"
    success = False # Initialize success flag
    try:
        driver.get(full_url);
        logging.info(f"Waiting up to {WAIT_TIME}s for scorecard container: '{SCORECARD_WAIT_SELECTOR}'")
        WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, SCORECARD_WAIT_SELECTOR)))
        # !!! Verify wait condition and selector for 2025 scorecards !!!
        # Increased wait time slightly and wait for a more specific element if possible
        logging.info(f"Waiting up to {WAIT_TIME + 10}s for Innings 1 Batting Table: '{INNINGS_1_BATTING_TABLE_SELECTOR}'")
        WebDriverWait(driver, WAIT_TIME + 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, INNINGS_1_BATTING_TABLE_SELECTOR)))
        time.sleep(random.uniform(3.0, 5.0)) # Increased sleep
        page_soup = BeautifulSoup(driver.page_source, 'lxml')

        # --- Innings 1 ---
        logging.info(f"Match {match_id}: Processing Innings 1...")
        # !!! Verify selectors for 2025 !!!
        team1_name_tag = page_soup.select_one(INNINGS_1_BATTING_TEAM_SELECTOR)
        if team1_name_tag: team1_name = safe_get_text(team1_name_tag, default=team1_name)
        else: logging.warning(f"Match {match_id} Inn 1: Batting team name selector not found. Check: {INNINGS_1_BATTING_TEAM_SELECTOR}")
        logging.info(f"  Innings 1 Batting Team: {team1_name}")
        batting_table_1 = page_soup.select_one(INNINGS_1_BATTING_TABLE_SELECTOR)
        bowl_table_1 = page_soup.select_one(INNINGS_1_BOWLING_TABLE_SELECTOR)
        bat_body_1 = batting_table_1.find('tbody') if batting_table_1 else None
        bowl_body_1 = bowl_table_1.find('tbody') if bowl_table_1 else None
        innings1_bat_processed = False; innings1_bowl_processed = False
        if not bat_body_1: logging.error(f"Match {match_id} Inn 1: BATTING TBODY NOT FOUND using selector {INNINGS_1_BATTING_TABLE_SELECTOR}")
        else: all_batting.extend(_process_batting_table(bat_body_1, match_id, 1, team1_name)); innings1_bat_processed = True
        if not bowl_body_1: logging.error(f"Match {match_id} Inn 1: BOWLING TBODY NOT FOUND using selector {INNINGS_1_BOWLING_TABLE_SELECTOR}")
        else: all_bowling.extend(_process_bowling_table(bowl_body_1, match_id, 1, "TBC_Opponent")); innings1_bowl_processed = True

        # --- Innings 2 ---
        logging.info(f"Match {match_id}: Processing Innings 2...")
         # !!! Verify selectors for 2025 !!!
        team2_name_tag = page_soup.select_one(INNINGS_2_BATTING_TEAM_SELECTOR)
        if team2_name_tag: team2_name = safe_get_text(team2_name_tag, default=team2_name)
        else: logging.warning(f"Match {match_id} Inn 2: Batting team name selector not found. Check: {INNINGS_2_BATTING_TEAM_SELECTOR}")
        logging.info(f"  Innings 2 Batting Team: {team2_name}")
        batting_table_2 = page_soup.select_one(INNINGS_2_BATTING_TABLE_SELECTOR)
        bowl_table_2 = page_soup.select_one(INNINGS_2_BOWLING_TABLE_SELECTOR)
        bat_body_2 = batting_table_2.find('tbody') if batting_table_2 else None
        bowl_body_2 = bowl_table_2.find('tbody') if bowl_table_2 else None
        innings2_bat_processed = False; innings2_bowl_processed = False
        # Check if second innings exists before trying to process
        if batting_table_2 and bowl_table_2:
            if not bat_body_2: logging.error(f"Match {match_id} Inn 2: BATTING TBODY NOT FOUND using selector {INNINGS_2_BATTING_TABLE_SELECTOR}")
            else: all_batting.extend(_process_batting_table(bat_body_2, match_id, 2, team2_name)); innings2_bat_processed = True
            if not bowl_body_2: logging.error(f"Match {match_id} Inn 2: BOWLING TBODY NOT FOUND using selector {INNINGS_2_BOWLING_TABLE_SELECTOR}")
            else: all_bowling.extend(_process_bowling_table(bowl_body_2, match_id, 2, team1_name)); innings2_bowl_processed = True
        else:
             logging.info(f"Match {match_id}: Innings 2 tables not found (selectors: Bat='{INNINGS_2_BATTING_TABLE_SELECTOR}', Bowl='{INNINGS_2_BOWLING_TABLE_SELECTOR}'). Assuming only 1 innings or structure change.")


        # Post-process Bowling Team Name for Innings 1
        if team2_name != "Team_2_Unknown":
            updated_count = 0
            for record in all_bowling:
                if record['Match ID'] == match_id and record['Innings'] == 1 and record['Bowling Team'] == "TBC_Opponent":
                    record['Bowling Team'] = team2_name; updated_count += 1
            if updated_count > 0: logging.debug(f"Updated Inn 1 bowling team name to '{team2_name}' for {updated_count} records.")
        else: logging.warning(f"Match {match_id}: Could not determine Team 2 name to update Innings 1 bowling team.")

        # Consider successful if we managed to find and process at least one innings table
        # Adjusted to be more lenient if only Innings 1 exists/is found
        if innings1_bat_processed or innings1_bowl_processed:
             success = True
        elif innings2_bat_processed or innings2_bowl_processed: # Success if Inn2 processed even if Inn1 failed
             success = True
        else:
             logging.error(f"Failed to process any innings table for Match ID: {match_id}")
             success = False

    except TimeoutException:
        logging.error(f"Timed out waiting for elements on scorecard page {match_id}")
        success = False
    except Exception as e:
        logging.error(f"Failed scorecard scrape {match_id}: {e}", exc_info=True)
        success = False
    return all_batting, all_bowling, success

# --- Main Execution Logic ---
if __name__ == "__main__":
    overall_start_time = time.time(); driver = None; season_summary_data = [];
    master_batting_list = []; master_bowling_list = []
    failed_scorecards = []
    df_season_summary = None # Initialize DataFrame variable

    try:
        driver = setup_driver()
        season_url_part = format_season_string(TARGET_SEASON) # Will produce '2025-2025'

        # --- Stage 1: Scrape Season Summary ---
        logging.info(f"\n--- STAGE 1: Scraping Match Summary for Season {TARGET_SEASON} ---") # Updated log
        season_summary_data = scrape_season_summary(driver, TARGET_SEASON, season_url_part)

        # --- Process and Save Season Summary ---
        if season_summary_data:
            try:
                df_season_summary = pd.DataFrame(season_summary_data);
                initial_rows = df_season_summary.shape[0]
                df_season_summary.dropna(subset=['Match ID', 'Scorecard Link'], inplace=True)
                final_rows = df_season_summary.shape[0]
                if initial_rows > final_rows: logging.warning(f"Dropped {initial_rows - final_rows} rows from season summary due to missing Match ID or Scorecard Link.")

                if df_season_summary.empty:
                    logging.error(f"EXITING: No valid match summary data with Match IDs found for {TARGET_SEASON} after initial processing and dropna.");
                    # Set df_season_summary back to None to prevent further processing
                    df_season_summary = None
                else:
                    logging.info(f"Season Summary DF processed: {df_season_summary.shape[0]} valid rows.")
                    summary_cols_ordered = ['Season', 'Match ID', 'Team 1', 'Team 2', 'Winner', 'Net Margin', 'Margin Type', 'Ground Name', 'Ground ID', 'Match Date', 'Scorecard Link', 'Margin Raw']
                    for col in summary_cols_ordered: df_season_summary[col] = df_season_summary.get(col, pd.NA)
                    df_season_summary = df_season_summary[summary_cols_ordered]
                    try: df_season_summary['Match Date'] = pd.to_datetime(df_season_summary['Match Date'], errors='coerce'); logging.info("Cleaned Match Date")
                    except Exception as e: logging.warning(f"Date conversion failed: {e}")
                    sum_num_cols = ['Net Margin', 'Ground ID', 'Match ID'];
                    df_season_summary[sum_num_cols] = df_season_summary[sum_num_cols].apply(pd.to_numeric, errors='coerce');
                    logging.info("Cleaned summary numeric types.")
                    print(f"\n--- Full Match Summary Table for Season {TARGET_SEASON} ---"); # Updated print
                    pd.set_option('display.max_rows', len(df_season_summary) + 10); pd.set_option('display.max_columns', None); pd.set_option('display.width', 3000);
                    print(df_season_summary.to_string(index=False)); print("--- End Summary Table ---")
                    # Save to DATA_DIR using updated path
                    df_season_summary.to_csv(SEASON_SUMMARY_CSV_PATH, index=False, encoding='utf-8-sig');
                    logging.info(f"Saved season summary: {SEASON_SUMMARY_CSV_PATH}"); print(f"\nSeason summary saved: {SEASON_SUMMARY_CSV_PATH}")

            except Exception as e:
                 logging.error(f"Error processing/saving season summary: {e}", exc_info=True);
                 logging.error(f"EXITING due to error processing season summary.");
                 df_season_summary = None # Ensure df is None on error

        # --- Check if summary processing was successful before proceeding ---
        if df_season_summary is None or df_season_summary.empty:
             logging.error(f"EXITING: No valid season summary data processed for {TARGET_SEASON}. Cannot proceed to scorecard scraping.")
        else:
            # --- Only proceed if df_season_summary is valid ---
            df_season_summary['Match ID'] = df_season_summary['Match ID'].astype(str)
            valid_matches = df_season_summary.to_dict('records')

            # --- Stage 2: Scrape Scorecard Details (All Matches) ---
            if not valid_matches: logging.error(f"EXITING: No matches with valid IDs/Links found in summary for {TARGET_SEASON} after processing. Cannot proceed."); # Updated log
            else:
                matches_to_process = valid_matches # Process all valid matches
                total_matches = len(matches_to_process)
                logging.info(f"\n--- STAGE 2: Processing Scorecard Details for {total_matches} Valid Matches ---")
                for i, match_info in enumerate(matches_to_process):
                    match_id = match_info.get('Match ID'); scorecard_link = match_info.get('Scorecard Link')
                    if pd.isna(match_id) or pd.isna(scorecard_link): logging.warning(f"Skipping scorecard {i + 1}/{total_matches} (redundant check: missing ID/Link)."); continue
                    logging.info(f"\n--- Processing Scorecard {i + 1}/{total_matches} (Match ID: {match_id}) ---")
                    batting_data, bowling_data, success = scrape_scorecard_details(driver, scorecard_link, str(match_id))
                    if success:
                        master_batting_list.extend(batting_data); master_bowling_list.extend(bowling_data)
                    else:
                        logging.warning(f"Scorecard scrape failed for Match ID: {match_id}. Will retry later if enabled.")
                        if RETRY_FAILED_SCORECARDS: failed_scorecards.append(match_info)
                    if i < total_matches - 1:
                        sleep_duration = random.uniform(SCORECARD_SLEEP_MIN, SCORECARD_SLEEP_MAX);
                        logging.info(f"--- Delaying {sleep_duration:.2f}s ---"); time.sleep(sleep_duration)

                # --- Stage 3: Retry Failed Scorecards ---
                if RETRY_FAILED_SCORECARDS and failed_scorecards:
                    logging.info(f"\n--- STAGE 3: Retrying {len(failed_scorecards)} Failed Scorecards ---")
                    for i, match_info in enumerate(failed_scorecards):
                        match_id = match_info.get('Match ID'); scorecard_link = match_info.get('Scorecard Link')
                        logging.info(f"\n--- Retrying Scorecard {i + 1}/{len(failed_scorecards)} (Match ID: {match_id}) ---")
                        batting_data, bowling_data, success = scrape_scorecard_details(driver, scorecard_link, str(match_id))
                        if success:
                            logging.info(f"Retry successful for Match ID: {match_id}")
                            master_batting_list.extend(batting_data); master_bowling_list.extend(bowling_data)
                        else: logging.error(f"Retry FAILED for Match ID: {match_id}.")
                        if i < len(failed_scorecards) - 1:
                            sleep_duration = random.uniform(SCORECARD_SLEEP_MIN, SCORECARD_SLEEP_MAX);
                            logging.info(f"--- Delaying {sleep_duration:.2f}s ---"); time.sleep(sleep_duration)
                elif RETRY_FAILED_SCORECARDS: logging.info("\n--- STAGE 3: No failed scorecards to retry ---")

    except Exception as e:
        logging.critical(f"Critical error in main execution block: {e}", exc_info=True)
    finally:
        if driver:
            try:
                logging.info("Quitting WebDriver...");
                driver.quit();
                logging.info("WebDriver closed successfully.")
            except Exception as quit_err:
                logging.error(f"Error closing WebDriver: {quit_err}")

    # --- Process and Save Detailed Data ---
    logging.info(f"\n--- Processing and Saving Detailed Scorecard Data ---")
    # Process Batting
    if master_batting_list:
        try:
            df_batting = pd.DataFrame(master_batting_list);
            # Add a more robust check for duplicates if needed, e.g., based on player ID if available
            df_batting.drop_duplicates(subset=['Match ID', 'Innings', 'Batter', 'Run Scored', 'Ball faced'], keep='last', inplace=True)
            logging.info(f"Created Batting DataFrame: {df_batting.shape[0]} unique rows.")
            batting_cols_ordered = ['Match ID', 'Innings', 'Batting Team', 'Batter', 'Batter id', 'Run Scored', 'Ball faced', 'Fours', 'Sixes', 'Strike rate', 'Dismissal Type', 'Dismissal Player', 'Dismissal Bowler']
            # Ensure all columns exist, adding missing ones with NA
            for col in batting_cols_ordered:
                 if col not in df_batting.columns:
                     df_batting[col] = pd.NA
            df_batting = df_batting[batting_cols_ordered] # Reorder
            bat_numeric_cols = ['Batter id', 'Run Scored', 'Ball faced', 'Fours', 'Sixes', 'Strike rate'];
            cols_to_convert = [col for col in bat_numeric_cols if col in df_batting.columns]
            if cols_to_convert:
                df_batting[cols_to_convert] = df_batting[cols_to_convert].fillna(pd.NA)
                df_batting[cols_to_convert] = df_batting[cols_to_convert].apply(pd.to_numeric, errors='coerce');
                logging.info(f"Converted detailed batting numeric cols: {cols_to_convert}")
            else: logging.warning("No numeric batting columns found to convert.")
            # Save to DATA_DIR using updated path
            df_batting.to_csv(BATTING_CSV_PATH, index=False, encoding='utf-8-sig');
            logging.info(f"Saved detailed batting data: {BATTING_CSV_PATH}"); print(f"\nDetailed batting data saved: {BATTING_CSV_PATH}")
            print("\n--- Detailed Batting Performance Table (Head) ---"); pd.set_option('display.max_rows', 40);
            print(df_batting.head(30).to_string(index=False, na_rep='<NA>')); print("--- End Detailed Batting Head ---")
        except Exception as e: logging.error(f"Error processing/saving detailed batting data: {e}", exc_info=True)
    else: logging.warning("No detailed batting data collected."); print("\n--- No detailed batting data collected/saved. ---")
    # Process Bowling
    if master_bowling_list:
        try:
            df_bowling = pd.DataFrame(master_bowling_list);
            df_bowling.drop_duplicates(subset=['Match ID', 'Innings', 'Bowler', 'Over bowled', 'Run given', 'Wicket taken'], keep='last', inplace=True)
            logging.info(f"Created Bowling DataFrame: {df_bowling.shape[0]} unique rows.")
            bowling_cols_ordered = ['Match ID', 'Innings', 'Bowling Team', 'Bowler', 'Bowler id', 'Over bowled', 'Maiden Over', 'Run given', 'Wicket taken', 'Economy rate', 'Wides', 'No balls', 'Dot balls', 'Fours', 'Sixes']
            # Ensure all columns exist, adding missing ones with NA
            for col in bowling_cols_ordered:
                 if col not in df_bowling.columns:
                     df_bowling[col] = pd.NA
            df_bowling = df_bowling[bowling_cols_ordered] # Reorder
            bowl_numeric_cols = ['Bowler id', 'Over bowled', 'Maiden Over', 'Run given', 'Wicket taken', 'Economy rate', 'Wides', 'No balls', 'Dot balls', 'Fours', 'Sixes'];
            cols_to_convert = [col for col in bowl_numeric_cols if col in df_bowling.columns]
            if cols_to_convert:
                 df_bowling[cols_to_convert] = df_bowling[cols_to_convert].fillna(pd.NA)
                 df_bowling[cols_to_convert] = df_bowling[cols_to_convert].apply(pd.to_numeric, errors='coerce');
                 logging.info(f"Converted detailed bowling numeric cols: {cols_to_convert}")
            else: logging.warning("No numeric bowling columns found to convert.")
            # Save to DATA_DIR using updated path
            df_bowling.to_csv(BOWLING_CSV_PATH, index=False, encoding='utf-8-sig');
            logging.info(f"Saved detailed bowling data: {BOWLING_CSV_PATH}"); print(f"\nDetailed bowling data saved: {BOWLING_CSV_PATH}")
            print("\n--- Detailed Bowling Performance Table (Head) ---"); pd.set_option('display.max_rows', 40);
            print(df_bowling.head(30).to_string(index=False, na_rep='<NA>')); print("--- End Detailed Bowling Head ---")
        except Exception as e: logging.error(f"Error processing/saving detailed bowling data: {e}", exc_info=True)
    else: logging.warning("No detailed bowling data collected."); print("\n--- No detailed bowling data collected/saved. ---")

    overall_end_time = time.time(); total_duration = overall_end_time - overall_start_time;
    logging.info(f"\nScript finished execution in {total_duration:.2f} seconds."); logging.info("--- Script End ---");
    print(f"\nScript finished in {total_duration:.2f} seconds.")
    # Use sys.exit(0) for a cleaner exit in case of early termination
    if df_season_summary is None or df_season_summary.empty:
        sys.exit(1) # Indicate an error exit code
    else:
        sys.exit(0) # Indicate successful completion (or completion after processing what was found)

