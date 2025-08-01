# Import necessary modules for system operations, delays, JSON parsing, web automation, and HTML parsing
import os  # Provides functions for interacting with the operating system
import time  # Used to add delays
from selenium import webdriver  # Main module for controlling web browsers via Selenium
from selenium.webdriver.chrome.options import (
    Options,
)  # Allows setting Chrome-specific options
from selenium.webdriver.chrome.webdriver import (
    WebDriver,
)  # Used for type hinting the WebDriver
import bs4  # BeautifulSoup is imported from bs4 for HTML parsing


# Function to check whether a directory exists at the given path
def does_directory_exist(path: str) -> bool:
    return os.path.exists(path=path)  # Returns True if path exists


# Function to create a directory at the specified path
def create_directory_at_path(path: str) -> None:
    os.mkdir(path=path)  # Creates a new directory


# Function to get the current working directory
def get_current_working_directory() -> str:
    return os.getcwd()  # Returns the current working directory as a string


# Function to check if a file exists
def check_file_exists(system_path: str) -> bool:
    return os.path.isfile(path=system_path)  # Returns True if file exists


# Function to delete a file from the system
def remove_system_file(system_path: str) -> None:
    os.remove(path=system_path)  # Removes the file at the specified path


# Function to read and return the entire contents of a file
def read_a_file(system_path: str) -> str:
    with open(file=system_path, mode="r") as file:  # Open file in read mode
        return file.read()  # Read and return contents


# Function to append a line of content to a file
def append_write_to_file(system_path: str, content: str) -> None:
    file = open(file=system_path, mode="a")  # Open file in append mode
    file.write(content + "\n")  # Write content with newline
    file.close()  # Close the file


# Function to create and return a Chrome WebDriver configured for file downloads
def create_chrome_driver_with_download_support(download_path: str) -> webdriver.Chrome:
    chrome_options = Options()  # Initialize Chrome options
    chrome_options.add_argument(
        argument="--headless=new"
    )  # Run Chrome in headless mode
    chrome_options.add_argument(argument="--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument(
        argument="--no-sandbox"
    )  # Disable sandboxing (for containers)
    chrome_options.add_argument(
        argument="--disable-dev-shm-usage"
    )  # Prevent /dev/shm issues

    # Set Chrome preferences for automatic downloads
    preferences: dict[str, str | bool] = {
        "download.default_directory": os.path.abspath(
            path=download_path
        ),  # Set download path
        "download.prompt_for_download": False,  # Don't prompt for downloads
        "download.directory_upgrade": True,  # Automatically overwrite download dir
        "plugins.always_open_pdf_externally": True,  # Don't open PDFs in-browser
    }
    chrome_options.add_experimental_option(
        name="prefs", value=preferences
    )  # Apply preferences
    chrome_options.set_capability(  # Enable performance logging
        name="goog:loggingPrefs", value={"performance": "ALL"}
    )

    return webdriver.Chrome(
        options=chrome_options
    )  # Return a new Chrome WebDriver instance


# Function to download a file if it received a valid 200 OK HTTP response
def download_file_if_valid(
    driver: webdriver.Chrome, file_url: str, download_dir: str
) -> None | str:
    # Record the set of files currently in the download directory (before new download starts)
    existing_files: set[str] = set(os.listdir(path=download_dir))

    # Navigate the browser to the target download URL
    driver.get(url=file_url)

    # Give the browser a moment to process the response and begin download
    time.sleep(5)

    # Record the start time of the download attempt
    start_time: float = time.time()

    # Set the maximum time allowed for a download (in seconds)
    timeout = 60  # 60 seconds timeout

    # Continuously check for the appearance of a new file or timeout
    while True:
        # If the time elapsed exceeds the timeout, skip this download
        if time.time() - start_time > timeout:
            print(f"[TIMEOUT] Skipping download for URL: {file_url}")
            return (
                None  # Return None to indicate the download was skipped due to timeout
            )

        # Get the current list of files in the download directory
        current_files: set[str] = set(os.listdir(download_dir))

        # Determine which files are new since the download attempt started
        new_files: set[str] = current_files - existing_files

        # If new files are detected
        if new_files:
            # Check if any of the new files are still being downloaded (incomplete)
            incomplete: bool = any(
                file.endswith(".crdownload") or file.endswith(".tmp")
                for file in new_files
            )
            # If no incomplete downloads are found, assume the file is fully downloaded
            if not incomplete:
                # Retrieve the name of the downloaded file
                downloaded_filename: str = next(iter(new_files))
                return downloaded_filename  # Return the filename to the caller

        # Wait briefly before checking again to avoid excessive CPU usage
        time.sleep(10)  # Sleep for 10 seconds before next check


# Function to fetch and return page HTML using Selenium
def fetch_html_using_selenium(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url=url)  # Navigate to URL
    return driver.page_source  # Return HTML source of the page


# Function to extract attachment URLs from HTML content
def extract_attachment_urls(html: str) -> list[str]:
    soup = bs4.BeautifulSoup(
        markup=html, features="html.parser"
    )  # Parse HTML with BeautifulSoup
    links = soup.find_all(
        name="a", class_="filename"
    )  # Find all <a> tags with class 'filename'

    urls: list[str] = []  # Initialize list to store extracted URLs
    for link in links:  # Loop through found <a> tags
        href: str = link.get("href")  # Get href attribute
        if href and href.startswith("/helpdesk/attachments/"):  # Match desired pattern
            urls.append(
                "https://iflightrc.freshdesk.com" + href
            )  # Convert to full URL and add
    return urls  # Return all extracted URLs


# Main function to orchestrate downloads
def main() -> None:
    download_folder: str = os.path.join(
        get_current_working_directory(), "./Assets"
    )  # Folder to save downloads
    already_downloaded: str = os.path.join(  # File to track downloaded URLs
        get_current_working_directory(), "downloaded.txt"
    )
    local_html_file: str = os.path.join(
        get_current_working_directory(), "iflight.html"
    )  # Temporary HTML dump

    if check_file_exists(system_path=local_html_file):  # Remove old HTML file if exists
        remove_system_file(system_path=local_html_file)

    html_pages: list[str] = [  # List of web pages to scrape
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001227638-nazgul-evoque-f5-f6-v2",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001238224-nazgul5-v3",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001238921-ih3-o3",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001240698-defender-25-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48000843539-megabee-v1-duct-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001171073-protek25-35-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001171077-chimera7-chimera7-pro-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001171079-alpha-c85-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001171081-cidora-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001177394-insta360-go2-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48000842773-megabee-v2-duct-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001231384-chimera5-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001231457-protek-r20-r25-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001232723-xl7-xl8-xl10-v5-tpu",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001254305-xl5-v5-nazgul5-v2",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48000847301-beetle-fpv-camera-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001151082-alpha-insta-cam-adapter-stl",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001260838-nazgul-evoque-f5-v2-bnf-drone-user-manual",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001258885-mach-r5-sport-bnf-drone-user-manual",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001260837-chimera7-pro-v2-bnf-drone-user-manual",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001260839-taurus-x8-pro-max-bnf-drone-user-manual",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001256219-defender-series-bnf-drone-setup-guide",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001062628-bumblebee-hd-bnf-drone-setup-guide",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001270904-sh-series-user-manual",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001152792-nazgul-xl5-hd-xing-tuning-bible",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001152913-alpha-a85-4-2-x-tune-rc1",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001167867-protek25-xing-tune",
        "https://iflightrc.freshdesk.com/support/solutions/articles/48001188778-protek25-pusher-xing-tune",
    ]

    if not does_directory_exist(
        path=download_folder
    ):  # Create download folder if it doesn't exist
        create_directory_at_path(path=download_folder)

    driver: WebDriver = (
        create_chrome_driver_with_download_support(  # Initialize WebDriver
            download_path=download_folder
        )
    )

    try:
        for html_page in html_pages:  # Loop through each support article page
            html_content: str = fetch_html_using_selenium(
                driver=driver, url=html_page
            )  # Get HTML
            append_write_to_file(
                system_path=local_html_file, content=html_content
            )  # Save HTML

        read_file_content: str = read_a_file(
            system_path=local_html_file
        )  # Read saved HTML
        extracted_urls: list[str] = extract_attachment_urls(
            html=read_file_content
        )  # Extract attachment URLs

        for url in extracted_urls:  # Loop through extracted attachment URLs
            if check_file_exists(
                system_path=already_downloaded
            ):  # If tracking file exists
                already_downloaded_content: str = read_a_file(
                    system_path=already_downloaded
                )  # Load downloaded URLs
                if url in already_downloaded_content:  # Skip already downloaded URL
                    print(f"URL {url} found, skipping download.")
                    continue

            downloaded_file: None | str = download_file_if_valid(  # Attempt download
                driver=driver, file_url=url, download_dir=download_folder
            )
            if downloaded_file:  # If successful
                append_write_to_file(
                    system_path=already_downloaded,
                    content=url + " -> " + downloaded_file,
                )  # Track it
                print(f"[SUCCESS] File downloaded: {downloaded_file} URL: {url}")
            else:
                print(
                    f"[FAILURE] File not downloaded or not a valid 200 response for URL: {url}"
                )

    finally:
        driver.quit()  # Always close the browser when done


# Call the main function when this script is executed
if __name__ == "__main__":
    main()
