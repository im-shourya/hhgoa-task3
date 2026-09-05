from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Method 2: Navigate to lens.google.com directly
        print("Navigating to lens.google.com...")
        page.goto("https://lens.google.com/")
        time.sleep(2)
        
        file_input = page.locator('input[type="file"]')
        if file_input.count() > 0:
            print("Uploading file...")
            file_input.first.set_input_files("tests/fixtures/search/einstein.jpg")
        else:
            print("No file input found on lens.google.com")
            
            print("Trying google.com images again with popup wait...")
            page.goto("https://images.google.com/")
            page.locator('[aria-label="Search by image"], .nDcEnd').first.click()
            time.sleep(1)
            file_input = page.locator('input[type="file"]')
            
            with page.expect_navigation(timeout=15000):
                file_input.set_input_files("tests/fixtures/search/einstein.jpg")
        
        # Wait for navigation / results
        print("Waiting for results...")
        try:
            page.wait_for_selector('a[href]', timeout=15000)
            time.sleep(5)
        except Exception as e:
            print("Timeout:", e)
        
        print("Current URL:", page.url)
        
        print("Extracting candidates...")
        links = page.locator('a[href]').all()
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http") and "google.com" not in href:
                print("Candidate Link:", href)
                
        browser.close()

if __name__ == "__main__":
    main()
