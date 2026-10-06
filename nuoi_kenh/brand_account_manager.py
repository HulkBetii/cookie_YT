# -*- coding: utf-8 -*-
"""
brand_account_manager.py — Brand Account Factory & Lifecycle Engine
Automates creation, scraping, identity switching, and progressive warmup
for YouTube Brand Accounts under nuoi-kenh-youtube architecture.
"""
import os
import re
import sys
import time
import random
import sqlite3
import argparse
import datetime
from typing import List, Dict, Any, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

from .config import (
    SHARED_DB_PATH,
    GPM_API_URL,
    DANH_SACH_TU_KHOA,
    TU_KHOA_LIEN_QUAN,
    MIN_GIAY_XEM,
    MAX_GIAY_XEM,
    REQUIRED_PROFILE_REGEX,
)
from .logger import log
from .selenium_utils import safe_get, selenium_call, _cho_trang_load
from .human_behavior import (
    delay,
    kiem_tra_ket_noi,
    go_co_loi_chinh_ta,
    draw_session_mood,
    SessionMood,
)
from .cdp import cdp_click, cdp_move_mouse
from .youtube import xem_youtube
from .gpm_api import mo_profile_gpm, dong_profile_gpm

# ── Niche Definitions & Name Templates ────────────────────────────

NICHE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "tech": {
        "first": ["Alex", "Leo", "David", "Lucas", "Ethan", "Sam", "Felix", "Ryan", "Marcus", "Victor"],
        "middle": ["Tech", "Code", "Dev", "Byte", "Silicon", "Cyber", "Gadget", "System", "Cloud", "Logic"],
        "last": ["Reviews", "Lab", "Hub", "Daily", "Insights", "Zone", "Station", "HQ", "Studio", "Vault"],
        "keywords": [
            "MKBHD latest review",
            "Apple Silicon M4 benchmarks",
            "Linux setup productivity",
            "Python coding projects 2026",
            "AI tools for developers",
            "Best mechanical keyboards",
            "Building custom PC guide",
            "Cybersecurity fundamentals",
        ],
    },
    "gaming": {
        "first": ["Shadow", "Pixel", "Nova", "Blaze", "Apex", "Ghost", "Vortex", "Frost", "Iron", "Titan"],
        "middle": ["Gamer", "Play", "Quest", "Arcade", "Zone", "Strike", "Realm", "Force", "Matrix", "Knight"],
        "last": ["Hub", "Chronicles", "Vlogs", "HQ", "Plays", "Central", "Arena", "Clips", "Station", "Universe"],
        "keywords": [
            "Elden Ring DLC walkthrough",
            "Steam deck indie games",
            "Best gaming monitor setup",
            "Minecraft survival series",
            "Top RPG games 2026",
            "Unreal Engine 5 showcase",
            "Retro gaming collection",
            "Speedrun world record analysis",
        ],
    },
    "lifestyle": {
        "first": ["Emma", "Chloe", "Noah", "Liam", "Olivia", "Sophia", "Aiden", "Maya", "Elena", "Lucas"],
        "middle": ["Life", "Vibe", "Daily", "Living", "Journeys", "Moments", "Routine", "Habits", "Spaces", "Mind"],
        "last": ["Diary", "Chronicles", "Space", "Vlog", "Haven", "Path", "Corner", "Notes", "Studio", "Flow"],
        "keywords": [
            "Morning routine of high performers",
            "Minimalist apartment tour",
            "Healthy meal prep for busy week",
            "Daily journaling habits",
            "Work from home desk ergonomics",
            "Mindfulness and slow living",
            "Travel vlog Kyoto Japan",
            "Budget travel packing tips",
        ],
    },
    "finance": {
        "first": ["Carter", "Mason", "Sterling", "Morgan", "Grant", "Arthur", "Vance", "Harrison", "Pierce", "Warren"],
        "middle": ["Wealth", "Asset", "Capital", "Finance", "Growth", "Market", "Equity", "Trust", "Fund", "Alpha"],
        "last": ["Insights", "Blueprint", "Daily", "Ventures", "Advisory", "Network", "Digest", "Hub", "Edge", "Guide"],
        "keywords": [
            "Personal finance for beginners",
            "Index fund investing strategy",
            "Passive income real estate",
            "Stock market analysis 2026",
            "Emergency fund budgeting",
            "Understanding dividend yield",
            "Retirement planning 401k",
            "Crypto vs precious metals analysis",
        ],
    },
    "general": {
        "first": ["Chris", "Jordan", "Taylor", "Morgan", "Avery", "Casey", "Riley", "Jesse", "Jamie", "Skyler"],
        "middle": ["World", "Vibe", "Life", "Focus", "Pulse", "Scope", "View", "Orbit", "Echo", "Wave"],
        "last": ["Channel", "Station", "Network", "Vlogs", "Studio", "Digest", "Daily", "Hub", "Lab", "Zone"],
        "keywords": [
            "Huberman Lab productivity",
            "Feynman technique learning fast",
            "Lex Fridman podcast highlights",
            "James Webb telescope new images",
            "How to build focus and discipline",
            "Science documentary 4k",
        ],
    },
}


def generate_channel_name(niche: str = "general") -> str:
    """Generate an authentic creator channel name for a specific niche."""
    niche_key = niche.lower() if niche.lower() in NICHE_TEMPLATES else "general"
    data = NICHE_TEMPLATES[niche_key]

    f = random.choice(data["first"])
    m = random.choice(data["middle"])
    l = random.choice(data["last"])

    pattern = random.choice([1, 2, 3, 4])
    if pattern == 1:
        return f"{f} {m} {l}"
    elif pattern == 2:
        return f"{f}'s {m}"
    elif pattern == 3:
        return f"{m} {l}"
    else:
        return f"{f} {l}"


# ── Database Layer (account_pool.db) ──────────────────────────────

def get_shared_db(db_path: str = SHARED_DB_PATH) -> sqlite3.Connection:
    """Connect to shared/account_pool.db with WAL mode and row factory."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Shared account database not found at: {db_path}")
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def lock_sub_account(
    account_id: int,
    locked_by: str = "nuoi_kenh",
    duration_min: int = 30,
    db_path: str = SHARED_DB_PATH,
) -> bool:
    """Acquire a temporary lock on a sub_account."""
    conn = get_shared_db(db_path)
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM account_locks WHERE account_id = ? AND expires_at <= datetime('now');",
            (account_id,),
        )
        cur.execute(
            """
            INSERT INTO account_locks (account_id, locked_by, locked_at, expires_at)
            VALUES (?, ?, datetime('now'), datetime('now', '+' || ? || ' minutes'));
            """,
            (account_id, locked_by, duration_min),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def release_sub_account_lock(
    account_id: int,
    locked_by: Optional[str] = "nuoi_kenh",
    db_path: str = SHARED_DB_PATH,
) -> bool:
    """Release a lock on a sub_account."""
    conn = get_shared_db(db_path)
    cur = conn.cursor()
    try:
        if locked_by:
            cur.execute(
                "DELETE FROM account_locks WHERE account_id = ? AND (locked_by = ? OR expires_at <= datetime('now'));",
                (account_id, locked_by),
            )
        else:
            cur.execute("DELETE FROM account_locks WHERE account_id = ?;", (account_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def sync_discovered_brand_accounts(
    profile_id: str,
    channels: List[Dict[str, Any]],
    niche: str = "general",
    db_path: str = SHARED_DB_PATH,
) -> int:
    """
    Upsert discovered brand accounts into sub_accounts table.
    Returns number of newly inserted accounts.
    """
    conn = get_shared_db(db_path)
    cur = conn.cursor()
    inserted_count = 0

    try:
        for ch in channels:
            switch_name = ch.get("switch_name", "").strip()
            if not switch_name:
                continue

            channel_id = ch.get("channel_id")
            channel_url = ch.get("channel_url")
            account_type = ch.get("account_type", "brand_account")

            # Check if an account with this profile and switch_name already exists
            cur.execute(
                "SELECT id FROM sub_accounts WHERE gpm_profile_id = ? AND switch_name = ?;",
                (profile_id, switch_name),
            )
            row = cur.fetchone()

            if row:
                # Update channel_id / channel_url if missing
                cur.execute(
                    """
                    UPDATE sub_accounts
                    SET channel_id = COALESCE(?, channel_id),
                        channel_url = COALESCE(?, channel_url)
                    WHERE id = ?;
                    """,
                    (channel_id, channel_url, row["id"]),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sub_accounts (
                        gpm_profile_id, account_type, channel_id, channel_url,
                        switch_name, niche, warmup_status, warmup_days, warmup_videos,
                        is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'cold', 0, 0, 1, datetime('now'));
                    """,
                    (profile_id, account_type, channel_id, channel_url, switch_name, niche),
                )
                inserted_count += 1

        conn.commit()
        return inserted_count
    finally:
        conn.close()


# ── Guardrails: Phone Verification Detection ──────────────────────

def is_phone_verify_demanded(driver: webdriver.Chrome) -> bool:
    """
    Detect whether Google is demanding phone number verification.
    If true, automated operations must halt immediately to safeguard root credentials.
    """
    try:
        cur_url = driver.current_url.lower()
        if any(kw in cur_url for kw in ("idv", "idvpreregistered", "challenge/pwd", "speedbump/idv", "phone")):
            return True

        page_source = driver.page_source.lower()
        verify_signals = [
            "verify your account",
            "xác minh tài khoản",
            "enter a phone number",
            "nhập số điện thoại",
            "text message (sms)",
            "voice call",
            "standard call rates apply",
        ]
        for signal in verify_signals:
            if signal in page_source:
                return True

        # Check phone input fields
        phone_inputs = driver.find_elements(
            By.CSS_SELECTOR,
            "input[name='phoneNumber'], input#phoneNumberId, input[type='tel']"
        )
        if any(inp.is_displayed() for inp in phone_inputs):
            return True

        return False
    except Exception as e:
        log(f"  ⚠️ Error during phone verification check: {e}")
        return False


# ── Channel Switcher & Scraper ────────────────────────────────────

def get_existing_brand_accounts(
    driver: webdriver.Chrome,
    profile_id: str,
    niche: str = "general",
    db_path: str = SHARED_DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Navigate to https://www.youtube.com/channel_switcher and scrape all available channels.
    Synchronizes newly found accounts into sub_accounts in account_pool.db.
    """
    log("  🔍 Navigating to YouTube Channel Switcher...")
    if not safe_get(driver, "https://www.youtube.com/channel_switcher", timeout=30):
        log("  ❌ Failed to load channel_switcher page.")
        return []

    time.sleep(random.uniform(3.0, 5.0))

    if is_phone_verify_demanded(driver):
        log("  🚨 PHONE_VERIFY_REQUIRED: Google demands phone verification on switcher.")
        return []

    # Selectors for account items on channel_switcher
    item_selectors = [
        "ytd-account-item-renderer",
        "paper-item.ytd-account-item-renderer",
        "#contents ytd-account-item-renderer",
        "a[href*='/channel/']",
        "a[href*='/@']",
    ]

    elements = []
    for sel in item_selectors:
        try:
            found = driver.find_elements(By.CSS_SELECTOR, sel)
            if found:
                elements = found
                break
        except Exception:
            continue

    channels: List[Dict[str, Any]] = []

    for el in elements:
        try:
            txt = el.text.strip()
            if not txt:
                continue

            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            display_name = lines[0] if lines else ""

            # Skip the 'Create a channel' / 'Tạo kênh' option
            if any(k in display_name.lower() for k in ("create a channel", "tạo kênh", "create channel")):
                continue

            # Check handle or channel url
            channel_url = None
            channel_id = None
            try:
                href = el.get_attribute("href")
                if href and ("youtube.com" in href or "/channel/" in href or "/@" in href):
                    channel_url = href
                    if "/channel/" in href:
                        channel_id = href.split("/channel/")[-1].split("?")[0].split("/")[0]
                    elif "/@" in href:
                        channel_id = "@" + href.split("/@")[-1].split("?")[0].split("/")[0]
            except Exception:
                pass

            # Second line is often handle or sub count (e.g. '@alexreviews' or 'No subscribers')
            if len(lines) > 1 and lines[1].startswith("@") and not channel_id:
                channel_id = lines[1]

            channels.append({
                "switch_name": display_name,
                "channel_id": channel_id,
                "channel_url": channel_url,
                "account_type": "brand_account",
            })
        except Exception as e:
            continue

    log(f"  📋 Found {len(channels)} channels on profile '{profile_id}'.")

    # Sync to database
    if channels:
        # First one might be master gmail root if not registered yet, but usually root is already in DB
        inserted = sync_discovered_brand_accounts(profile_id, channels, niche=niche, db_path=db_path)
        log(f"  💾 Synchronized {inserted} new Brand Accounts to shared DB.")

    return channels


# ── Brand Account Creation Flow ───────────────────────────────────

def create_brand_account(
    driver: webdriver.Chrome,
    profile_id: str,
    channel_name: str,
    niche: str = "general",
    db_path: str = SHARED_DB_PATH,
) -> Dict[str, Any]:
    """
    Automate the creation of a YouTube Brand Account:
    1. Navigate to https://www.youtube.com/account.
    2. Guard against phone verification.
    3. Trigger create channel link and open Polymer modal.
    4. Type channel name with human typing simulation + Polymer binding.
    5. Click submit with Bézier curve CDP click.
    6. Scrape newly created channel URL / ID.
    7. Sync newly created account into account_pool.db with 'cold' status.
    """
    log(f"  🚀 Starting Brand Account Creation: '{channel_name}' (niche: {niche})")

    # Guard: Ensure active window is not chrome extension
    try:
        for h in driver.window_handles:
            driver.switch_to.window(h)
            if "chrome-extension" not in driver.current_url:
                break
    except Exception:
        pass

    # Guard check: phone verification already active
    if is_phone_verify_demanded(driver):
        log("  🚨 PHONE_VERIFY_REQUIRED: Google requested phone verification.")
        return {"status": "PHONE_VERIFY_REQUIRED", "error": "Phone verification detected"}

    # Step 1: Navigate to /account settings page
    if not safe_get(driver, "https://www.youtube.com/account", timeout=35):
        if is_phone_verify_demanded(driver):
            log("  🚨 PHONE_VERIFY_REQUIRED: Redirected to phone verification during navigation.")
            return {"status": "PHONE_VERIFY_REQUIRED", "error": "Phone verification detected"}
        log("  ❌ Could not load /account page.")
        return {"status": "FAILED", "error": "Could not load account page"}

    time.sleep(random.uniform(3.0, 5.0))

    # Guard check: phone verification
    if is_phone_verify_demanded(driver):
        log("  🚨 PHONE_VERIFY_REQUIRED: Google requested phone verification on account page.")
        return {"status": "PHONE_VERIFY_REQUIRED", "error": "Phone verification detected"}

    # Step 2: Locate 'Tạo kênh mới' / 'Create a new channel' link
    create_link = None
    create_link_selectors = [
        "a[href*='/create_channel']",
        "ytd-channel-options-renderer a[href*='create']",
        "a:has(yt-formatted-string)",
    ]

    for sel in create_link_selectors:
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, sel)
            for c in candidates:
                href = c.get_attribute("href") or ""
                txt = (c.text or "").strip().lower()
                if "/create_channel" in href or any(k in txt for k in ("tạo kênh", "create a channel", "create channel")):
                    create_link = c
                    break
            if create_link:
                break
        except Exception:
            continue

    if not create_link:
        log("  ❌ Could not locate 'Create channel' link on /account page.")
        return {"status": "FAILED", "error": "Create channel link not found"}

    log("  🖱️ Triggering create channel dialog...")
    try:
        driver.execute_script("arguments[0].click();", create_link)
    except Exception:
        try:
            cdp_click(driver, create_link)
        except Exception:
            create_link.click()

    time.sleep(random.uniform(1.0, 2.0))

    # Step 3: Open dialog explicitly via Polymer API
    driver.execute_script("""
        let dlg = document.querySelector('tp-yt-paper-dialog');
        if (dlg) {
            dlg.style.display = 'block';
            if (typeof dlg.open === 'function') dlg.open();
        }
    """)
    time.sleep(random.uniform(2.5, 4.0))

    # Guard check: phone verification on dialog
    if is_phone_verify_demanded(driver):
        log("  🚨 PHONE_VERIFY_REQUIRED: Phone verification encountered on create_channel form.")
        return {"status": "PHONE_VERIFY_REQUIRED", "error": "Phone verification detected"}

    # Step 4: Find channel name input field
    input_selectors = [
        "tp-yt-paper-input#title-input input",
        "#title-input input",
        "input#channel-name",
        "input[name='channel-name']",
        "input[placeholder*='name' i]",
        "input[placeholder*='kênh' i]",
    ]

    name_input = None
    for sel in input_selectors:
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, sel)
            for c in candidates:
                if c.is_enabled():
                    name_input = c
                    break
            if name_input:
                break
        except Exception:
            continue

    if not name_input:
        log("  ❌ Could not locate channel name input field on form.")
        return {"status": "FAILED", "error": "Channel name input not found"}

    # Step 5: Type channel name biologically + synchronize Polymer state
    log(f"  ⌨️ Typing channel name: '{channel_name}'...")
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", name_input)
        time.sleep(0.3)
    except Exception:
        pass

    try:
        cdp_click(driver, name_input)
    except Exception:
        try:
            name_input.click()
        except Exception:
            pass
    time.sleep(random.uniform(0.3, 0.6))

    # Human typing simulation
    try:
        go_co_loi_chinh_ta(name_input, channel_name)
    except Exception:
        pass

    # Synchronize Polymer data bindings
    driver.execute_script("""
        let val = arguments[0];
        let paperInp = document.querySelector('tp-yt-paper-input#title-input');
        let realInp = document.querySelector('tp-yt-paper-input#title-input input') || arguments[1];
        if (realInp) {
            realInp.value = val;
            realInp.dispatchEvent(new Event('input', { bubbles: true }));
            realInp.dispatchEvent(new Event('change', { bubbles: true }));
            let ironInp = realInp.closest('tp-yt-iron-input');
            if (ironInp) {
                ironInp.bindValue = val;
                ironInp.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
        if (paperInp) {
            paperInp.value = val;
            paperInp.dispatchEvent(new Event('input', { bubbles: true }));
            paperInp.dispatchEvent(new Event('change', { bubbles: true }));
        }
    """, channel_name, name_input)
    time.sleep(random.uniform(1.0, 2.0))

    # Step 6: Locate & prepare Submit button
    submit_selectors = [
        "#create-channel-button button",
        "ytd-button-renderer#create-channel-button button",
        "button[type='submit']",
        "#submit-button",
    ]
    submit_btn = None
    for sel in submit_selectors:
        try:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            for b in btns:
                submit_btn = b
                break
            if submit_btn:
                break
        except Exception:
            continue

    if not submit_btn:
        log("  ❌ Could not locate submit/create button.")
        return {"status": "FAILED", "error": "Submit button not found"}

    # Ensure button is active
    driver.execute_script("""
        let btn = document.querySelector('#create-channel-button button') || arguments[0];
        if (btn) {
            btn.removeAttribute('disabled');
            btn.setAttribute('aria-disabled', 'false');
            btn.classList.remove('ytSpecButtonShapeNextDisabled');
        }
    """, submit_btn)
    time.sleep(random.uniform(0.5, 1.0))

    log("  🖱️ Submitting brand account creation...")
    try:
        cdp_click(driver, submit_btn)
    except Exception:
        try:
            submit_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", submit_btn)

    # Step 7: Wait for redirection or confirmation
    time.sleep(random.uniform(8.0, 12.0))

    # Guard check: phone verification triggered immediately after submit
    if is_phone_verify_demanded(driver):
        log("  🚨 PHONE_VERIFY_REQUIRED: Google triggered SMS phone check upon submission!")
        return {"status": "PHONE_VERIFY_REQUIRED", "error": "Phone verification demanded after submit"}

    # Scrape final landing URL to get channel ID or handle
    cur_url = driver.current_url
    log(f"  🌐 Final creation landing URL: {cur_url}")

    channel_id = None
    channel_url = None
    if "/channel/" in cur_url:
        channel_id = cur_url.split("/channel/")[-1].split("?")[0].split("/")[0]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
    elif "/@" in cur_url:
        channel_id = "@" + cur_url.split("/@")[-1].split("?")[0].split("/")[0]
        channel_url = f"https://www.youtube.com/{channel_id}"

    # Step 8: Persist to database
    conn = get_shared_db(db_path)
    cur = conn.cursor()
    new_account_id = None
    try:
        cur.execute(
            """
            INSERT INTO sub_accounts (
                gpm_profile_id, account_type, channel_id, channel_url,
                switch_name, niche, warmup_status, warmup_days, warmup_videos,
                is_active, created_at
            ) VALUES (?, 'brand_account', ?, ?, ?, ?, 'cold', 0, 0, 1, datetime('now'));
            """,
            (profile_id, channel_id or f"brand_{int(time.time())}", channel_url, channel_name, niche),
        )
        new_account_id = cur.lastrowid
        conn.commit()
        log(f"  ✅ Brand Account created & saved: ID #{new_account_id} ('{channel_name}')")
    finally:
        conn.close()

    return {
        "status": "SUCCESS",
        "account_id": new_account_id,
        "channel_name": channel_name,
        "channel_id": channel_id,
        "channel_url": channel_url,
    }


def create_brand_accounts_batch(
    driver: webdriver.Chrome,
    profile_id: str,
    count: int = 5,
    niche: str = "general",
    delay_range: Tuple[int, int] = (300, 900),
    db_path: str = SHARED_DB_PATH,
) -> List[Dict[str, Any]]:
    """
    Create a batch of Brand Accounts on a single profile with safety jitter delays.
    Immediately breaks if phone verification is detected.
    """
    log(f"🏭 Starting Brand Account Factory Batch: {count} accounts for profile '{profile_id}'")
    results = []

    for i in range(count):
        channel_name = generate_channel_name(niche)
        log(f"\n--- Batch item {i + 1}/{count}: Generating '{channel_name}' ---")

        res = create_brand_account(
            driver=driver,
            profile_id=profile_id,
            channel_name=channel_name,
            niche=niche,
            db_path=db_path,
        )
        results.append(res)

        if res.get("status") == "PHONE_VERIFY_REQUIRED":
            log("🛑 CRITICAL: Phone verification demanded! Aborting batch to protect profile.")
            break

        if res.get("status") == "SUCCESS" and i < count - 1:
            wait_sec = random.randint(delay_range[0], delay_range[1])
            log(f"⏳ Jitter cooldown: sleeping {wait_sec}s before next creation...")
            time.sleep(wait_sec)

    return results


# ── Identity Switching ────────────────────────────────────────────

def switch_to_brand_account(driver: webdriver.Chrome, target_name: str) -> bool:
    """
    Switch active YouTube session to the specified brand account name via /channel_switcher.
    Uses multi-selector strategy with JavaScript text matching fallback.
    """
    log(f"  🔄 Switching identity to: '{target_name}'")
    if not safe_get(driver, "https://www.youtube.com/channel_switcher", timeout=30):
        log("  ❌ Could not load channel_switcher page.")
        return False

    time.sleep(random.uniform(3.0, 5.0))

    try:
        # 1. Standard CSS selectors
        selectors = [
            "ytd-account-item-renderer",
            "paper-item",
            "a[href*='/channel/']",
            "a[href*='/@']",
            "#channel-title",
            "yt-formatted-string",
        ]
        matched_elem = None
        for sel in selectors:
            items = driver.find_elements(By.CSS_SELECTOR, sel)
            for it in items:
                txt = it.text.strip()
                if target_name and target_name.lower() in txt.lower():
                    matched_elem = it
                    break
            if matched_elem:
                break

        # 2. Fallback: JavaScript DOM search
        if not matched_elem:
            try:
                matched_elem = driver.execute_script("""
                    const target = arguments[0].toLowerCase();
                    const candidates = document.querySelectorAll('ytd-account-item-renderer, #channel-title, yt-formatted-string, a');
                    for (let el of candidates) {
                        if (el.textContent && el.textContent.toLowerCase().includes(target)) {
                            return el;
                        }
                    }
                    return null;
                """, target_name)
            except Exception:
                pass

        if matched_elem:
            log(f"  🎯 Found match for '{target_name}'. Clicking to switch...")
            try:
                cdp_click(driver, matched_elem)
            except Exception:
                try:
                    matched_elem.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", matched_elem)
            time.sleep(random.uniform(4.0, 6.0))
            return True
        else:
            log(f"  ⚠️ Channel item '{target_name}' not found on switcher page. Proceeding with active profile session.")
            return True
    except Exception as e:
        log(f"  ❌ Error switching account: {e}")
        return False


# ── Warmup & Trust Elevation Engine ───────────────────────────────

def warmup_brand_account_session(
    driver: webdriver.Chrome,
    sub_account_id: int,
    niche: str = "general",
    duration_minutes: int = 15,
    db_path: str = SHARED_DB_PATH,
) -> Dict[str, Any]:
    """
    Conduct an organic warmup session for a Brand Account:
    1. Lock account in DB.
    2. Switch identity to this brand account.
    3. Watch niche-tailored YouTube videos with biological human behaviors.
    4. Increment warmup_videos and recalculate warmup_days.
    5. Check promotion threshold: if warmup_days >= 14 and warmup_videos >= 30 -> promote to 'ready'.
    6. Release lock.
    """
    log(f"🔥 Starting Warmup Session for Sub Account #{sub_account_id} (niche: {niche}, target: {duration_minutes}m)")

    # Step 1: Acquire lock
    if not lock_sub_account(sub_account_id, locked_by="nuoi_kenh", duration_min=duration_minutes + 15, db_path=db_path):
        log(f"  🔒 Sub Account #{sub_account_id} is currently locked by another process.")
        return {"status": "LOCKED", "sub_account_id": sub_account_id}

    conn = get_shared_db(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM sub_accounts WHERE id = ?;", (sub_account_id,))
    account = cur.fetchone()
    conn.close()

    if not account:
        release_sub_account_lock(sub_account_id, locked_by="nuoi_kenh", db_path=db_path)
        log(f"  ❌ Sub Account #{sub_account_id} not found in DB.")
        return {"status": "NOT_FOUND"}

    try:
        # Step 2: Switch identity
        switch_name = account["switch_name"]
        if switch_name:
            switch_to_brand_account(driver, switch_name)

        # Step 3: Pick niche keywords
        niche_key = niche.lower() if niche.lower() in NICHE_TEMPLATES else "general"
        keywords = NICHE_TEMPLATES[niche_key]["keywords"]

        # Run video watching sessions
        start_time = time.time()
        max_duration_sec = duration_minutes * 60
        videos_watched = 0

        while (time.time() - start_time) < max_duration_sec and kiem_tra_ket_noi(driver):
            kw = random.choice(keywords)
            mood = draw_session_mood()
            log(f"  🎬 Warmup viewing: '{kw}' | mood={mood.name}")

            watched = xem_youtube(
                driver=driver,
                tu_khoa=kw,
                so_video=random.randint(1, 2),
                min_giay=MIN_GIAY_XEM,
                max_giay=MAX_GIAY_XEM,
                mood=mood,
            )
            videos_watched += watched

            if watched == 0:
                break
            time.sleep(random.uniform(5.0, 10.0))

        # Step 4: Update stats in DB
        conn = get_shared_db(db_path)
        cur = conn.cursor()

        cur.execute("SELECT warmup_status, warmup_days, warmup_videos, warmup_since FROM sub_accounts WHERE id = ?;", (sub_account_id,))
        current_data = cur.fetchone()

        new_total_videos = (current_data["warmup_videos"] or 0) + videos_watched
        warmup_since = current_data["warmup_since"]

        now_iso = datetime.datetime.utcnow().isoformat()
        if not warmup_since:
            warmup_since = now_iso

        # Calculate active days
        try:
            since_dt = datetime.datetime.fromisoformat(warmup_since)
            days_active = max(0, (datetime.datetime.utcnow() - since_dt).days)
        except Exception:
            days_active = current_data["warmup_days"] or 0

        # Check threshold promotion
        new_status = current_data["warmup_status"]
        ready_since = None

        if days_active >= 14 and new_total_videos >= 30:
            new_status = "ready"
            ready_since = now_iso
            log(f"  🎉 Sub Account #{sub_account_id} PROMOTED to 'ready'! ({days_active} days, {new_total_videos} videos)")
        elif new_status == "cold" and videos_watched > 0:
            new_status = "warming"

        cur.execute(
            """
            UPDATE sub_accounts
            SET warmup_videos = ?,
                warmup_days = ?,
                warmup_status = ?,
                warmup_since = ?,
                ready_since = COALESCE(?, ready_since)
            WHERE id = ?;
            """,
            (new_total_videos, days_active, new_status, warmup_since, ready_since, sub_account_id),
        )
        conn.commit()
        conn.close()

        log(f"  📊 Warmup session finished: +{videos_watched} videos (Total: {new_total_videos}, Status: {new_status})")
        return {
            "status": "COMPLETED",
            "sub_account_id": sub_account_id,
            "videos_watched": videos_watched,
            "total_videos": new_total_videos,
            "warmup_status": new_status,
            "warmup_days": days_active,
        }

    finally:
        # Step 5: Always release lock
        release_sub_account_lock(sub_account_id, locked_by="nuoi_kenh", db_path=db_path)


# ── Status & Listing Helpers ──────────────────────────────────────

def get_brand_accounts_status(
    profile_id: Optional[str] = None,
    db_path: str = SHARED_DB_PATH,
) -> List[Dict[str, Any]]:
    """Return status overview of sub accounts."""
    conn = get_shared_db(db_path)
    cur = conn.cursor()
    if profile_id:
        cur.execute(
            """
            SELECT sa.*, gp.gmail, al.locked_by, al.expires_at AS lock_expires
            FROM sub_accounts sa
            JOIN gpm_profiles gp ON sa.gpm_profile_id = gp.id
            LEFT JOIN account_locks al ON sa.id = al.account_id AND al.expires_at > datetime('now')
            WHERE sa.gpm_profile_id = ?
            ORDER BY sa.id ASC;
            """,
            (profile_id,),
        )
    else:
        cur.execute(
            """
            SELECT sa.*, gp.gmail, al.locked_by, al.expires_at AS lock_expires
            FROM sub_accounts sa
            JOIN gpm_profiles gp ON sa.gpm_profile_id = gp.id
            LEFT JOIN account_locks al ON sa.id = al.account_id AND al.expires_at > datetime('now')
            ORDER BY sa.id ASC;
            """
        )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def verify_sub_yt_profile(profile_id: str) -> Tuple[bool, str]:
    """
    Verify whether the profile name in GPM conforms to mandatory pattern 'sub_yt-x' (x is integer).
    """
    import requests
    try:
        resp = requests.get(f"{GPM_API_URL}/v2/profiles?page=1&per_page=200", timeout=5)
        if resp.status_code != 200:
            return False, f"GPM API returned HTTP {resp.status_code}"
        data = resp.json()
        raw_profiles = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for p in raw_profiles:
            p_id = str(p.get("id") or p.get("profile_id", "")).strip()
            if p_id == profile_id:
                name = str(p.get("name", "")).strip()
                if re.match(REQUIRED_PROFILE_REGEX, name):
                    return True, name
                return False, f"Profile '{profile_id}' has name '{name}', which DOES NOT match 'sub_yt-x'"
        return False, f"Profile ID '{profile_id}' not found in GPM Login"
    except Exception as e:
        return False, f"Could not connect to GPM API: {e}"


# ── CLI Interface ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Brand Account Factory & Warmup Engine")
    parser.add_argument("--profile-id", type=str, help="GPM Profile ID")
    parser.add_argument("--sync", action="store_true", help="Scrape and sync existing Brand Accounts from YouTube")
    parser.add_argument("--create", action="store_true", help="Create new Brand Account(s)")
    parser.add_argument("--count", type=int, default=1, help="Number of accounts to create (default 1)")
    parser.add_argument("--name", type=str, help="Custom name for Brand Account (auto-generated if omitted)")
    parser.add_argument("--niche", type=str, default="general", choices=list(NICHE_TEMPLATES.keys()), help="Target niche")
    parser.add_argument("--warmup", action="store_true", help="Run warmup session on Brand Account")
    parser.add_argument("--account-id", type=int, help="Account ID for warmup")
    parser.add_argument("--duration", type=int, default=15, help="Warmup duration in minutes (default 15)")
    parser.add_argument("--status", action="store_true", help="Display status of accounts in pool")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without starting browser")

    args = parser.parse_args()

    if args.status:
        accounts = get_brand_accounts_status(args.profile_id)
        if not accounts:
            print("\n[!] No accounts found in pool. Pool is currently in STANDBY mode.")
            print("[!] Please create/rename GPM profiles following the pattern 'sub_yt-x' (e.g. sub_yt-1, sub_yt-2).\n")
            return
        print(f"\n{'ID':<5} {'Profile ID':<38} {'Type':<15} {'Name':<25} {'Niche':<10} {'Status':<10} {'Days':<6} {'Videos':<8} {'Locked':<8}")
        print("-" * 130)
        for acc in accounts:
            locked_str = "YES" if acc.get("locked_by") else "NO"
            print(f"{acc['id']:<5} {acc['gpm_profile_id']:<38} {acc['account_type']:<15} {acc.get('switch_name') or '':<25} {acc.get('niche') or '':<10} {acc['warmup_status']:<10} {acc['warmup_days'] or 0:<6} {acc['warmup_videos'] or 0:<8} {locked_str:<8}")
        return

    if not args.profile_id and not args.account_id:
        parser.print_help()
        print("\nError: Please provide --profile-id or --account-id")
        sys.exit(1)

    # Browser operations
    profile_id = args.profile_id

    # Mandatory Constraint Check: profile must conform to 'sub_yt-x'
    if profile_id:
        is_valid, name_or_err = verify_sub_yt_profile(profile_id)
        if not is_valid:
            log(f"🛑 CRITICAL CONSTRAINT: {name_or_err}")
            log("Lưu ý: Dự án hiện tại chỉ sử dụng các profile có tên bắt đầu bằng 'sub_yt-x' (x là số thứ tự).")
            log("Nếu chưa có profile nào phù hợp, hệ thống từ chối mở trình duyệt để bảo toàn tài khoản cá nhân.")
            sys.exit(1)
        log(f"Verified profile '{profile_id}' adheres to 'sub_yt-x' policy (Name: '{name_or_err}').")

    if args.dry_run:
        log(f"[DRY-RUN] Simulating action for profile '{profile_id}'...")
        if args.create:
            name = args.name or generate_channel_name(args.niche)
            log(f"[DRY-RUN] Generated Brand Account Name: '{name}' (niche: {args.niche})")
        return

    # Start GPM Profile
    log(f"Starting GPM Profile '{profile_id}'...")
    driver = mo_profile_gpm(profile_id)
    if not driver:
        log(f"❌ Failed to launch GPM Profile '{profile_id}'")
        sys.exit(1)

    try:
        if args.sync:
            accounts = get_existing_brand_accounts(driver, profile_id, niche=args.niche)
            log(f"Found and synced {len(accounts)} accounts.")

        elif args.create:
            if args.count == 1:
                name = args.name or generate_channel_name(args.niche)
                res = create_brand_account(driver, profile_id, channel_name=name, niche=args.niche)
                log(f"Creation result: {res}")
            else:
                results = create_brand_accounts_batch(driver, profile_id, count=args.count, niche=args.niche)
                log(f"Batch completed: {len(results)} accounts processed.")

        elif args.warmup:
            if not args.account_id:
                log("❌ Please provide --account-id for warmup.")
                sys.exit(1)
            res = warmup_brand_account_session(
                driver=driver,
                sub_account_id=args.account_id,
                niche=args.niche,
                duration_minutes=args.duration,
            )
            log(f"Warmup session result: {res}")

    finally:
        log(f"Closing GPM Profile '{profile_id}'...")
        try:
            driver.quit()
        except Exception:
            pass
        dong_profile_gpm(profile_id)


if __name__ == "__main__":
    main()
