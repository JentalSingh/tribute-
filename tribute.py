import os
import time
import random
import string
import logging
import requests
from faker import Faker
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RaiselyAutomation")

fake = Faker()

ENV_FILE_PATH = ".env"
if os.path.exists(ENV_FILE_PATH):
    load_dotenv(ENV_FILE_PATH)
else:
    logger.error(f"❌ '{ENV_FILE_PATH}' file nahi mili!")
    exit(1)

PROXY_FILE = os.getenv("PROXY_FILE_NAME", "Webshare proxies.txt")
TARGET_URL = "https://donate-in-memory-awh.raiselysite.com/signup"

def get_live_proxy():
    possible_names = [PROXY_FILE, "Webshare proxies.txt", "Webshare proxies"]
    chosen_file = None
    for name in possible_names:
        if os.path.exists(name):
            chosen_file = name
            break
    if not chosen_file:
        logger.warning("⚠️ Proxy file missing. Running proxyless.")
        return None

    with open(chosen_file, "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not proxies:
        return None

    random.shuffle(proxies)
    for proxy in proxies:
        parts = proxy.strip().split(":")
        if len(parts) == 4:
            ip, port, user, password = parts
            formatted_proxy = f"http://{user}:{password}@{ip}:{port}"
        else:
            formatted_proxy = proxy if proxy.startswith("http") else f"http://{proxy}"
            
        proxies_dict = {"http": formatted_proxy, "https": formatted_proxy}
        try:
            response = requests.get("https://www.google.com", proxies=proxies_dict, timeout=6)
            if response.status_code == 200:
                logger.info(f"✅ LIVE PROXY CONFIRMED: {proxy}")
                return proxy
        except Exception:
            continue
    return None

def parse_proxy_for_playwright(proxy_str):
    if not proxy_str:
        return None
    try:
        cleaned = proxy_str.replace("http://", "").replace("https://", "")
        parts = cleaned.split(":")
        if len(parts) == 4:
            ip, port, username, password = parts
            return {"server": f"http://{ip}:{port}", "username": username, "password": password}
        else:
            return {"server": f"http://{cleaned}"}
    except Exception as e:
        logger.error(f"❌ Parse proxy exception: {e}")
        return None

def generate_profile():
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}{last_name.lower()}{random.randint(10,999)}@gmail.com"
    password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=12))
    tribute_name = fake.first_name()
    return first_name, last_name, email, password, tribute_name

def load_page_with_retry(page, url, max_retries=3):
    """🔥 NEW: Load page with retry and better wait strategy"""
    for attempt in range(max_retries):
        try:
            logger.info(f"🌐 Loading page (attempt {attempt + 1}/{max_retries})...")
            
            # Use domcontentloaded instead of networkidle (faster)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Additional wait for network to settle
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            logger.info("✅ Page loaded successfully!")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Load attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                logger.error("❌ All load attempts failed!")
                return False

def run_raisely_automation():
    first_name, last_name, email, password, tribute_name = generate_profile()
    signup_success = False
    tribute_success = False
    
    raw_proxy = get_live_proxy()
    playwright_proxy = parse_proxy_for_playwright(raw_proxy) if raw_proxy else None

    with sync_playwright() as p:
        logger.info("🚀 Starting browser...")
        
        # 🔥 BROWSER LAUNCH OPTIONS
        launch_options = {
            "headless": False,
            "slow_mo": 2000,
        }
        
        if playwright_proxy:
            launch_options["proxy"] = playwright_proxy
            logger.info(f"🌐 Using proxy: {raw_proxy}")
        else:
            logger.info("🌐 No proxy, running direct")
        
        browser = p.chromium.launch(**launch_options)
            
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # 🔥 Load page with retry
        if not load_page_with_retry(page, TARGET_URL):
            logger.error("❌ Failed to load page, exiting...")
            browser.close()
            return
        
        time.sleep(3)
        
        # ============================================
        # STEP 1: Fill Signup Form (Page 1)
        # ============================================
        logger.info("📝 STEP 1: Filling signup form...")
        
        # First Name - name="firstName" id="firstName"
        try:
            fname = page.locator("input#firstName, input[name='firstName']").first
            if fname and fname.is_visible():
                fname.fill(first_name)
                logger.info(f"✅ First Name: {first_name}")
                time.sleep(1)
            else:
                fname = page.locator("input[type='text']").first
                if fname and fname.is_visible():
                    fname.fill(first_name)
                    logger.info(f"✅ First Name (fallback): {first_name}")
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ First Name: {e}")
        
        # Last Name
        try:
            lname = page.locator("input#lastName, input[name='lastName']").first
            if lname and lname.is_visible():
                lname.fill(last_name)
                logger.info(f"✅ Last Name: {last_name}")
                time.sleep(1)
            else:
                lname = page.locator("input[type='text']").nth(1)
                if lname and lname.is_visible():
                    lname.fill(last_name)
                    logger.info(f"✅ Last Name (fallback): {last_name}")
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Last Name: {e}")
        
        # Email
        try:
            email_input = page.locator("input#email, input[name='email'], input[type='email']").first
            if email_input and email_input.is_visible():
                email_input.fill(email)
                logger.info(f"✅ Email: {email}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Email: {e}")
        
        # Password
        try:
            pwd = page.locator("input#password, input[name='password'], input[type='password']").first
            if pwd and pwd.is_visible():
                pwd.fill(password)
                logger.info(f"✅ Password: {'*' * len(password)}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Password: {e}")
        
        # Click CONTINUE
        logger.info("🚀 Clicking CONTINUE...")
        try:
            continue_btn = page.locator("button:has-text('CONTINUE')").first
            if continue_btn and continue_btn.is_visible():
                continue_btn.click()
                logger.info("✅ CONTINUE clicked!")
                signup_success = True
                time.sleep(5)
        except Exception as e:
            logger.error(f"❌ CONTINUE failed: {e}")
        
        # Wait for tribute page
        time.sleep(5)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass
        
        # ============================================
        # STEP 2: Fill "Who is this tribute for?" (Page 2)
        # ============================================
        logger.info("📝 STEP 2: Filling tribute name...")
        
        try:
            tribute_input = page.locator("input[placeholder*='Who is this tribute'], input[placeholder*='tribute for']").first
            
            if not tribute_input or not tribute_input.is_visible():
                all_inputs = page.locator("input[type='text']").all()
                for inp in all_inputs:
                    if inp.is_visible():
                        tribute_input = inp
                        break
            
            if tribute_input and tribute_input.is_visible():
                tribute_input.fill(tribute_name)
                logger.info(f"✅ Tribute for: {tribute_name}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ Tribute name: {e}")
        
        # ============================================
        # STEP 3: Click CREATE TRIBUTE PAGE
        # ============================================
        logger.info("🚀 STEP 3: Clicking CREATE TRIBUTE PAGE...")
        
        for attempt in range(3):
            try:
                create_btn = page.locator("button:has-text('CREATE TRIBUTE PAGE')").first
                
                if create_btn and create_btn.is_visible():
                    create_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    create_btn.click()
                    logger.info("✅ CREATE TRIBUTE PAGE clicked!")
                    tribute_success = True
                    time.sleep(5)
                    break
                else:
                    create_btn = page.locator("button").filter(has_text="CREATE").first
                    if create_btn and create_btn.is_visible():
                        create_btn.click()
                        logger.info("✅ CREATE TRIBUTE PAGE clicked (filter)!")
                        tribute_success = True
                        time.sleep(5)
                        break
            except Exception as e:
                logger.warning(f"⚠️ Create attempt {attempt+1}: {e}")
                time.sleep(2)
        
        time.sleep(5)
        browser.close()

    # ============================================
    # SUCCESS OUTPUT
    # ============================================
    print("\n" + "=" * 75)
    print("🎉 RAISELY TRIBUTE PAGE CREATED!")
    print("=" * 75)
    print(f"✅ Signup: {'SUCCESS' if signup_success else 'FAILED'}")
    print(f"✅ Tribute: {'SUCCESS' if tribute_success else 'FAILED'}")
    print(f"\n📧 Gmail ID: {email}")
    print(f"🔑 Password: {password}")
    print(f"👤 Tribute For: {tribute_name}")
    print(f"🌐 Proxy: {raw_proxy if raw_proxy else 'None'}")
    print("=" * 75)
    
    try:
        with open("raisely_accounts.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Password: {password}\n")
            f.write(f"Tribute: {tribute_name}\n")
            f.write(f"Proxy: {raw_proxy}\n")
            f.write(f"Success: {tribute_success}\n")
        logger.info("💾 Account saved to raisely_accounts.txt")
    except Exception as e:
        logger.warning(f"⚠️ Save failed: {e}")

if __name__ == "__main__":
    run_raisely_automation()