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

# --- Player Data (Updated List - Set 1) ---
PLAYER_DATA = [
    {'id': '1060380', 'name': 'RD Gaikwad'}, {'id': '1125688', 'name': 'Mukesh Choudhary'}, {'id': '1182529', 'name': 'Noor Ahmad'}, {'id': '1194795', 'name': 'M Pathirana'}, {'id': '234675', 'name': 'RA Jadeja'}, {'id': '26421', 'name': 'R Ashwin'}, {'id': '28081', 'name': 'MS Dhoni'}, {'id': '379140', 'name': 'DP Conway'}, {'id': '446763', 'name': 'RA Tripathi'}, {'id': '477021', 'name': 'V Shankar'}, {'id': '497121', 'name': 'DJ Hooda'}, {'id': '510530', 'name': 'J Overton'}, {'id': '662973', 'name': 'SM Curran'}, {'id': '714451', 'name': 'S Dube'}, {'id': '826915', 'name': 'NT Ellis'}, {'id': '942645', 'name': 'KK Ahmed'}, {'id': '959767', 'name': 'R Ravindra'}, {'id': '1131978', 'name': 'AR Sharma'}, {'id': '1168049', 'name': 'J Fraser-McGurk'}, {'id': '1175489', 'name': 'Sameer Rizvi'}, {'id': '1277545', 'name': 'Abishek Porel'}, {'id': '1449074', 'name': 'V Nigam'}, {'id': '311592', 'name': 'MA Starc'}, {'id': '422108', 'name': 'KL Rahul'}, {'id': '44828', 'name': 'F du Plessis'}, {'id': '537119', 'name': 'MM Sharma'}, {'id': '554691', 'name': 'AR Patel'}, {'id': '559235', 'name': 'Kuldeep Yadav'}, {'id': '595978', 'name': 'T Stubbs'}, {'id': '926851', 'name': 'Mukesh Kumar'}, {'id': '1048739', 'name': 'R Sai Kishore'}, {'id': '1070173', 'name': 'Shubman Gill'}, {'id': '1151288', 'name': 'B Sai Sudharsan'}, {'id': '1244751', 'name': 'Arshad Khan'}, {'id': '236779', 'name': 'I Sharma'}, {'id': '308967', 'name': 'JC Buttler'}, {'id': '423838', 'name': 'R Tewatia'}, {'id': '550215', 'name': 'K Rabada'}, {'id': '719715', 'name': 'Washington Sundar'}, {'id': '719719', 'name': 'M Shahrukh Khan'}, {'id': '793463', 'name': 'Rashid Khan'}, {'id': '914541', 'name': 'SE Rutherford'}, {'id': '917159', 'name': 'M Prasidh Krishna'}, {'id': '940973', 'name': 'Mohammed Siraj'}, {'id': '1070196', 'name': 'Yash Thakur'}, {'id': '1125976', 'name': 'Arshdeep Singh'}, {'id': '1151273', 'name': 'N Wadhera'}, {'id': '1161024', 'name': 'Prabhsimran Singh'}, {'id': '1175456', 'name': 'P Arya'}, {'id': '1339698', 'name': 'Suryansh Shedge'}, {'id': '325012', 'name': 'MP Stoinis'}, {'id': '325026', 'name': 'GJ Maxwell'}, {'id': '377534', 'name': 'Shashank Singh'}, {'id': '430246', 'name': 'YS Chahal'}, {'id': '493773', 'name': 'LH Ferguson'}, {'id': '642519', 'name': 'SS Iyer'}, {'id': '696401', 'name': 'M Jansen'}, {'id': '777815', 'name': 'V Vyshak'}, {'id': '819429', 'name': 'Azmatullah Omarzai'}, {'id': '1079470', 'name': 'Ramandeep Singh'}, {'id': '1108375', 'name': 'CV Varun'}, {'id': '1123718', 'name': 'SH Johnson'}, {'id': '1209292', 'name': 'VG Arora'}, {'id': '1292495', 'name': 'A Raghuvanshi'}, {'id': '1312645', 'name': 'Harshit Rana'}, {'id': '230558', 'name': 'SP Narine'}, {'id': '276298', 'name': 'AD Russell'}, {'id': '277916', 'name': 'AM Rahane'}, {'id': '290630', 'name': 'MK Pandey'}, {'id': '379143', 'name': 'Q de Kock'}, {'id': '723105', 'name': 'RK Singh'}, {'id': '851403', 'name': 'VR Iyer'}, {'id': '8917', 'name': 'MM Ali'}, {'id': '1151270', 'name': 'A Badoni'}, {'id': '1151286', 'name': 'M Siddharth'}, {'id': '1159711', 'name': 'Shahbaz Ahmed'}, {'id': '1175441', 'name': 'Ravi Bishnoi'}, {'id': '1175485', 'name': 'Abdul Samad'}, {'id': '1176959', 'name': 'Akash Deep'}, {'id': '1350768', 'name': 'Prince Yadav'}, {'id': '1460529', 'name': 'DS Rathi'}, {'id': '272450', 'name': 'MR Marsh'}, {'id': '321777', 'name': 'DA Miller'}, {'id': '475281', 'name': 'SN Thakur'}, {'id': '600498', 'name': 'AK Markram'}, {'id': '604302', 'name': 'N Pooran'}, {'id': '694211', 'name': 'Avesh Khan'}, {'id': '931581', 'name': 'RR Pant'}, {'id': '1170265', 'name': 'NT Tilak Varma'}, {'id': '1209126', 'name': 'Ashwani Kumar'}, {'id': '1287032', 'name': 'Naman Dhir'}, {'id': '1292502', 'name': 'RA Bawa'}, {'id': '1350762', 'name': 'R Minz'}, {'id': '1392201', 'name': 'PVSN Raju'}, {'id': '1460388', 'name': 'V Puthur'}, {'id': '277912', 'name': 'TA Boult'}, {'id': '34102', 'name': 'RG Sharma'}, {'id': '446507', 'name': 'SA Yadav'}, {'id': '447261', 'name': 'DL Chahar'}, {'id': '502714', 'name': 'MJ Santner'}, {'id': '605661', 'name': 'RD Rickelton'}, {'id': '625371', 'name': 'HH Pandya'}, {'id': '625383', 'name': 'JJ Bumrah'}, {'id': '897549', 'name': 'WG Jacks'}, {'id': '974109', 'name': 'Mujeeb Ur Rahman'}, {'id': '1079434', 'name': 'R Parag'}, {'id': '1138316', 'name': 'M Theekshana'}, {'id': '1151278', 'name': 'YBK Jaiswal'}, {'id': '1159843', 'name': 'K Kartikeya'}, {'id': '1175488', 'name': 'DC Jurel'}, {'id': '1206052', 'name': 'Yudhvir Singh'}, {'id': '1252585', 'name': 'SB Dubey'}, {'id': '425943', 'name': 'SV Samson'}, {'id': '438362', 'name': 'Sandeep Sharma'}, {'id': '604527', 'name': 'N Rana'}, {'id': '669855', 'name': 'JC Archer'}, {'id': '670025', 'name': 'SO Hetmyer'}, {'id': '784379', 'name': 'PW Hasaranga'}, {'id': '822553', 'name': 'TU Deshpande'}, {'id': '974175', 'name': 'Fazalhaq Farooqi'}, {'id': '1119026', 'name': 'D Padikkal'}, {'id': '1159720', 'name': 'Yash Dayal'}, {'id': '1161489', 'name': 'Rasikh Salam'}, {'id': '1350792', 'name': 'Suyash Sharma'}, {'id': '253802', 'name': 'V Kohli'}, {'id': '288284', 'name': 'JR Hazlewood'}, {'id': '326016', 'name': 'B Kumar'}, {'id': '403902', 'name': 'LS Livingstone'}, {'id': '471342', 'name': 'KH Pandya'}, {'id': '669365', 'name': 'PD Salt'}, {'id': '721867', 'name': 'JM Sharma'}, {'id': '823703', 'name': 'RM Patidar'}, {'id': '892749', 'name': 'TH David'}, {'id': '1070183', 'name': 'Abhishek Sharma'}, {'id': '1159722', 'name': 'Simarjeet Singh'}, {'id': '1175496', 'name': 'K Nitish Kumar Reddy'}, {'id': '1409976', 'name': 'AU Verma'}, {'id': '379504', 'name': 'A Zampa'}, {'id': '390481', 'name': 'HV Patel'}, {'id': '390484', 'name': 'JD Unadkat'}, {'id': '436757', 'name': 'H Klaasen'}, {'id': '481896', 'name': 'Mohammed Shami'}, {'id': '489889', 'name': 'PJ Cummins'}, {'id': '530011', 'name': 'TM Head'}, {'id': '698189', 'name': 'PWA Mulder'}, {'id': '720471', 'name': 'Ishan Kishan'}, {'id': '778963', 'name': 'A Manohar'}, {'id': '784373', 'name': 'PHKD Mendis'}, {'id': '942371', 'name': 'Zeeshan Ansari'}
]

# --- Configuration ---
BASE_URL = 'https://stats.espncricinfo.com/ci/engine/player/{player_id}.html?class=6;template=results;type=batting;view=innings'
OUTPUT_DIR = "Innings_By_Innings_output" # Updated output directory name
os.makedirs(OUTPUT_DIR, exist_ok=True)
FALLBACK_TABLE_SELECTOR = '#ciHomeContentlhs > div.pnl650M > table:nth-child(5)'
# Define CSV Output file path (Updated Filename)
OUTPUT_CSV_FILENAME = "innings_by_innings_batting.csv" # CHANGED FILENAME
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, OUTPUT_CSV_FILENAME)

# --- Logging Setup ---
log_filename = os.path.join(OUTPUT_DIR, f"player_innings_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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

# Get current time using system timezone
# Use datetime object from datetime module
current_time_system = datetime.now()
current_date_system = current_time_system.date()
current_time_str = current_time_system.strftime('%Y-%m-%d %H:%M:%S %Z') # %Z might be empty depending on OS/locale

logging.info(f"Log file: {log_filename}")
logging.info(f"Script started at: {current_time_str} (System Time - IST)") # Explicitly mention IST
logging.info(f"Current Date according to system: {current_date_system}") # Log current date
logging.info(f"Processing {len(PLAYER_DATA)} players.")
logging.info("Targeting player innings batting stats using index-based extraction.")
logging.info(f"Output CSV will be saved to: {OUTPUT_CSV_PATH}") # Log CSV path (reflects new filename)
logging.warning("This index-based extraction method is FRAGILE and may break if table structure changes.")


# --- Helper Functions ---
def safe_get_text(element, default='N/A'):
    """Safely extracts text from a BeautifulSoup Tag or returns default."""
    if isinstance(element, Tag): text = element.get_text(strip=True); return text if text else default
    elif isinstance(element, str): return element.strip()
    return default if element is None else str(element)

# --- Driver Setup ---
def setup_driver():
    """Sets up the undetected_chromedriver with options and retries."""
    driver = None; retries = 3; last_exception = None
    for attempt in range(retries):
        logging.info(f"Attempting to initialize WebDriver (Attempt {attempt + 1}/{retries})...")
        try:
            options = uc.ChromeOptions()
            # options.add_argument('--headless=new')
            options.add_argument("--start-maximized"); options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage")
            options.add_argument('--log-level=3'); options.add_argument("--disable-gpu"); options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars"); options.add_argument("--window-size=1920,1080")
            # Ensure you have a valid User Agent if needed
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36") # Example UA
            driver = uc.Chrome(options=options, enable_cdp_events=True, version_main=None) # version_main=None lets uc detect it
            logging.info("Browser driver setup successful.")
            return driver
        except Exception as e:
            last_exception = e; logging.warning(f"Failed WebDriver init attempt {attempt + 1}: {e}")
            if attempt < retries - 1: logging.info("Retrying after 5 seconds..."); time.sleep(5)
            else: logging.error("Max retries reached for WebDriver init."); raise last_exception
    if driver is None and last_exception: raise last_exception
    return driver

# --- Function to Scrape Innings Data for ONE Player (Index-Based) ---
def scrape_player_innings_by_index(driver: WebDriver, player_id: str, player_name: str) -> list:
    """
    Scrapes batting innings data for a specific player using column indices.
    Returns a list of dictionaries, each representing an innings.
    """
    target_url = BASE_URL.format(player_id=player_id)
    logging.info(f"Attempting to scrape innings data for {player_name} from: {target_url}")
    player_innings_list = []
    expected_caption_text = "Innings by innings list"

    # Column mapping based on observed structure - ADJUST IF THE SITE CHANGES
    column_mapping = {
        'Runs': {'index': 1, 'clean': '*'}, 'Mins': {'index': 2}, 'BF': {'index': 3},
        '4s': {'index': 4}, '6s': {'index': 5}, 'SR': {'index': 6}, 'Pos': {'index': 7},
        'Dismissal': {'index': 8}, 'Inns': {'index': 9},
        'Opposition': {'index': 11, 'inner_tag': 'a'}, 'Ground': {'index': 12, 'inner_tag': 'a'},
        'Start Date': {'index': 13, 'inner_tag': 'b'}
    }
    max_index = max(details['index'] for details in column_mapping.values())

    try:
        driver.get(target_url)
        wait_time = 30
        data_table = None

        # Find Table logic (Caption preferred, CSS fallback)
        try:
            # Wait for a container element that should hold the table
            WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ciHomeContentlhs > div.pnl650M")))
            time.sleep(random.uniform(1.5, 2.5)) # Short pause for potential dynamic loading
            page_soup = BeautifulSoup(driver.page_source, 'lxml')

            # Try finding by expected caption text
            caption_element = page_soup.find("b", string=lambda text: text and expected_caption_text in text.strip())
            if caption_element:
                # Find the next sibling table after the caption's parent (usually a div or similar)
                parent_element = caption_element.parent
                if parent_element:
                    data_table = parent_element.find_next_sibling("table", class_="engineTable")
                    if data_table: logging.info(f"Found innings table via caption for {player_name}.")
                    else: logging.warning(f"Found caption but no valid sibling table for {player_name}. Trying fallback.")
                else:
                    logging.warning(f"Found caption but couldn't find its parent to locate sibling table for {player_name}. Trying fallback.")
            else:
                 logging.warning(f"Could not find caption containing '{expected_caption_text}' for {player_name}. Trying fallback.")

            # Fallback using CSS selector if caption method failed
            if not data_table:
                logging.warning("Trying CSS selector fallback...")
                # Re-parse just in case, although usually not needed if the wait above succeeded
                page_soup = BeautifulSoup(driver.page_source, 'lxml')
                # Use the defined fallback selector
                data_table = page_soup.select_one(FALLBACK_TABLE_SELECTOR)
                if data_table: logging.info(f"Found innings table via CSS selector fallback for {player_name}.")
                else: logging.error(f"Could not find table using EITHER method for {player_name}. Skipping."); return []

        except TimeoutException: logging.error(f"Timed out waiting for table elements for {player_name}. Skipping."); return []
        except Exception as find_err: logging.error(f"Error finding table for {player_name}: {find_err}", exc_info=True); return []

        # Extract Data Rows based on Index Mapping
        table_body = data_table.find('tbody')
        if not table_body: logging.warning(f"Could not find table body (tbody) for {player_name}."); return []

        data_rows = table_body.find_all('tr', recursive=False) # Find only direct children 'tr'
        processed_count = 0; skipped_rows = 0
        for i, row in enumerate(data_rows):
            # Skip header rows if they exist within tbody (sometimes they do)
            if row.find('th'):
                skipped_rows += 1
                logging.debug(f"Skipping potential header row {i+1} in tbody for {player_name}.")
                continue

            cols = row.find_all('td', recursive=False) # Find only direct children 'td'

            # Check if the row has enough columns based on the maximum index needed
            # Allow rows with fewer columns if they represent non-batting entries (like 'did not bat')
            # A simple check: if the first cell contains text like 'DNB', 'absent', 'sub', it's likely not a standard innings row.
            first_cell_text = safe_get_text(cols[0]).lower() if cols else ""
            is_non_standard_row = any(marker in first_cell_text for marker in ['dnb', 'absent', 'sub', 'retired hurt', 'tdnb'])

            if len(cols) <= max_index and not is_non_standard_row:
                 # Check if it's a known dismissal/summary row class (might need adjustment)
                 row_classes = row.get("class", [])
                 is_dismissal_summary = any(cls in row_classes for cls in ["dismissal", "inningsSummary", "note"]) # Add relevant classes

                 if not is_dismissal_summary:
                     logging.warning(f"Skipping row {i+1} for {player_name} (only {len(cols)} cells, needed >{max_index}, not standard non-batting row). Content: {[safe_get_text(c) for c in cols]}")
                     skipped_rows += 1
                 else:
                     logging.debug(f"Ignoring known summary/dismissal row {i+1} for {player_name}.")
                     skipped_rows += 1
                 continue

            row_data = {}
            extraction_successful = True
            for key_name, details in column_mapping.items():
                index = details['index']; cell_index_0_based = index - 1
                if cell_index_0_based < len(cols):
                    cell = cols[cell_index_0_based]; value = 'N/A'; target_element = cell
                    # If an inner tag is specified (like 'a' or 'b'), try to find it
                    if 'inner_tag' in details:
                        inner_element = cell.find(details['inner_tag'])
                        if inner_element: target_element = inner_element
                    value = safe_get_text(target_element)
                    # Clean '*' from Runs if specified
                    if 'clean' in details and details['clean'] == '*': value = value.replace('*', '')
                    row_data[key_name] = value
                else:
                    # Only log error if it's not a known non-standard row where fewer columns are expected
                    if not is_non_standard_row:
                         logging.error(f"Cell index {index} out of bounds (found {len(cols)}) for row {i+1} for {player_name}. Assigning N/A to '{key_name}'.")
                         row_data[key_name] = 'N/A'; extraction_successful = False # Mark as unsuccessful if critical data missing
                    else:
                         # For non-standard rows, it's okay to have missing data in later columns
                         row_data[key_name] = 'N/A'

            # Add player identifiers
            row_data['Player Name'] = player_name; row_data['Player ID'] = player_id

            # Add the row data only if extraction was generally successful OR it was a recognized non-standard row (like DNB)
            # We might want to filter out DNB rows later if not needed, but capture them initially.
            # Let's add a check: only append if the 'Runs' column was found or it's a known non-standard row.
            if extraction_successful or (is_non_standard_row and row_data.get('Runs') != 'N/A'):
                 player_innings_list.append(row_data); processed_count += 1
            elif not is_non_standard_row: # Log skipped rows that aren't DNB/etc. and had errors
                skipped_rows +=1
                logging.warning(f"Row {i+1} for {player_name} skipped due to data extraction issues (Index out of bounds).")
            else: # Log skipped non-standard rows if they somehow didn't get added
                 skipped_rows +=1
                 logging.debug(f"Row {i+1} for {player_name} skipped (non-standard type without runs extracted).")


        logging.info(f"Processed {processed_count} innings, skipped {skipped_rows} rows for {player_name}.")

    except NoSuchElementException as e: logging.error(f"Scraping error for {player_name} (NoSuchElement): {e}")
    except WebDriverException as e_wd: logging.error(f"WebDriver error for {player_name}: {e_wd}", exc_info=False) # Set exc_info=False for cleaner logs unless debugging WebDriver issues
    except Exception as e_player: logging.error(f"Unexpected error processing {player_name}: {e_player}", exc_info=True) # Keep exc_info=True for unexpected errors
    return player_innings_list

# --- Main Execution Logic ---
if __name__ == "__main__":
    overall_start_time = time.time()
    driver = None
    all_innings_data = [] # List to hold innings dicts from ALL players

    try:
        driver = setup_driver()
        total_players = len(PLAYER_DATA)
        player_count = 0

        for player in PLAYER_DATA:
            player_id = player['id']
            player_name = player['name']
            player_count += 1
            logging.info(f"\n>>> Processing Player {player_count}/{total_players}: {player_name} (ID: {player_id}) <<<\n")

            player_data = scrape_player_innings_by_index(driver, player_id, player_name)

            if player_data:
                all_innings_data.extend(player_data)
                logging.info(f"Added {len(player_data)} innings records for {player_name}.")
            else:
                logging.warning(f"No data retrieved or processed for {player_name}.")
            # Random delay between player requests
            time.sleep(random.uniform(2.0, 4.5)) # Increased delay slightly

    except Exception as e:
        logging.critical(f"A critical error occurred during driver setup or the main player loop: {e}", exc_info=True)
    finally:
        if driver:
            try: logging.info("Quitting WebDriver..."); driver.quit(); logging.info("Browser closed.")
            except Exception as quit_err: logging.error(f"Error occurred while closing the browser: {quit_err}")

    # --- Process and Save Final DataFrame to CSV ---
    logging.info("\n" + "="*20 + f" Processing and Saving Combined Innings Data " + "="*20)

    if all_innings_data:
        try:
            summary_df = pd.DataFrame(all_innings_data)
            logging.info(f"Created combined DataFrame with {len(summary_df)} total innings rows from {pd.unique(summary_df['Player ID']).size} players.")

            # Define and Apply Final Column Order
            final_cols_ordered = [
                'Player Name', 'Player ID', 'Runs', 'Mins', 'BF', '4s', '6s', 'SR',
                'Pos', 'Dismissal', 'Inns', 'Opposition', 'Ground', 'Start Date'
                ]
            # Ensure all expected columns exist, add if missing (with N/A or default)
            for col in final_cols_ordered:
                if col not in summary_df.columns:
                    summary_df[col] = 'N/A' # Or pd.NA or appropriate default
                    logging.warning(f"Expected column '{col}' was missing, added with default value 'N/A'.")

            # Select and reorder columns
            final_cols_present = [col for col in final_cols_ordered if col in summary_df.columns] # Should now include all from final_cols_ordered
            extra_cols = [col for col in summary_df.columns if col not in final_cols_present]
            if extra_cols: logging.warning(f"Extra columns found not in expected list: {extra_cols}. These will be included at the end.")
            final_df_cols = final_cols_present + extra_cols

            summary_df = summary_df[final_df_cols]
            logging.info(f"Final columns ordered: {final_df_cols}")

            # --- Data Cleaning/Type Conversion (Optional but Recommended) ---
            # Example: Convert numeric columns, handle 'N/A' or '-'
            numeric_cols = ['Runs', 'Mins', 'BF', '4s', '6s', 'SR', 'Pos', 'Inns']
            for col in numeric_cols:
                if col in summary_df.columns:
                     # Replace non-numeric placeholders like '-' or 'N/A' with NaN
                     summary_df[col] = summary_df[col].replace(['-', 'N/A', ''], pd.NA)
                     # Attempt conversion, coerce errors to NaN
                     summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')
            logging.info("Attempted numeric conversion for relevant columns.")
            # Convert 'Start Date' to datetime objects if needed (handle potential errors)
            try:
                 summary_df['Start Date'] = pd.to_datetime(summary_df['Start Date'], errors='coerce')
                 logging.info("Converted 'Start Date' column to datetime objects.")
            except Exception as date_err:
                 logging.warning(f"Could not convert 'Start Date' to datetime: {date_err}")


            # --- Save to CSV ---
            logging.info(f"Saving combined innings data to CSV file: {OUTPUT_CSV_PATH}")
            summary_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig') # Saves the file
            logging.info(f"Successfully saved data to {OUTPUT_CSV_PATH}")
            print(f"\n*** Combined innings data successfully saved to: {OUTPUT_CSV_PATH} ***")
            print(f"      You can now use this CSV file.")

            # --- Console Print of DataFrame (Optional - Keep commented out for large data) ---
            # print("\n" + "="*50)
            # print(f"Combined Batting Innings Data ({len(summary_df)} rows)")
            # print("="*50)
            # pd.set_option('display.max_rows', 50) # Show fewer rows in console
            # pd.set_option('display.max_columns', None)
            # pd.set_option('display.width', 2000)
            # print(summary_df.head(20).to_string(index=False)) # Print first 20 rows

        except Exception as e_proc:
            logging.error(f"Error creating DataFrame or saving to CSV: {e_proc}", exc_info=True)
            print(f"\n--- Error processing or saving final data. Check logs: {log_filename} ---")

    else:
        logging.warning("No innings data collected for any player. Cannot generate CSV.")
        print("\n--- No innings data retrieved. No CSV file generated. ---")

    # --- Final Summary ---
    overall_end_time = time.time(); total_duration = overall_end_time - overall_start_time
    total_minutes = total_duration / 60
    logging.info(f"\nScript finished in {total_duration:.2f} seconds ({total_minutes:.2f} minutes).")
    try:
        # Check if summary_df was created and is not empty
        if 'summary_df' in locals() and isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            logging.info(f"Final combined DataFrame shape: {summary_df.shape}")
            processed_players = pd.unique(summary_df['Player ID']).size
            logging.info(f"Successfully processed innings data for {processed_players} players.")
        elif 'all_innings_data' in locals() and not all_innings_data:
             logging.info("No data was collected in the 'all_innings_data' list.")
        else:
            logging.info("Final combined DataFrame was empty or not created due to earlier errors or no data.")
    except NameError: # summary_df might not exist if there were critical errors early on
        logging.info("Final combined DataFrame variable ('summary_df') was not created, likely due to earlier errors.")
    logging.info(f"Attempted processing for {len(PLAYER_DATA)} players.")
    logging.info("="*50 + " Script End " + "="*50)