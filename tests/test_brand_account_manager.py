# -*- coding: utf-8 -*-
"""
test_brand_account_manager.py — Unit Tests for Brand Account Factory & Lifecycle Engine
Tests naming generator, database synchronization, phone verification guardrails,
creation flows, identity switching, and warmup progressive promotion.
"""
import os
import sqlite3
import datetime
import pytest
from unittest.mock import MagicMock, patch

from nuoi_kenh.brand_account_manager import (
    generate_channel_name,
    NICHE_TEMPLATES,
    lock_sub_account,
    release_sub_account_lock,
    sync_discovered_brand_accounts,
    is_phone_verify_demanded,
    create_brand_account,
    create_brand_accounts_batch,
    switch_to_brand_account,
    warmup_brand_account_session,
    get_brand_accounts_status,
)


@pytest.fixture
def mock_db(tmp_path):
    """Create a temporary SQLite database initialized with account_pool schema."""
    db_file = str(tmp_path / "test_account_pool.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE gpm_profiles (
        id              TEXT PRIMARY KEY,
        gmail           TEXT NOT NULL,
        proxy           TEXT,
        is_active       INTEGER DEFAULT 1,
        last_used_at    TEXT,
        notes           TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE sub_accounts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        gpm_profile_id  TEXT NOT NULL,
        account_type    TEXT NOT NULL,  -- 'gmail_root', 'brand_account'
        channel_id      TEXT,
        channel_url     TEXT,
        switch_name     TEXT,
        niche           TEXT DEFAULT 'general',
        warmup_status   TEXT DEFAULT 'cold',  -- 'cold', 'warming', 'ready', 'suspended'
        warmup_days     INTEGER DEFAULT 0,
        warmup_videos   INTEGER DEFAULT 0,
        warmup_since    TEXT,
        ready_since     TEXT,
        total_subs_done INTEGER DEFAULT 0,
        subs_this_month INTEGER DEFAULT 0,
        last_sub_at     TEXT,
        cooldown_until  TEXT,
        is_active       INTEGER DEFAULT 1,
        created_at      TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(gpm_profile_id) REFERENCES gpm_profiles(id)
    );
    """)

    cur.execute("""
    CREATE TABLE account_locks (
        account_id      INTEGER PRIMARY KEY,
        locked_by       TEXT NOT NULL,
        locked_at       TEXT DEFAULT (datetime('now')),
        expires_at      TEXT NOT NULL,
        FOREIGN KEY(account_id) REFERENCES sub_accounts(id)
    );
    """)

    # Seed mock profile
    cur.execute(
        "INSERT INTO gpm_profiles (id, gmail, proxy) VALUES ('prof-test-1', 'test@gmail.local', '127.0.0.1:8080');"
    )

    # Seed master root account
    cur.execute("""
    INSERT INTO sub_accounts (id, gpm_profile_id, account_type, switch_name, warmup_status)
    VALUES (1, 'prof-test-1', 'gmail_root', 'Root Master', 'ready');
    """)

    conn.commit()
    conn.close()
    return db_file


# ── Test 1: Channel Name Generator ────────────────────────────────

def test_generate_channel_name():
    for niche in list(NICHE_TEMPLATES.keys()) + ["unknown_niche"]:
        name = generate_channel_name(niche)
        assert isinstance(name, str)
        assert len(name) > 3
        tokens = name.split()
        assert len(tokens) >= 2, f"Channel name '{name}' should contain at least 2 words"


# ── Test 2: Database Locking & Releasing ──────────────────────────

def test_database_lock_and_release(mock_db):
    # Lock account #1
    ok = lock_sub_account(1, locked_by="nuoi_kenh", duration_min=10, db_path=mock_db)
    assert ok is True

    # Try locking again while active -> should fail
    ok_again = lock_sub_account(1, locked_by="buff_sub", duration_min=10, db_path=mock_db)
    assert ok_again is False

    # Release lock
    released = release_sub_account_lock(1, locked_by="nuoi_kenh", db_path=mock_db)
    assert released is True

    # Re-acquire lock -> should succeed
    reacquired = lock_sub_account(1, locked_by="buff_sub", duration_min=10, db_path=mock_db)
    assert reacquired is True


# ── Test 3: Synchronization of Discovered Brand Accounts ─────────

def test_sync_discovered_brand_accounts(mock_db):
    discovered = [
        {"switch_name": "Tech Channel 1", "channel_id": "@tech1", "channel_url": "https://youtube.com/@tech1"},
        {"switch_name": "Gaming Hub", "channel_id": "@gaminghub", "channel_url": "https://youtube.com/@gaminghub"},
    ]

    inserted = sync_discovered_brand_accounts("prof-test-1", discovered, niche="tech", db_path=mock_db)
    assert inserted == 2

    # Verify rows in DB
    conn = sqlite3.connect(mock_db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM sub_accounts WHERE gpm_profile_id = 'prof-test-1';")
    rows = cur.fetchall()
    assert len(rows) == 3  # 1 root + 2 brand accounts

    # Re-sync same accounts with updated channel_id -> should NOT insert duplicates
    updated_discovery = [
        {"switch_name": "Tech Channel 1", "channel_id": "UC12345678", "channel_url": "https://youtube.com/channel/UC12345678"},
    ]
    re_inserted = sync_discovered_brand_accounts("prof-test-1", updated_discovery, db_path=mock_db)
    assert re_inserted == 0

    cur.execute("SELECT channel_id FROM sub_accounts WHERE switch_name = 'Tech Channel 1';")
    row = cur.fetchone()
    assert row["channel_id"] == "UC12345678"
    conn.close()


# ── Test 4: Phone Verification Detection ──────────────────────────

def test_is_phone_verify_demanded():
    mock_driver = MagicMock()

    # Case 1: Normal YouTube page
    mock_driver.current_url = "https://www.youtube.com/channel_switcher"
    mock_driver.page_source = "<html><body>Select your channel</body></html>"
    mock_driver.find_elements.return_value = []
    assert is_phone_verify_demanded(mock_driver) is False

    # Case 2: URL indicates IDV / Phone verification
    mock_driver.current_url = "https://accounts.google.com/signin/v2/challenge/idvpreregistered"
    assert is_phone_verify_demanded(mock_driver) is True

    # Case 3: Page source contains Vietnamese verify prompt
    mock_driver.current_url = "https://www.youtube.com"
    mock_driver.page_source = "<div>Xác minh tài khoản của bạn để tiếp tục</div>"
    assert is_phone_verify_demanded(mock_driver) is True

    # Case 4: Phone input field displayed
    mock_driver.current_url = "https://www.youtube.com"
    mock_driver.page_source = "<div>Enter details</div>"
    phone_input = MagicMock()
    phone_input.is_displayed.return_value = True
    mock_driver.find_elements.return_value = [phone_input]
    assert is_phone_verify_demanded(mock_driver) is True


# ── Test 5: Brand Account Creation - Phone Verify Abort ────────────

def test_create_brand_account_phone_verify_abort(mock_db):
    mock_driver = MagicMock()
    mock_driver.current_url = "https://accounts.google.com/signin/challenge/idv"
    mock_driver.page_source = "Verify your account"
    mock_driver.find_elements.return_value = []

    res = create_brand_account(
        driver=mock_driver,
        profile_id="prof-test-1",
        channel_name="Risky Brand Account",
        niche="tech",
        db_path=mock_db,
    )

    assert res["status"] == "PHONE_VERIFY_REQUIRED"

    # Confirm no new account was inserted into DB
    conn = sqlite3.connect(mock_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sub_accounts WHERE switch_name = 'Risky Brand Account';")
    assert cur.fetchone()[0] == 0
    conn.close()


# ── Test 6: Brand Account Creation - Successful Creation ──────────

@patch("nuoi_kenh.brand_account_manager.safe_get", return_value=True)
@patch("nuoi_kenh.brand_account_manager.cdp_click")
@patch("nuoi_kenh.brand_account_manager.go_co_loi_chinh_ta")
@patch("nuoi_kenh.brand_account_manager.time.sleep")
def test_create_brand_account_success(mock_sleep, mock_type, mock_click, mock_get, mock_db):
    mock_driver = MagicMock()
    mock_driver.current_url = "https://www.youtube.com/channel/UCnewBrand123"
    mock_driver.page_source = "<html><body>Studio Channel Dashboard</body></html>"

    create_btn = MagicMock()
    create_btn.is_displayed.return_value = True
    name_input = MagicMock()
    name_input.is_displayed.return_value = True
    name_input.is_enabled.return_value = True
    checkbox = MagicMock()
    checkbox.is_displayed.return_value = True
    checkbox.get_attribute.return_value = "false"
    submit_btn = MagicMock()
    submit_btn.is_displayed.return_value = True
    submit_btn.is_enabled.return_value = True

    def find_elements_mock(by, selector):
        if "create_channel" in selector:
            return [create_btn]
        if "channel-name" in selector:
            return [name_input]
        if "checkbox" in selector:
            return [checkbox]
        if "submit" in selector or "create" in selector:
            return [submit_btn]
        return []

    mock_driver.find_elements.side_effect = find_elements_mock

    res = create_brand_account(
        driver=mock_driver,
        profile_id="prof-test-1",
        channel_name="Apex Gaming Lab",
        niche="gaming",
        db_path=mock_db,
    )

    assert res["status"] == "SUCCESS"
    assert res["channel_name"] == "Apex Gaming Lab"
    assert res["channel_id"] == "UCnewBrand123"
    assert res["account_id"] is not None

    # Verify DB state
    conn = sqlite3.connect(mock_db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM sub_accounts WHERE id = ?;", (res["account_id"],))
    account = cur.fetchone()
    assert account["switch_name"] == "Apex Gaming Lab"
    assert account["niche"] == "gaming"
    assert account["warmup_status"] == "cold"
    assert account["warmup_videos"] == 0
    conn.close()


# ── Test 7: Batch Creation with Early Phone Guard Halt ────────────

@patch("nuoi_kenh.brand_account_manager.create_brand_account")
def test_create_brand_accounts_batch_phone_verify_break(mock_create, mock_db):
    mock_driver = MagicMock()

    # 1st succeeds, 2nd hits phone verify
    mock_create.side_effect = [
        {"status": "SUCCESS", "channel_name": "Channel 1", "account_id": 2},
        {"status": "PHONE_VERIFY_REQUIRED", "error": "Phone verify demanded"},
        {"status": "SUCCESS", "channel_name": "Channel 3", "account_id": 3},  # Should never be reached
    ]

    results = create_brand_accounts_batch(
        driver=mock_driver,
        profile_id="prof-test-1",
        count=5,
        niche="lifestyle",
        delay_range=(0, 0),
        db_path=mock_db,
    )

    assert len(results) == 2
    assert results[0]["status"] == "SUCCESS"
    assert results[1]["status"] == "PHONE_VERIFY_REQUIRED"
    assert mock_create.call_count == 2


# ── Test 8: Identity Switching ────────────────────────────────────

@patch("nuoi_kenh.brand_account_manager.safe_get", return_value=True)
@patch("nuoi_kenh.brand_account_manager.cdp_click")
@patch("nuoi_kenh.brand_account_manager.time.sleep")
def test_switch_to_brand_account(mock_sleep, mock_click, mock_get):
    mock_driver = MagicMock()

    item_1 = MagicMock()
    item_1.text = "Root Master\n@rootmaster"
    item_2 = MagicMock()
    item_2.text = "Apex Gaming Lab\n@apexgaming"

    mock_driver.find_elements.return_value = [item_1, item_2]

    # Switch to Apex Gaming Lab
    switched = switch_to_brand_account(mock_driver, "Apex Gaming Lab")
    assert switched is True
    mock_click.assert_called_once_with(mock_driver, item_2)


# ── Test 9: Warmup Progressive Promotion ──────────────────────────

@patch("nuoi_kenh.brand_account_manager.switch_to_brand_account", return_value=True)
@patch("nuoi_kenh.brand_account_manager.xem_youtube", return_value=2)
@patch("nuoi_kenh.brand_account_manager.kiem_tra_ket_noi")
@patch("nuoi_kenh.brand_account_manager.time.sleep")
def test_warmup_brand_account_session_lifecycle(mock_sleep, mock_connect, mock_watch, mock_switch, mock_db):
    mock_connect.side_effect = [True, False]  # Run 1 watch loop then finish
    mock_driver = MagicMock()

    # Seed an account in 'cold' state
    conn = sqlite3.connect(mock_db)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO sub_accounts (id, gpm_profile_id, account_type, switch_name, niche, warmup_status, warmup_days, warmup_videos)
    VALUES (10, 'prof-test-1', 'brand_account', 'Warmup Target', 'tech', 'cold', 0, 0);
    """)
    conn.commit()
    conn.close()

    # Session 1: 2 videos watched -> should transition from 'cold' to 'warming'
    res1 = warmup_brand_account_session(
        driver=mock_driver,
        sub_account_id=10,
        niche="tech",
        duration_minutes=5,
        db_path=mock_db,
    )

    assert res1["status"] == "COMPLETED"
    assert res1["videos_watched"] == 2
    assert res1["total_videos"] == 2
    assert res1["warmup_status"] == "warming"

    # Simulate aging: 15 days active and 28 existing videos
    past_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).isoformat()
    conn = sqlite3.connect(mock_db)
    cur = conn.cursor()
    cur.execute(
        "UPDATE sub_accounts SET warmup_since = ?, warmup_videos = 28 WHERE id = 10;",
        (past_date,),
    )
    conn.commit()
    conn.close()

    # Session 2: 2 videos watched -> 28 + 2 = 30 videos & days >= 14 -> should PROMOTE to 'ready'
    mock_connect.side_effect = [True, False]
    res2 = warmup_brand_account_session(
        driver=mock_driver,
        sub_account_id=10,
        niche="tech",
        duration_minutes=5,
        db_path=mock_db,
    )

    assert res2["status"] == "COMPLETED"
    assert res2["total_videos"] == 30
    assert res2["warmup_status"] == "ready"

    # Verify lock is released
    conn = sqlite3.connect(mock_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM account_locks WHERE account_id = 10;")
    assert cur.fetchone()[0] == 0

    # Verify ready_since is populated
    cur.execute("SELECT ready_since FROM sub_accounts WHERE id = 10;")
    assert cur.fetchone()[0] is not None
    conn.close()


# ── Test 10: Status & Reporting Helper ────────────────────────────

def test_get_brand_accounts_status(mock_db):
    accounts = get_brand_accounts_status(profile_id="prof-test-1", db_path=mock_db)
    assert len(accounts) >= 1
    assert accounts[0]["gpm_profile_id"] == "prof-test-1"
    assert "gmail" in accounts[0]
    assert "lock_expires" in accounts[0]


# ── Test 11: Mandatory Profile Name Pattern Guard (sub_yt-x) ──────

@patch("requests.get")
def test_verify_sub_yt_profile_constraint(mock_get):
    from nuoi_kenh.brand_account_manager import verify_sub_yt_profile

    # Case A: Valid sub_yt-1
    mock_resp_a = MagicMock()
    mock_resp_a.status_code = 200
    mock_resp_a.json.return_value = [
        {"id": "prof-1", "name": "sub_yt-1"},
        {"id": "prof-2", "name": "sub_yt-20"},
        {"id": "prof-3", "name": "ko-jp"},
        {"id": "prof-4", "name": "sub_yt-abc"},
    ]
    mock_get.return_value = mock_resp_a

    ok1, name1 = verify_sub_yt_profile("prof-1")
    assert ok1 is True
    assert name1 == "sub_yt-1"

    ok2, name2 = verify_sub_yt_profile("prof-2")
    assert ok2 is True
    assert name2 == "sub_yt-20"

    # Case B: Non-matching personal profile (ko-jp)
    ok3, err3 = verify_sub_yt_profile("prof-3")
    assert ok3 is False
    assert "DOES NOT match 'sub_yt-x'" in err3

    # Case C: Non-numeric suffix (sub_yt-abc)
    ok4, err4 = verify_sub_yt_profile("prof-4")
    assert ok4 is False
    assert "DOES NOT match 'sub_yt-x'" in err4

    # Case D: Profile ID not in GPM
    ok5, err5 = verify_sub_yt_profile("prof-999")
    assert ok5 is False
    assert "not found in GPM Login" in err5

