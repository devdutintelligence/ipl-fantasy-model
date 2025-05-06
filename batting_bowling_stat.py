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
import numpy as np # For NaN handling if needed during Mat merge
from urllib.parse import urljoin
import traceback
from datetime import datetime
import re
import logging
import os

# --- Team Information ---
IPL_TEAMS = {
    '4343': 'Chennai Super Kings',
    '4347': 'Deccan Chargers', # Defunct
    '4344': 'Delhi Daredevils', # Defunct name, now Delhi Capitals
    '5845': 'Gujarat Lions', # Defunct
    '6904': 'Gujarat Titans',
    '4342': 'Kings XI Punjab', # Defunct name, now Punjab Kings
    '4788': 'Kochi Tuskers Kerala', # Defunct
    '4341': 'Kolkata Knight Riders',
    '6903': 'Lucknow Super Giants',
    '4346': 'Mumbai Indians',
    '4787': 'Pune Warriors', # Defunct
    '4345': 'Rajasthan Royals',
    '5843': 'Rising Pune Supergiants', # Defunct
    '4340': 'Royal Challengers Bangalore', # Defunct name, now Royal Challengers Bengaluru
    '5143': 'Sunrisers Hyderabad'
}

# --- Segment Information (Internal Use Only) ---
SEGMENT_INFO = {
    'Batting': {'name': 'Batting', 'path': 'averages-batting'},
    'Bowling': {'name': 'Bowling', 'path': 'averages-bowling'}
}

# Base URL structure parts
BASE_URL_START = 'https://www.espncricinfo.com/records/trophy/'
BASE_URL_END = '/indian-premier-league-117?team={}' # Placeholder for team ID

# --- Configuration ---
OUTPUT_DIR = "batting_bowling_stat_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV_FILENAME = "batting_bowling_stat.csv"
OUTPUT_CSV_PATH = os.path.join(OUTPUT_DIR, OUTPUT_CSV_FILENAME)

# --- Logging Setup ---
log_filename = os.path.join(OUTPUT_DIR, f"ipl_all_teams_merged_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
current_date_system = current_time_system.date()
current_time_str = current_time_system.strftime('%Y-%m-%d %H:%M:%S %Z')

logging.info(f"Log file: {log_filename}")
logging.info(f"Script started at: {current_time_str} (System Time)")
logging.info(f"Current Date according to system: {current_date_system}")
logging.info(f"Processing ALL {len(IPL_TEAMS)} teams defined in IPL_TEAMS dictionary.")
logging.info(f"Output CSV will be saved to: {OUTPUT_CSV_PATH}")
logging.warning("Note: Fielding columns 'Ct' and 'St' are not included as they are not available on the scraped batting/bowling average pages.")
logging.warning("Processing all teams will take a significant amount of time.")


# --- Helper Functions ---
def safe_get_text(element, default='N/A'):
    """Safely extracts text from a BeautifulSoup Tag or returns default."""
    if isinstance(element, Tag): text = element.get_text(strip=True); return text if text else default
    elif isinstance(element, str): return element.strip()
    return default

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
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36") # Example UA
            driver = uc.Chrome(options=options, enable_cdp_events=True, version_main=None)
            logging.info("Browser driver setup successful.")
            return driver
        except Exception as e:
            last_exception = e; logging.warning(f"Failed WebDriver init attempt {attempt + 1}: {e}")
            if attempt < retries - 1: logging.info("Retrying after 5 seconds..."); time.sleep(5)
            else: logging.error("Max retries reached for WebDriver init."); raise last_exception
    if driver is None and last_exception: raise last_exception
    return driver

# --- Parsing Functions ---
def extract_player_id(player_url):
    """Extracts the numeric ID from the end of a player URL using regex."""
    if isinstance(player_url, str) and player_url != 'N/A':
        match = re.search(r'(?:-|/)(\d+)$', player_url)
        if match: return match.group(1)
    logging.debug(f"Could not extract player ID from URL: {player_url}")
    return 'N/A'

def parse_career_span(span_str):
    """Parses a career span string (e.g., '2011-2013') into start and end years."""
    first_season, last_season = 'N/A', 'N/A'
    if isinstance(span_str, str) and span_str != 'N/A':
        span_str = span_str.strip()
        if '-' in span_str:
            parts = span_str.split('-')
            if len(parts) == 2:
                p1, p2 = parts[0].strip(), parts[1].strip()
                if (p1.isdigit() and len(p1) == 4 and p2.isdigit() and len(p2) == 4):
                    first_season, last_season = p1, p2
                else:
                    logging.warning(f"Span parts '{p1}', '{p2}' not valid years in '{span_str}'. Using original.")
                    first_season = last_season = span_str
            else:
                logging.warning(f"Unexpected format (multiple hyphens): {span_str}")
                first_season = last_season = span_str
        elif span_str.isdigit() and len(span_str) == 4:
            first_season = last_season = span_str
        else:
            logging.warning(f"Unexpected format: {span_str}")
            first_season = last_season = span_str
    return first_season, last_season

# --- Core Scraping Function (for one segment) ---
def scrape_segment_data(driver: WebDriver, team_id: str, segment_name: str, segment_path: str) -> list:
    """
    Scrapes data for a specific team and segment. Renames specific
    columns ('Runs', 'Ave', 'SR', 'Mat', 'Inns', '5', '10') based on segment
    and expected headers. Cleans 'HS' column. Splits 'BBI' column.
    Returns a list of dictionaries containing refined data.
    """
    target_url = f"{BASE_URL_START}{segment_path}{BASE_URL_END.format(team_id)}"
    logging.info(f"Attempting to scrape {segment_name} data for Team {team_id} from: {target_url}")
    refined_data = []
    raw_data = [] # Holds data before refinement

    try:
        driver.get(target_url)
        table_body_selector = "table.ds-table tbody"; wait_time = 60
        logging.info(f"Waiting up to {wait_time}s for {segment_name} table body ('{table_body_selector}')...")
        try:
            WebDriverWait(driver, wait_time).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, table_body_selector))
            )
            logging.info(f"{segment_name} table body found and visible for Team {team_id}.")
            time.sleep(3)
        except TimeoutException:
            logging.error(f"Timed out waiting for {segment_name} table body: {table_body_selector} at {target_url}")
            # Save page source on timeout
            # Removed for brevity, can be re-added if needed
            return []

        page_soup = BeautifulSoup(driver.page_source, 'lxml')
        data_table = page_soup.select_one("table.ds-table")
        if not data_table:
            logging.error(f"Could not find data table element ('table.ds-table') for {segment_name} at {target_url}.")
            return []

        headers = []
        header_row = data_table.select_one("thead tr")
        if header_row:
            header_cells = header_row.find_all(['th', 'td'], recursive=False)
            headers = [safe_get_text(cell).replace('Span','Span Text') for cell in header_cells]
            # logging.info(f"Extracted {segment_name} Headers for Team {team_id}: {headers}") # Reduce log noise
        else:
            logging.error(f"Could not find table header row (thead tr) for {segment_name} at {target_url}.")
            return []

        table_body = data_table.find('tbody')
        if not table_body:
            logging.error(f"Could not find table body (tbody) for {segment_name} at {target_url}.")
            return []
        else:
            data_rows = table_body.find_all('tr', recursive=False)
            processed_count = 0
            # Define wanted base headers (before rename) + Player Link / Span Text
            # Includes 'BBI' now for processing
            wanted_bat_headers = ['Player', 'Player Link', 'Span Text', 'Mat', 'Inns', 'NO', 'Runs', 'HS', 'Ave', 'SR', '100', '50', '0']
            wanted_bowl_headers = ['Player', 'Player Link', 'Span Text', 'Mat', 'Inns', 'Mdns', 'Runs', 'Wkts', 'BBI', 'Ave', 'Econ', 'SR', '5', '10']
            wanted_headers = wanted_bat_headers if segment_name == 'Batting' else wanted_bowl_headers

            for i, row in enumerate(data_rows):
                cols = row.find_all('td', recursive=False)
                if len(cols) == len(headers):
                    row_data = {}
                    valid_row = True
                    for j, header in enumerate(headers):
                        header_text = header
                        if header_text not in wanted_headers:
                            continue

                        value = safe_get_text(cols[j])
                        key_name = header_text # Keep track of original for special handling

                        # Handle Player link extraction and ID (essential)
                        if header_text == 'Player':
                            player_cell = cols[j]
                            value = safe_get_text(player_cell)
                            link_tag = player_cell.find('a', href=True)
                            player_link = urljoin(target_url, link_tag['href']) if link_tag and link_tag.get('href') else 'N/A'
                            row_data['Player Link'] = player_link
                            row_data['Player'] = value # Store player name
                            if value == 'N/A' or value == '':
                                 logging.warning(f"Row {i+1} (Team {team_id}, {segment_name}) skipped, missing player name.")
                                 valid_row = False
                                 break
                            continue # Move to next header after handling Player

                        # Handle BBI splitting (Bowling only)
                        elif header_text == 'BBI' and segment_name == 'Bowling':
                            bbi_wickets = 'N/A'
                            bbi_runs = 'N/A'
                            if value != 'N/A' and '/' in value:
                                parts = value.split('/')
                                if len(parts) == 2:
                                    bbi_wickets = parts[0].strip()
                                    bbi_runs = parts[1].strip()
                                else:
                                    logging.warning(f"Unexpected BBI format '{value}' for player in row {i+1}, Team {team_id}.")
                            elif value != 'N/A' and value != '-': # Handle cases where BBI might just be '-' if no wickets
                                logging.warning(f"Unexpected BBI value '{value}' (no '/') for player in row {i+1}, Team {team_id}.")

                            row_data['BBI Wickets'] = bbi_wickets
                            row_data['BBI Runs'] = bbi_runs
                            continue # Move to next header after handling BBI

                        # Perform renaming for other specific columns
                        elif header_text == 'Runs':
                            key_name = 'Runs Scored' if segment_name == 'Batting' else 'Runs Conceded'
                        elif header_text == 'Ave':
                            key_name = 'Batting Ave' if segment_name == 'Batting' else 'Bowling Ave'
                        elif header_text == 'SR':
                            key_name = 'Batting SR' if segment_name == 'Batting' else 'Bowling SR'
                        elif header_text == 'Mat':
                            key_name = 'Mat_bat' if segment_name == 'Batting' else 'Mat_bowl'
                        elif header_text == 'Inns':
                             key_name = 'Inns_bat' if segment_name == 'Batting' else 'Inns_bowl'
                        elif header_text == '5':
                             key_name = '5 Wkts'
                        elif header_text == '10':
                             key_name = '10 Wkts'
                        elif header_text == 'HS':
                             value = value.replace('*', '') # Clean HS value

                        # Store the value with the final key name (if not handled above)
                        row_data[key_name] = value

                    if valid_row:
                        raw_data.append(row_data)
                        processed_count += 1
                else:
                    logging.warning(f"Skipping row {i+1} in {segment_name} table for Team {team_id} (column count mismatch).")
            # logging.info(f"Extracted raw {segment_name} data for {processed_count} rows for Team {team_id}.")

        # --- Refine Data ---
        # logging.info(f"Refining {len(raw_data)} {segment_name} entries for Team {team_id}...")
        for entry in raw_data:
            refined_entry = entry.copy()
            player_link = refined_entry.pop('Player Link', 'N/A')
            player_id_val = extract_player_id(player_link)
            if player_id_val == 'N/A':
                logging.warning(f"Skipping refinement for entry (Team {team_id}, {segment_name}), missing Player ID: {entry.get('Player', 'Unknown Player')}")
                continue
            refined_entry['Player ID'] = player_id_val

            span_text = refined_entry.pop('Span Text', 'N/A')
            first_season, last_season = parse_career_span(span_text)
            refined_entry['First Season'] = first_season
            refined_entry['Last Season'] = last_season
            refined_entry['Team ID'] = team_id
            refined_data.append(refined_entry)

        # logging.info(f"Finished refining {len(refined_data)} {segment_name} entries for Team {team_id}.")
        return refined_data

    except NoSuchElementException as e:
        logging.error(f"Could not find required element for {segment_name} (Team {team_id}): {e}")
        return []
    except WebDriverException as e_wd:
        logging.error(f"WebDriver error during {segment_name} (Team {team_id}): {e_wd}", exc_info=False)
        return []
    except Exception as e_main:
        logging.error(f"Unexpected error during {segment_name} (Team {team_id}): {e_main}", exc_info=True)
        return []

# --- Function to Scrape and Merge Data for ONE Team ---
def scrape_and_merge_team_data(driver: WebDriver, team_id: str) -> pd.DataFrame | None:
    """
    Scrapes Batting and Bowling data for a single team, merges them,
    handles 'Mat' column combination, and returns a merged DataFrame.
    Returns None if scraping fails significantly for the team.
    """
    team_name = IPL_TEAMS.get(team_id, f"Unknown ({team_id})")
    logging.info(f"--- Starting data collection for Team: {team_name} (ID: {team_id}) ---")

    segment_info_bat = SEGMENT_INFO['Batting']
    batting_data_list = scrape_segment_data(driver, team_id, segment_info_bat['name'], segment_info_bat['path'])

    segment_info_bowl = SEGMENT_INFO['Bowling']
    bowling_data_list = scrape_segment_data(driver, team_id, segment_info_bowl['name'], segment_info_bowl['path'])

    if not batting_data_list and not bowling_data_list:
        logging.warning(f"No data collected for Team ID {team_id}. Skipping merge.")
        return None

    try:
        batting_df = pd.DataFrame(batting_data_list)
        bowling_df = pd.DataFrame(bowling_data_list)

        key_cols = ['Player ID', 'Player', 'Team ID', 'First Season', 'Last Season']
        valid_batting_df = not batting_df.empty and all(col in batting_df.columns for col in key_cols)
        valid_bowling_df = not bowling_df.empty and all(col in bowling_df.columns for col in key_cols)
        merged_df = pd.DataFrame()

        if valid_batting_df and valid_bowling_df:
            merged_df = pd.merge(batting_df, bowling_df, on=key_cols, how='outer')
        elif valid_batting_df:
             logging.warning(f"Only batting data found/valid for Team {team_id}.")
             merged_df = batting_df
        elif valid_bowling_df:
             logging.warning(f"Only bowling data found/valid for Team {team_id}.")
             merged_df = bowling_df
        else:
             logging.error(f"Neither batting nor bowling data valid for merge for Team {team_id}.")
             return None

        if not merged_df.empty:
            # Combine Mat column
            if 'Mat_bat' in merged_df.columns:
                merged_df['Mat_bat_num'] = pd.to_numeric(merged_df['Mat_bat'], errors='coerce')
            else: merged_df['Mat_bat_num'] = np.nan
            if 'Mat_bowl' in merged_df.columns:
                merged_df['Mat_bowl_num'] = pd.to_numeric(merged_df['Mat_bowl'], errors='coerce')
            else: merged_df['Mat_bowl_num'] = np.nan

            merged_df['Mat'] = merged_df[['Mat_bat_num', 'Mat_bowl_num']].max(axis=1)
            merged_df['Mat'] = merged_df['Mat'].astype('Int64')

            cols_to_drop = [col for col in ['Mat_bat', 'Mat_bowl', 'Mat_bat_num', 'Mat_bowl_num'] if col in merged_df.columns]
            merged_df = merged_df.drop(columns=cols_to_drop)
            return merged_df
        else:
            logging.warning(f"Resulting merged DataFrame is empty for Team {team_id}.")
            return None

    except Exception as e_merge:
        logging.error(f"Error merging data for Team {team_id}: {e_merge}", exc_info=True)
        return None

# --- Main Execution Logic ---
if __name__ == "__main__":
    overall_start_time = time.time()
    driver = None
    all_teams_dataframes = [] # List to hold final DataFrame for each team

    logging.info(f"--- Starting processing for all {len(IPL_TEAMS)} IPL teams ---")

    try:
        driver = setup_driver() # Setup driver once for all teams

        team_count = 0
        total_teams = len(IPL_TEAMS)
        for team_id, team_name in IPL_TEAMS.items():
            team_count += 1
            logging.info(f"\n>>> Processing Team {team_count}/{total_teams}: {team_name} (ID: {team_id}) <<<\n")

            team_merged_df = scrape_and_merge_team_data(driver, team_id)

            if team_merged_df is not None and not team_merged_df.empty:
                all_teams_dataframes.append(team_merged_df)
                logging.info(f"Successfully processed and stored data for {team_name}.")
            else:
                logging.warning(f"Failed to get complete merged data for {team_name} (ID: {team_id}). Team skipped.")
            # Optional: Add delay between teams?
            # time.sleep(random.uniform(3, 7)) # Example random delay


    except Exception as e:
        logging.critical(f"A critical error occurred during driver setup or the main team processing loop: {e}", exc_info=True)
    finally:
        if driver:
            try:
                logging.info("Quitting WebDriver after processing all teams...")
                driver.quit()
                logging.info("Browser closed.")
            except Exception as quit_err:
                logging.error(f"Error occurred while closing the browser: {quit_err}")

    # --- Concatenate All Team Results and Save to CSV ---
    logging.info("\n" + "="*20 + f" Concatenating and Saving Data for ALL Processed Teams " + "="*20)

    if all_teams_dataframes: # Check if we got data for at least one team
        try:
            final_df = pd.concat(all_teams_dataframes, ignore_index=True)
            logging.info(f"Concatenated DataFrames for {len(all_teams_dataframes)} teams. Final combined shape: {final_df.shape}")

            if not final_df.empty:
                # Define final column order including NEW BBI columns
                final_merged_cols = [
                    'Player', 'Player ID', 'Team ID', 'First Season', 'Last Season', # Keys
                    'Mat', # Combined Matches
                    # Batting Stats
                    'Inns_bat', 'NO', 'Runs Scored', 'HS', 'Batting Ave', 'Batting SR', '100', '50', '0',
                    # Bowling Stats
                    'Inns_bowl', 'Mdns', 'Runs Conceded', 'Wkts',
                    'BBI Wickets', 'BBI Runs', # New BBI columns
                    'Bowling Ave', 'Econ', 'Bowling SR', '5 Wkts', '10 Wkts'
                ]

                # Filter/reorder based on columns actually present
                final_cols_present = [col for col in final_merged_cols if col in final_df.columns]
                missing_cols = [col for col in final_merged_cols if col not in final_df.columns]
                if missing_cols:
                    logging.warning(f"Columns missing from final concatenated data: {missing_cols}")

                final_df = final_df[final_cols_present]
                logging.info(f"Final columns selected and ordered for combined CSV: {final_cols_present}")

                # --- Save to CSV ---
                logging.info(f"Saving combined data for ALL processed teams to CSV file: {OUTPUT_CSV_PATH}")
                final_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
                logging.info(f"Successfully saved data to {OUTPUT_CSV_PATH}")
                print(f"\n*** Combined player data for ALL processed teams successfully saved to: {OUTPUT_CSV_PATH} ***")
                print(f"    You can now connect Power BI to this CSV file.")
            else:
                 logging.warning(f"Final concatenated DataFrame is empty after processing all teams. No CSV file generated.")
                 print(f"\n--- Final data is empty after processing all teams. No CSV file generated. ---")

        except Exception as e_proc:
            logging.error(f"Error concatenating DataFrames or saving final CSV: {e_proc}", exc_info=True)
            print(f"\n--- Error processing or saving final combined data. Check logs: {log_filename} ---")
    else:
        logging.warning(f"No valid data collected for ANY team. Cannot generate CSV.")
        print(f"\n--- No valid data retrieved for any team. No CSV file generated. ---")

    # --- Final Summary ---
    overall_end_time = time.time(); total_duration = overall_end_time - overall_start_time
    total_minutes = total_duration / 60
    logging.info(f"\nScript finished in {total_duration:.2f} seconds ({total_minutes:.2f} minutes).")
    try:
        if 'final_df' in locals() and not final_df.empty:
             logging.info(f"Final combined DataFrame shape: {final_df.shape}")
        else:
             logging.info("Final combined DataFrame was empty or not created.")
    except NameError:
         logging.info("Final combined DataFrame was not created due to earlier errors.")
    logging.info(f"Processed data for {len(all_teams_dataframes)} out of {len(IPL_TEAMS)} defined teams.")
    logging.info("="*50 + " Script End " + "="*50)