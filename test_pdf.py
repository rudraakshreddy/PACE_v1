from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--window-size=1920,1080')
options.add_argument('--log-level=3')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
driver = webdriver.Chrome(options=options)

try:
    print("Opening page...")
    driver.get("http://pace_permionics:satyaraj_permionics%402026@127.0.0.1:8000")
    
    time.sleep(2)
    print("Logs after load:")
    for entry in driver.get_log('browser'):
        print(entry)
        
    print("Clicking Process Rec...")
    driver.find_element(By.ID, "process-tab-btn").click()
    
    print("Clicking Report Tab...")
    driver.find_element(By.ID, "report-tab-btn").click()
    
    print("Clicking Generate Preview...")
    driver.find_element(By.ID, "wave-report-generate-btn").click()
    
    time.sleep(3)
    print("Clicking Download PDF...")
    driver.find_element(By.ID, "wave-report-download-btn").click()
    
    time.sleep(1)
    print("Logs after download click:")
    for entry in driver.get_log('browser'):
        print(entry)
        
finally:
    driver.quit()
