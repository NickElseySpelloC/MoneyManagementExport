"""Money Management Exporter."""
import re
import sys

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from sc_utility import CSVReader, DateHelper, SCCommon, SCConfigManager, SCLogger

from config_schemas import ConfigSchema

CONFIG_FILE = "config.yaml"


def get_browser_context(config, logger):
    """
    Initializes a Playwright browser context with a realistic user-agent.

    Args:
        config (SCConfigManager): The configuration manager instance.
        logger (SCLogger): The logger instance for logging messages.

    Returns:
        tuple: A tuple containing (playwright_instance, browser_context) or (None, None) on failure.

    Raises:
        RuntimeError: If the browser fails to launch or if Playwright is not installed correctly.
    """
    headless_mode = config.get("MoneyManagement", "HeadlessMode", default=True)
    error_msg = None

    try:
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=headless_mode)
        if browser is None:
            p.stop()
            error_msg = "Failed to launch browser. Ensure Playwright is installed correctly."
        else:
            logger.log_message("Browser launched successfully", "debug")

    except (ImportError, OSError, RuntimeError) as e:
        error_msg = f"Failed to initialize browser context: {e}"

    else:
        context = browser.new_context()
        return (p, context)

    if error_msg:
        raise RuntimeError(error_msg)
    return None, None


def get_page_content(config, logger, browser_context, url) -> str | None:
    """
    Initializes a Playwright browser page with a realistic user-agent.

    Args:
        config (SCConfigManager): The configuration manager instance.
        logger (SCLogger): The logger instance for logging messages.
        browser_context (object): The Playwright browser context object.
        url (str): The URL to navigate to.

    Returns:
        html (str): The contents of the page or None
    """
    logger.log_message(f"Getting content for page {url}", "debug")
    timeout_time = config.get("MoneyManagement", "PageLoad", default=10) * 1000  # Convert seconds to milliseconds
    page = browser_context.new_page()
    if not page:
        logger.log_fatal_error("Failed to create new browser page.")
        return None

    # Set a realistic user-agent
    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })

    # Navigate to the specified URL
    page.goto(url)

    # Wait for the "Exit Price" text to be available in the page
    try:
        page.wait_for_selector("text=Exit Price", timeout=timeout_time)
    except TimeoutError:
        # If "Exit Price" is not found, fall back to general page load timeout
        try:
            page.wait_for_timeout(timeout_time)
        except TimeoutError:
            logger.log_message(f"Timeout waiting for required selector on page {url}", "error")
            return None

    # Get the HTML content of the page
    html = page.content()
    return html


def extract_fund_data(logger, fund, html: str) -> dict | None:
    """
    Extracts the exit price and date from the HTML content.

    Args:
        logger (SCLogger): The logger instance for logging messages.
        fund (dict): A dictionary containing fund information as specified in the config.
        html (str): The HTML content of the page.

    Returns:
        fund_price (dict): A dict object containing the price, effectove date, name and currency or None if not found.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Create a dictionary to hold the fund data
    fund_data = {
        "Symbol": fund.get("Symbol", "Unknown"),
        "Date": DateHelper.today(),  # Use today's date if no date is found
        "Name": fund.get("Name", "Unknown"),
        "Currency": "AUD",
        "Price": None,
    }

    # First get the exit price. Find all table cells containing "Exit Price:"
    exit_price_cells = soup.find_all("td", string=re.compile(r"Exit Price:", re.IGNORECASE))

    for cell in exit_price_cells:
        # Get the next sibling cell in the same row
        next_cell = cell.find_next_sibling("td")
        if next_cell:
            cell_text = next_cell.text.strip()
            # Parse price and date from format like "$1.00 (29/06/2025)"
            match = re.match(r"\$?([\d.]+)\s*\((\d{2}/\d{2}/\d{4})\)", cell_text)
            if match:
                price_str, date_str = match.groups()
                fund_data["Price"] = float(price_str)
                fund_data["Date"] = DateHelper.parse_date(date_str, "%d/%m/%Y")
            else:
                # If pattern doesn't match, try to extract just the price
                price_match = re.search(r"\$?([\d.]+)", cell_text)
                if price_match:
                    fund_data["Price"] = float(price_match.group(1))

    # Now get fund name. Find the first <h1> tag with class "mt-2"
    fund_name_tag = soup.find("h1", class_="mt-2")
    if fund_name_tag:
        fund_data["Name"] = fund_name_tag.text.strip()

    # Now get the symbol
    symbol_cells = soup.find_all("td", string=re.compile(r"APIR code:", re.IGNORECASE))
    for cell in symbol_cells:
        # Get the next sibling cell in the same row
        next_cell = cell.find_next_sibling("td")
        if next_cell:
            fund_data["Symbol"] = next_cell.text.strip()

    # Now get the currency
    currency_cells = soup.find_all("td", string=re.compile(r"Currency:", re.IGNORECASE))
    for cell in currency_cells:
        # Get the next sibling cell in the same row
        next_cell = cell.find_next_sibling("td")
        if next_cell:
            fund_data["Currency"] = next_cell.text.strip()

    logger.log_message(f"Extracted fund data: {fund_data}", "debug")
    return fund_data if fund_data["Price"] is not None else None


def close_browser(logger, playwright_instance, context):
    """
    Closes the Playwright browser context and playwright instance.

    Args:
        logger (SCLogger): The logger instance for logging messages.
        playwright_instance: The Playwright instance to stop.
        context (object): The Playwright browser context to close.
    """
    logger.log_message("Closing browser session", "debug")
    if context:
        browser = context.browser
        context.close()
        browser.close()
    if playwright_instance:
        playwright_instance.stop()


def get_fund_prices(config, logger) -> list:
    """
    Fetches fund prices from the URLs specified in the configuration.

    Args:
        config (SCConfigManager): The configuration manager instance.
        logger (SCLogger): The logger instance for logging messages.

    Returns:
        list: A list of fund prices extracted from the specified URLs.
    """
    logger.log_message("Starting get_fund_prices()", "debug")
    fund_prices = []
    funds = config.get("MoneyManagement", "Funds", default=[])

    # Create a browser context for fetching fund prices
    try:
        playwright_instance, context = get_browser_context(config, logger)
    except RuntimeError as e:
        logger.log_fatal_error(f"Failed to create browser context: {e}")
        return fund_prices

    # Iterate over each fund URL in the configuration
    for fund in funds:
        logger.log_message(f"Getting price for fund {fund.get("Name")}", "debug")
        url = fund.get("URL")
        html = get_page_content(config, logger, context, url)
        if html:
            # Extract the price and date from the HTML content
            fund_data = extract_fund_data(logger, fund, html)
            if fund_data is not None:
                fund_prices.append(fund_data)
                logger.log_message(f"Fetched price for {fund.get('Name')}: {fund_data['Price']} on {fund_data['Date']}", "debug")
            else:
                logger.log_message(f"No price found for {fund.get('Name')} at {url}", "warning")

    # Close the browser context after fetching all fund prices
    close_browser(logger, playwright_instance, context)

    # Return the list of fund prices
    return fund_prices


def save_prices_to_csv(fund_prices, config, logger, header_config):
    """
    Saves the fund prices to a CSV file.

    Args:
        fund_prices (list[dict]): The list of fund prices to save.
        config (SCConfigManager): The configuration manager instance.
        logger (SCLogger): The logger instance for logging messages.
        header_config (list[dict]): The configuration for the CSV header.
    """
    csv_path = SCCommon.select_file_location(config.get("Files", "OutputCSV", default="price_data.csv"))
    assert csv_path is not None, "CSV file path cannot be empty."

    # Second entry in header_config is the Date column
    header_config[1]["minimum"] = DateHelper.today_add_days(-config.get("Files", "DaysToSave", default=365))

    # Create an instance of the CSVReader class and update the file
    try:
        csv_reader = CSVReader(csv_path, header_config)
        csv_reader.update_csv_file(fund_prices)
    except (ImportError, TypeError, ValueError, RuntimeError) as e:
        logger.log_fatal_error(f"Failed to update CSV file: {e}")


def main():
    """Get our default schema, validation schema, and placeholders."""
    schemas = ConfigSchema()

    # Initialize the SCConfigManager class
    try:
        config = SCConfigManager(
            config_file=CONFIG_FILE,
            default_config=schemas.default,
            validation_schema=schemas.validation,
            placeholders=schemas.placeholders
        )
    except RuntimeError as e:
        print(f"Configuration file error: {e}", file=sys.stderr)
        sys.exit(1)     # Exit with errorcode 1 so that launch.sh can detect it

    # Initialize the SCLogger class
    try:
        logger = SCLogger(config.get_logger_settings())
    except RuntimeError as e:
        print(f"Logger initialisation error: {e}", file=sys.stderr)
        sys.exit(1)     # Exit with errorcode 1 so that launch.sh can detect it

    # Startup message
    logger.log_message("Starting Money Management Exporter", "summary")

    # Setup email
    logger.register_email_settings(config.get_email_settings())

    # Get the fund prices for each fund listed in the config
    fund_prices = get_fund_prices(config, logger)

    # Save the fund prices to a CSV file
    save_prices_to_csv(fund_prices, config, logger, schemas.csv_header_config)

    # Final message
    logger.log_message("Fund prices export complete.", "summary")

    # If the prior run fails, send email that this run worked OK
    if logger.get_fatal_error():
        logger.log_message(
            "Run was successful after a prior failure.", "summary"
        )
        logger.send_email(
            "Run recovery",
            "Run was successful after a prior failure.",
        )
        logger.clear_fatal_error()


if __name__ == "__main__":
    main()
