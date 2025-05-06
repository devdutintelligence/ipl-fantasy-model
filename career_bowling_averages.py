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
from datetime import datetime # Import the datetime class itself
import logging
import os
import random
import re # Import regex module

# --- Player Data (Same as before) ---
PLAYER_DATA = [
    {'id': '1060380', 'name': 'RD Gaikwad'}, {'id': '1125688', 'name': 'Mukesh Choudhary'}, {'id': '1182529', 'name': 'Noor Ahmad'}, {'id': '1194795', 'name': 'M Pathirana'}, {'id': '234675', 'name': 'RA Jadeja'}, {'id': '26421', 'name': 'R Ashwin'}, {'id': '28081', 'name': 'MS Dhoni'}, {'id': '379140', 'name': 'DP Conway'}, {'id': '446763', 'name': 'RA Tripathi'}, {'id': '477021', 'name': 'V Shankar'}, {'id': '497121', 'name': 'DJ Hooda'}, {'id': '510530', 'name': 'J Overton'}, {'id': '662973', 'name': 'SM Curran'}, {'id': '714451', 'name': 'S Dube'}, {'id': '826915', 'name': 'NT Ellis'}, {'id': '942645', 'name': 'KK Ahmed'}, {'id': '959767', 'name': 'R Ravindra'}, {'id': '1131978', 'name': 'AR Sharma'}, {'id': '1168049', 'name': 'J Fraser-McGurk'}, {'id': '1175489', 'name': 'Sameer Rizvi'}, {'id': '1277545', 'name': 'Abishek Porel'}, {'id': '1449074', 'name': 'V Nigam'}, {'id': '311592', 'name': 'MA Starc'}, {'id': '422108', 'name': 'KL Rahul'}, {'id': '44828', 'name': 'F du Plessis'}, {'id': '537119', 'name': 'MM Sharma'}, {'id': '554691', 'name': 'AR Patel'}, {'id': '559235', 'name': 'Kuldeep Yadav'}, {'id': '595978', 'name': 'T Stubbs'}, {'id': '926851', 'name': 'Mukesh Kumar'}, {'id': '1048739', 'name': 'R Sai Kishore'}, {'id': '1070173', 'name': 'Shubman Gill'}, {'id': '1151288', 'name': 'B Sai Sudharsan'}, {'id': '1244751', 'name': 'Arshad Khan'}, {'id': '236779', 'name': 'I Sharma'}, {'id': '308967', 'name': 'JC Buttler'}, {'id': '423838', 'name': 'R Tewatia'}, {'id': '550215', 'name': 'K Rabada'}, {'id': '719715', 'name': 'Washington Sundar'}, {'id': '719719', 'name': 'M Shahrukh Khan'}, {'id': '793463', 'name': 'Rashid Khan'}, {'id': '914541', 'name': 'SE Rutherford'}, {'id': '917159', 'name': 'M Prasidh Krishna'}, {'id': '940973', 'name': 'Mohammed Siraj'}, {'id': '1070196', 'name': 'Yash Thakur'}, {'id': '1125976', 'name': 'Arshdeep Singh'}, {'id': '1151273', 'name': 'N Wadhera'}, {'id': '1161024', 'name': 'Prabhsimran Singh'}, {'id': '1175456', 'name': 'P Arya'}, {'id': '1339698', 'name': 'Suryansh Shedge'}, {'id': '325012', 'name': 'MP Stoinis'}, {'id': '325026', 'name': 'GJ Maxwell'}, {'id': '377534', 'name': 'Shashank Singh'}, {'id': '430246', 'name': 'YS Chahal'}, {'id': '493773', 'name': 'LH Ferguson'}, {'id': '642519', 'name': 'SS Iyer'}, {'id': '696401', 'name': 'M Jansen'}, {'id': '777815', 'name': 'V Vyshak'}, {'id': '819429', 'name': 'Azmatullah Omarzai'}, {'id': '1079470', 'name': 'Ramandeep Singh'}, {'id': '1108375', 'name': 'CV Varun'}, {'id': '1123718', 'name': 'SH Johnson'}, {'id': '1209292', 'name': 'VG Arora'}, {'id': '1292495', 'name': 'A Raghuvanshi'}, {'id': '1312645', 'name': 'Harshit Rana'}, {'id': '230558', 'name': 'SP Narine'}, {'id': '276298', 'name': 'AD Russell'}, {'id': '277916', 'name': 'AM Rahane'}, {'id': '290630', 'name': 'MK Pandey'}, {'id': '379143', 'name': 'Q de Kock'}, {'id': '723105', 'name': 'RK Singh'}, {'id': '851403', 'name': 'VR Iyer'}, {'id': '8917', 'name': 'MM Ali'}, {'id': '1151270', 'name': 'A Badoni'}, {'id': '1151286', 'name': 'M Siddharth'}, {'id': '1159711', 'name': 'Shahbaz Ahmed'}, {'id': '1175441', 'name': 'Ravi Bishnoi'}, {'id': '1175485', 'name': 'Abdul Samad'}, {'id': '1176959', 'name': 'Akash Deep'}, {'id': '1350768', 'name': 'Prince Yadav'}, {'id': '1460529', 'name': 'DS Rathi'}, {'id': '272450', 'name': 'MR Marsh'}, {'id': '321777', 'name': 'DA Miller'}, {'id': '475281', 'name': 'SN Thakur'}, {'id': '600498', 'name': 'AK Markram'}, {'id': '604302', 'name': 'N Pooran'}, {'id': '694211', 'name': 'Avesh Khan'}, {'id': '931581', 'name': 'RR Pant'}, {'id': '1170265', 'name': 'NT Tilak Varma'}, {'id': '1209126', 'name': 'Ashwani Kumar'}, {'id': '1287032', 'name': 'Naman Dhir'}, {'id': '1292502', 'name': 'RA Bawa'}, {'id': '1350762', 'name': 'R Minz'}, {'id': '1392201', 'name': 'PVSN Raju'}, {'id': '1460388', 'name': 'V Puthur'}, {'id': '277912', 'name': 'TA Boult'}, {'id': '34102', 'name': 'RG Sharma'}, {'id': '446507', 'name': 'SA Yadav'}, {'id': '447261', 'name': 'DL Chahar'}, {'id': '502714', 'name': 'MJ Santner'}, {'id': '605661', 'name': 'RD Rickelton'}, {'id': '625371', 'name': 'HH Pandya'}, {'id': '625383', 'name': 'JJ Bumrah'}, {'id': '897549', 'name': 'WG Jacks'}, {'id': '974109', 'name': 'Mujeeb Ur Rahman'}, {'id': '1079434', 'name': 'R Parag'}, {'id': '1138316', 'name': 'M Theekshana'}, {'id': '1151278', 'name': 'YBK Jaiswal'}, {'id': '1159843', 'name': 'K Kartikeya'}, {'id': '1175488', 'name': 'DC Jurel'}, {'id': '1206052', 'name': 'Yudhvir Singh'}, {'id': '1252585', 'name': 'SB Dubey'}, {'id': '425943', 'name': 'SV Samson'}, {'id': '438362', 'name': 'Sandeep Sharma'}, {'id': '604527', 'name': 'N Rana'}, {'id': '669855', 'name': 'JC Archer'}, {'id': '670025', 'name': 'SO Hetmyer'}, {'id': '784379', 'name': 'PW Hasaranga'}, {'id': '822553', 'name': 'TU Deshpande'}, {'id': '974175', 'name': 'Fazalhaq Farooqi'}, {'id': '1119026', 'name': 'D Padikkal'}, {'id': '1159720', 'name': 'Yash Dayal'}, {'id': '1161489', 'name': 'Rasikh Salam'}, {'id': '1350792', 'name': 'Suyash Sharma'}, {'id': '253802', 'name': 'V Kohli'}, {'id': '288284', 'name': 'JR Hazlewood'}, {'id': '326016', 'name': 'B Kumar'}, {'id': '403902', 'name': 'LS Livingstone'}, {'id': '471342', 'name': 'KH Pandya'}, {'id': '669365', 'name': 'PD Salt'}, {'id': '721867', 'name': 'JM Sharma'}, {'id': '823703', 'name': 'RM Patidar'}, {'id': '892749', 'name': 'TH David'}, {'id': '1070183', 'name': 'Abhishek Sharma'}, {'id': '1159722', 'name': 'Simarjeet Singh'}, {'id': '1175496', 'name': 'K Nitish Kumar Reddy'}, {'id': '1409976', 'name': 'AU Verma'}, {'id': '379504', 'name': 'A Zampa'}, {'id': '390481', 'name': 'HV Patel'}, {'id': '390484', 'name': 'JD Unadkat'}, {'id': '436757', 'name': 'H Klaasen'}, {'id': '481896', 'name': 'Mohammed Shami'}, {'id': '489889', 'name': 'PJ Cummins'}, {'id': '530011', 'name': 'TM Head'}, {'id': '698189', 'name': 'PWA Mulder'}, {'id': '720471', 'name': 'Ishan Kishan'}, {'id': '778963', 'name': 'A Manohar'}, {'id': '784373', 'name': 'PHKD Mendis'}, {'id': '942371', 'name': 'Zeeshan Ansari'}
]

# --- Configuration ---
# UPDATED URL for Bowling stats
BASE_URL = 'https://stats.espncricinfo.com/ci/engine/player/{player_id}.html?class=6;template=results;type=bowling'
OUTPUT_DIR = "Career_Averages_Output" # UPDATED directory name
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Table selector remains the same as it's the 4th table on the page for both
CAREER_STATS_TABLE_SELECTOR = '#ciHomeContentlhs > div.pnl650M > table:nth-child(4)'
# Define CSV Output file path (UPDATED Filename)
OUTPUT_CSV_FILENAME = "career_bowling_averages.csv" # CHANGED FILENAME
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, OUTPUT_CSV_FILENAME)
# Span check constants remain the same
SPAN_HEADER_SELECTOR = f"{CAREER_STATS_TABLE_SELECTOR} > thead > tr > th:nth-child(2)"
EXPECTED_SPAN_TITLE_TEXT = "playing span"

# --- Logging Setup ---
log_filename = os.path.join(OUTPUT_DIR, f"career_bowling_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log") # UPDATED log filename
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
# Reduce verbosity of external libraries
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)

current_time_system = datetime.now()
current_date_system = current_time_system.date()
current_time_str = current_time_system.strftime('%Y-%m-%d %H:%M:%S %Z')

logging.info(f"Log file: {log_filename}")
logging.info(f"Script started at: {current_time_str} (System Time - IST)")
logging.info(f"Current Date according to system: {current_date_system}")
# UPDATED Log message
logging.info(f"Processing {len(PLAYER_DATA)} players for Career Bowling Averages.")
logging.info(f"Targeting table with selector: {CAREER_STATS_TABLE_SELECTOR}")
logging.info(f"Output CSV will be saved to: {OUTPUT_CSV_PATH}")
logging.info(f"Players will be skipped if Span header (th:nth-child(2)) title doesn't contain '{EXPECTED_SPAN_TITLE_TEXT}' OR if Span data cell is empty.")


# --- Helper Functions ---
def safe_get_text(element, default='N/A'):
    """Safely extracts text from a BeautifulSoup Tag or returns default."""
    if isinstance(element, Tag): text = element.get_text(strip=True); return text if text else default
    elif isinstance(element, str): return element.strip()
    # Return pd.NA if element is None or empty string, else string representation
    # Using pd.NA helps with subsequent numeric conversions
    if element is None:
        return pd.NA
    text = str(element).strip()
    return text if text else pd.NA # Return NA for empty strings too

def parse_bbi(bbi_string):
    """
    Parses a 'W/R' string (e.g., '3/15') into wickets and runs.
    Returns (wickets, runs) as integers, or (pd.NA, pd.NA) on failure.
    """
    # Use safe_get_text's NA handling
    if pd.isna(bbi_string) or bbi_string == '-':
         # logging.debug(f"BBI parsing: Input '{bbi_string}' is NA or placeholder.")
         return pd.NA, pd.NA

    if '/' not in bbi_string:
        logging.warning(f"BBI parsing: Expected format 'W/R' not found in '{bbi_string}'.")
        return pd.NA, pd.NA

    parts = bbi_string.split('/')
    if len(parts) != 2:
        logging.warning(f"BBI parsing: Unexpected number of parts ({len(parts)}) after splitting '{bbi_string}' by '/'.")
        return pd.NA, pd.NA

    try:
        # Extract only digits using regex before converting
        wkts_str = re.search(r'\d+', parts[0])
        runs_str = re.search(r'\d+', parts[1])

        if wkts_str and runs_str:
             wkts = int(wkts_str.group(0))
             runs = int(runs_str.group(0))
             # logging.debug(f"BBI parsing: Parsed '{bbi_string}' -> Wkts: {wkts}, Runs: {runs}")
             return wkts, runs
        else:
             logging.warning(f"BBI parsing: Could not extract numeric parts from '{parts[0]}' or '{parts[1]}'.")
             return pd.NA, pd.NA
    except ValueError:
        logging.warning(f"BBI parsing: Could not convert parts of '{bbi_string}' to integers.")
        return pd.NA, pd.NA
    except Exception as e:
        logging.error(f"BBI parsing: Unexpected error parsing '{bbi_string}': {e}")
        return pd.NA, pd.NA


# --- Driver Setup (Same as before) ---
def setup_driver():
    """Sets up the undetected_chromedriver with options and retries."""
    driver = None; retries = 3; last_exception = None
    for attempt in range(retries):
        logging.info(f"Attempting to initialize WebDriver (Attempt {attempt + 1}/{retries})...")
        try:
            options = uc.ChromeOptions()
            # options.add_argument('--headless=new') # Enable for headless
            options.add_argument("--start-maximized"); options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage")
            options.add_argument('--log-level=3'); options.add_argument("--disable-gpu"); options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars"); options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            driver = uc.Chrome(options=options, enable_cdp_events=True, version_main=None)
            logging.info("Browser driver setup successful.")
            return driver
        except Exception as e:
            last_exception = e; logging.warning(f"Failed WebDriver init attempt {attempt + 1}: {e}")
            if attempt < retries - 1: logging.info("Retrying after 5 seconds..."); time.sleep(5)
            else: logging.error("Max retries reached for WebDriver init."); raise last_exception
    if driver is None and last_exception: raise last_exception
    return driver


# --- UPDATED Function to Scrape Career BOWLING Stats ---
def scrape_player_career_bowling_stats(driver: WebDriver, player_id: str, player_name: str) -> dict | None:
    """
    Scrapes career BOWLING stats for a specific player.
    1. Checks if Span header (th:nth-child(2)) exists and title contains 'playing span'.
    2. Checks if Span data cell (td:nth-child(2)) is non-empty.
    3. Parses BBI column ('W/R') into separate Wkts and Runs columns.
    Skips player if header/span checks fail. Returns dict or None.
    """
    target_url = BASE_URL.format(player_id=player_id) # URL now points to bowling stats
    logging.info(f"Attempting to scrape career bowling stats for {player_name} from: {target_url}")
    bowling_data = {} # Renamed dict

    # UPDATED Column mapping for BOWLING stats based on user selectors
    column_mapping = {
        'Span': 2,      'Matches': 3,   'Innings': 4,   'Overs': 5,     'Mdns': 6,
        'Runs': 7,      'Wkts': 8,      'BBI': 9,       'Ave': 10,      'Econ': 11,
        'SR': 12,       '4w': 13,       '5w': 14
    }
    format_col_index = 1
    span_col_index = column_mapping['Span'] # Still 2
    bbi_col_index = column_mapping['BBI']   # Index 9 for BBI
    # Calculate max index needed based on the mapping
    max_index = max(v for k, v in column_mapping.items())


    try:
        driver.get(target_url)
        wait_time = 20

        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#ciHomeContentlhs > div.pnl650M'))
        )
        time.sleep(random.uniform(1.0, 2.0))

        page_soup = BeautifulSoup(driver.page_source, 'lxml')

        # --- Step 1: Check the Span Header Cell (Same Logic) ---
        span_header_cell = page_soup.select_one(SPAN_HEADER_SELECTOR)
        if not span_header_cell:
            logging.warning(f"Skipping {player_name} (ID: {player_id}): Could not find the expected Span header cell (th:nth-child(2)) using selector: {SPAN_HEADER_SELECTOR}")
            return None
        title_attr = span_header_cell.get('title')
        if not title_attr or EXPECTED_SPAN_TITLE_TEXT not in title_attr.lower():
            logging.warning(f"Skipping {player_name} (ID: {player_id}): Span header cell found, but its title attribute ('{title_attr}') does not contain '{EXPECTED_SPAN_TITLE_TEXT}'.")
            return None
        logging.debug(f"Span header check passed for {player_name}.")

        # --- Header check passed, find table and data row ---
        data_table = page_soup.select_one(CAREER_STATS_TABLE_SELECTOR)
        if not data_table:
            logging.error(f"Could not find career stats table for {player_name} even after header check passed. Skipping.")
            return None
        table_body = data_table.find('tbody')
        if not table_body:
            logging.warning(f"Could not find table body (tbody) for career stats for {player_name}. Skipping.")
            return None
        data_rows = table_body.find_all('tr', recursive=False)
        if not data_rows:
             logging.warning(f"No data rows found in tbody for career stats for {player_name}. Skipping.")
             return None
        summary_row = data_rows[0]
        cols = summary_row.find_all('td', recursive=False)

        # Check column count against the *new* max_index from bowling mapping
        if not cols or len(cols) < max_index:
            logging.warning(f"Career bowling summary row for {player_name} has insufficient columns ({len(cols)} found, need at least {max_index}). Skipping.")
            return None

        # --- Step 2: Check the Span Data Cell (Same Logic) ---
        span_cell_index_0_based = span_col_index - 1 # Index 1
        if span_cell_index_0_based < len(cols):
            span_text = safe_get_text(cols[span_cell_index_0_based]).strip() # Use strip() on the result of safe_get_text if it's a string
            # Check if span_text is NA or empty string
            if pd.isna(span_text) or span_text == "":
                logging.warning(f"Skipping player {player_name} (ID: {player_id}): Header check passed, but Span data cell (td:nth-child(2)) is missing or empty.")
                return None
            logging.debug(f"Span data cell check passed for {player_name}: '{span_text}'")
        else:
             logging.error(f"Span data column index ({span_col_index}) is out of bounds unexpectedly for {player_name}. Skipping.")
             return None

        # --- Both Header and Data Checks Passed - Extract Bowling Data ---
        bowling_data['Player Name'] = player_name
        bowling_data['Player ID'] = player_id
        bowling_data['Format'] = safe_get_text(cols[format_col_index - 1]) # Index 0

        for key_name, index in column_mapping.items():
            cell_index_0_based = index - 1
            if cell_index_0_based < len(cols): # Check index validity
                cell_value = safe_get_text(cols[cell_index_0_based])

                # --- Step 3: Special Handling for BBI ---
                if key_name == 'BBI':
                    bbi_wkts, bbi_runs = parse_bbi(cell_value)
                    bowling_data['BBI Wkts'] = bbi_wkts
                    bowling_data['BBI Runs'] = bbi_runs
                    # Optionally store the original string if needed
                    # bowling_data['BBI Raw'] = cell_value
                else:
                    # Store other values directly
                    bowling_data[key_name] = cell_value
            else:
                logging.error(f"Column index {index} ('{key_name}') out of bounds ({len(cols)} cols found) for {player_name}. Setting N/A.")
                # Ensure keys exist even if data is missing
                bowling_data[key_name] = pd.NA
                if key_name == 'BBI': # Need to add NA for split columns too
                     bowling_data['BBI Wkts'] = pd.NA
                     bowling_data['BBI Runs'] = pd.NA


        logging.info(f"Successfully extracted career bowling stats for {player_name}.")
        return bowling_data

    except TimeoutException:
        logging.error(f"Timed out waiting for page elements for {player_name}. Skipping.")
        return None
    except NoSuchElementException as e:
        logging.error(f"Scraping error for {player_name} (NoSuchElement): {e}")
        return None
    except WebDriverException as e_wd:
        logging.error(f"WebDriver error for {player_name} (career bowling): {e_wd}", exc_info=False)
        return None
    except Exception as e_player:
        logging.error(f"Unexpected error processing career bowling stats for {player_name}: {e_player}", exc_info=True)
        return None


# --- Main Execution Logic ---
if __name__ == "__main__":
    overall_start_time = time.time()
    driver = None
    all_bowling_data = [] # Renamed list
    skipped_players_count = 0

    try:
        driver = setup_driver()
        total_players = len(PLAYER_DATA)
        player_count = 0

        for player in PLAYER_DATA:
            player_id = player['id']
            player_name = player['name']
            player_count += 1
            logging.info(f"\n>>> Processing Player {player_count}/{total_players}: {player_name} (ID: {player_id}) <<<\n")

            # Call the UPDATED bowling stats function
            player_stats = scrape_player_career_bowling_stats(driver, player_id, player_name)

            if player_stats:
                all_bowling_data.append(player_stats) # Append to bowling list
                logging.info(f"Added career bowling record for {player_name}.")
            else:
                skipped_players_count += 1

            time.sleep(random.uniform(1.5, 3.5))

    except Exception as e:
        logging.critical(f"A critical error occurred during driver setup or the main player loop: {e}", exc_info=True)
    finally:
        if driver:
            try: logging.info("Quitting WebDriver..."); driver.quit(); logging.info("Browser closed.")
            except Exception as quit_err: logging.error(f"Error occurred while closing the browser: {quit_err}")

    # --- Process and Save Final DataFrame to CSV ---
    # UPDATED Log message
    logging.info("\n" + "="*20 + f" Processing and Saving Combined Career Bowling Stats Data " + "="*20)

    if all_bowling_data:
        try:
            summary_df = pd.DataFrame(all_bowling_data) # Create DF from bowling data
            processed_players_count = pd.unique(summary_df['Player ID']).size
            logging.info(f"Created combined DataFrame with {len(summary_df)} career bowling rows for {processed_players_count} players.")
            logging.info(f"Skipped {skipped_players_count} players (due to header/data validation failures).")

            # Define and Apply Final Column Order for BOWLING stats
            # Note: Excludes original 'BBI', includes split columns
            final_cols_ordered = [
                'Player Name', 'Player ID', 'Format', 'Span', 'Matches', 'Innings', 'Overs',
                'Mdns', 'Runs', 'Wkts', 'BBI Wkts', 'BBI Runs', 'Ave', 'Econ', 'SR', '4w', '5w'
            ]

            # Ensure all expected columns exist, add if missing
            for col in final_cols_ordered:
                if col not in summary_df.columns:
                    summary_df[col] = pd.NA # Use NA for consistency
                    logging.warning(f"Expected column '{col}' was missing, added with default value NA.")

            # Reorder columns
            final_cols_present = [col for col in final_cols_ordered if col in summary_df.columns]
            # Include columns extracted but not in the expected list (e.g. 'BBI' if not removed)
            extra_cols = [col for col in summary_df.columns if col not in final_cols_present]
            if extra_cols: logging.warning(f"Extra columns found not in expected list: {extra_cols}. These will be included at the end.")

            summary_df = summary_df[final_cols_present + extra_cols]
            logging.info(f"Final columns ordered: {final_cols_present + extra_cols}")

            # --- Data Cleaning/Type Conversion for BOWLING stats ---
            # UPDATED list of numeric columns
            numeric_cols = [
                'Matches', 'Innings', 'Overs', 'Mdns', 'Runs', 'Wkts',
                'BBI Wkts', 'BBI Runs', # Include parsed BBI parts
                'Ave', 'Econ', 'SR', '4w', '5w'
                ]
            for col in numeric_cols:
                if col in summary_df.columns:
                    # Replace placeholder '-' before attempting conversion
                    summary_df[col] = summary_df[col].replace(['-'], pd.NA, regex=False)
                    # Attempt conversion, coerce errors to NA (this handles pd.NA from parsing too)
                    summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')
            logging.info("Attempted numeric conversion for relevant bowling columns (errors coerced to NA).")

            # --- Save to CSV ---
            logging.info(f"Saving combined career bowling stats to CSV file: {OUTPUT_CSV_PATH}")
            summary_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
            logging.info(f"Successfully saved data to {OUTPUT_CSV_PATH}")
            # UPDATED Print message
            print(f"\n*** Combined career bowling stats successfully saved to: {OUTPUT_CSV_PATH} ***")
            print(f"      Processed {processed_players_count} players. Skipped {skipped_players_count} players.")
            print(f"      You can now use this CSV file.")

            # --- Console Print of DataFrame Head ---
            print("\n" + "="*60)
            print(f"Combined Career Bowling Stats Data ({len(summary_df)} rows) - First 10 Rows:") # UPDATED Title
            print("="*60)
            pd.set_option('display.max_rows', 20); pd.set_option('display.max_columns', None); pd.set_option('display.width', 2000)
            print(summary_df.head(10).to_string(index=False))
            print("="*60)

        except Exception as e_proc:
            # UPDATED Error message context
            logging.error(f"Error creating DataFrame or saving career bowling stats to CSV: {e_proc}", exc_info=True)
            print(f"\n--- Error processing or saving final data. Check logs: {log_filename} ---")

    else:
        # UPDATED Warning message context
        logging.warning(f"No career bowling data collected for any player (or all were skipped). Cannot generate CSV.")
        logging.info(f"Total players attempted: {len(PLAYER_DATA)}. Total players skipped: {skipped_players_count}.")
        print(f"\n--- No career bowling data retrieved or all {skipped_players_count} players were skipped. No CSV file generated. ---")

    # --- Final Summary (UPDATED logging context) ---
    overall_end_time = time.time(); total_duration = overall_end_time - overall_start_time
    total_minutes = total_duration / 60
    logging.info(f"\nScript finished in {total_duration:.2f} seconds ({total_minutes:.2f} minutes).")
    try:
        processed_count = 0
        if 'summary_df' in locals() and isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
             processed_count = pd.unique(summary_df['Player ID']).size
             logging.info(f"Final combined DataFrame shape: {summary_df.shape}")
        elif 'all_bowling_data' in locals() and not all_bowling_data: # Check bowling list
             logging.info("No data was collected in the 'all_bowling_data' list (all players skipped or errors occurred).")
        else:
             logging.info("Final combined DataFrame was empty or not created due to earlier errors or no data.")

        logging.info(f"Successfully processed career bowling stats for {processed_count} players.") # Updated context
        logging.info(f"Skipped {skipped_players_count} players.")

    except NameError:
        logging.info("Final combined DataFrame variable ('summary_df') was not created, likely due to earlier errors.")
        logging.info(f"Attempted processing for {len(PLAYER_DATA)} players. Skipped {skipped_players_count} players.")

    logging.info("="*50 + " Script End " + "="*50)