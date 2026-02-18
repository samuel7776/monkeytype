#!/usr/bin/env python3
"""
Fetches popular KJV Bible verses from GitHub (aruljohn/Bible-kjv) and generates
frontend/static/quotes/english.json for Monkeytype.

Downloads full book JSON files (no rate limits), then extracts curated verses locally.
Target: ~200 short (<=100 chars), ~200 medium (101-300 chars), ~200 long (301+ chars)
"""

import json
import re
import urllib.request
import os
import sys

GITHUB_RAW = "https://raw.githubusercontent.com/aruljohn/Bible-kjv/master"

# Map of book names used in our references -> GitHub filenames
BOOK_FILES = {
    "Genesis": "Genesis.json",
    "Exodus": "Exodus.json",
    "Leviticus": "Leviticus.json",
    "Numbers": "Numbers.json",
    "Deuteronomy": "Deuteronomy.json",
    "Joshua": "Joshua.json",
    "Ruth": "Ruth.json",
    "1 Samuel": "1Samuel.json",
    "2 Samuel": "2Samuel.json",
    "1 Chronicles": "1Chronicles.json",
    "2 Chronicles": "2Chronicles.json",
    "Nehemiah": "Nehemiah.json",
    "Job": "Job.json",
    "Psalm": "Psalms.json",
    "Proverbs": "Proverbs.json",
    "Ecclesiastes": "Ecclesiastes.json",
    "Song of Solomon": "SongofSolomon.json",
    "Isaiah": "Isaiah.json",
    "Jeremiah": "Jeremiah.json",
    "Lamentations": "Lamentations.json",
    "Ezekiel": "Ezekiel.json",
    "Daniel": "Daniel.json",
    "Hosea": "Hosea.json",
    "Joel": "Joel.json",
    "Amos": "Amos.json",
    "Micah": "Micah.json",
    "Nahum": "Nahum.json",
    "Habakkuk": "Habakkuk.json",
    "Zephaniah": "Zephaniah.json",
    "Zechariah": "Zechariah.json",
    "Malachi": "Malachi.json",
    "Matthew": "Matthew.json",
    "Mark": "Mark.json",
    "Luke": "Luke.json",
    "John": "John.json",
    "Acts": "Acts.json",
    "Romans": "Romans.json",
    "1 Corinthians": "1Corinthians.json",
    "2 Corinthians": "2Corinthians.json",
    "Galatians": "Galatians.json",
    "Ephesians": "Ephesians.json",
    "Philippians": "Philippians.json",
    "Colossians": "Colossians.json",
    "1 Thessalonians": "1Thessalonians.json",
    "2 Thessalonians": "2Thessalonians.json",
    "1 Timothy": "1Timothy.json",
    "2 Timothy": "2Timothy.json",
    "Titus": "Titus.json",
    "Hebrews": "Hebrews.json",
    "James": "James.json",
    "1 Peter": "1Peter.json",
    "2 Peter": "2Peter.json",
    "1 John": "1John.json",
    "Jude": "Jude.json",
    "Revelation": "Revelation.json",
}

# ============================================================
# Curated verse references organized by category
# Format: "Book Chapter:Verse" or "Book Chapter:Start-End"
# ============================================================

# --- GENESIS (creation, patriarchs, key narratives) ---
GENESIS = [
    "Genesis 1:1", "Genesis 1:2", "Genesis 1:3", "Genesis 1:26", "Genesis 1:27",
    "Genesis 1:28", "Genesis 1:31", "Genesis 2:7", "Genesis 2:18", "Genesis 2:24",
    "Genesis 3:1", "Genesis 3:6", "Genesis 3:15", "Genesis 3:19", "Genesis 5:24",
    "Genesis 6:8", "Genesis 6:9", "Genesis 7:1", "Genesis 8:22", "Genesis 9:13",
    "Genesis 12:1", "Genesis 12:2", "Genesis 12:3", "Genesis 15:1", "Genesis 15:5",
    "Genesis 15:6", "Genesis 17:1", "Genesis 18:14", "Genesis 22:8", "Genesis 22:14",
    "Genesis 28:15", "Genesis 28:16", "Genesis 31:49", "Genesis 50:20",
    # Longer passages
    "Genesis 1:1-5", "Genesis 1:26-28", "Genesis 2:7-9", "Genesis 2:18-24",
    "Genesis 3:1-6", "Genesis 3:14-19", "Genesis 6:5-8", "Genesis 9:12-16",
    "Genesis 12:1-3", "Genesis 15:1-6", "Genesis 22:1-8", "Genesis 28:12-17",
    "Genesis 50:19-21",
]

# --- PSALMS (worship, lament, praise, trust) ---
PSALMS = [
    "Psalm 1:1", "Psalm 1:2", "Psalm 1:3", "Psalm 1:6",
    "Psalm 4:8", "Psalm 5:3", "Psalm 8:1", "Psalm 8:3-4", "Psalm 8:5-6",
    "Psalm 9:1", "Psalm 9:9-10", "Psalm 16:8", "Psalm 16:11",
    "Psalm 18:2", "Psalm 18:30", "Psalm 19:1", "Psalm 19:7", "Psalm 19:14",
    "Psalm 20:7", "Psalm 23:1", "Psalm 23:2-3", "Psalm 23:4", "Psalm 23:5-6",
    "Psalm 24:1", "Psalm 24:3-4", "Psalm 25:4-5", "Psalm 27:1", "Psalm 27:4",
    "Psalm 27:14", "Psalm 28:7", "Psalm 29:2", "Psalm 30:5",
    "Psalm 31:24", "Psalm 32:1", "Psalm 32:8", "Psalm 33:4", "Psalm 33:12",
    "Psalm 34:1", "Psalm 34:4", "Psalm 34:8", "Psalm 34:18",
    "Psalm 37:4", "Psalm 37:5", "Psalm 37:7", "Psalm 37:23-24",
    "Psalm 40:1-3", "Psalm 42:1-2", "Psalm 42:11",
    "Psalm 46:1", "Psalm 46:10", "Psalm 47:1", "Psalm 48:14",
    "Psalm 51:1-2", "Psalm 51:10", "Psalm 51:12", "Psalm 55:22",
    "Psalm 56:3", "Psalm 56:11", "Psalm 57:1", "Psalm 59:16",
    "Psalm 62:1-2", "Psalm 63:1", "Psalm 66:1-2",
    "Psalm 68:5", "Psalm 69:30", "Psalm 71:23",
    "Psalm 73:26", "Psalm 84:10", "Psalm 84:11",
    "Psalm 86:5", "Psalm 86:15", "Psalm 89:1",
    "Psalm 90:2", "Psalm 90:12", "Psalm 91:1-2", "Psalm 91:4", "Psalm 91:11",
    "Psalm 94:19", "Psalm 95:1-2", "Psalm 96:1-3",
    "Psalm 100:1-2", "Psalm 100:3", "Psalm 100:4-5",
    "Psalm 103:1-2", "Psalm 103:8", "Psalm 103:12", "Psalm 103:13",
    "Psalm 104:33", "Psalm 107:1", "Psalm 108:4",
    "Psalm 111:10", "Psalm 112:1", "Psalm 116:1-2",
    "Psalm 118:1", "Psalm 118:6", "Psalm 118:8", "Psalm 118:24",
    "Psalm 119:9-11", "Psalm 119:11", "Psalm 119:105", "Psalm 119:114",
    "Psalm 119:130", "Psalm 119:160",
    "Psalm 121:1-2", "Psalm 121:7-8", "Psalm 122:1",
    "Psalm 126:5", "Psalm 127:1", "Psalm 127:3",
    "Psalm 130:5", "Psalm 133:1", "Psalm 136:1",
    "Psalm 138:8", "Psalm 139:13-14", "Psalm 139:23-24",
    "Psalm 141:3", "Psalm 143:8", "Psalm 143:10",
    "Psalm 144:15", "Psalm 145:3", "Psalm 145:8-9", "Psalm 145:18",
    "Psalm 146:5", "Psalm 147:3", "Psalm 147:5",
    "Psalm 148:1-3", "Psalm 149:1", "Psalm 150:6",
    # Longer psalm passages
    "Psalm 1:1-6", "Psalm 19:1-6", "Psalm 23:1-6", "Psalm 24:1-6",
    "Psalm 27:1-5", "Psalm 46:1-7", "Psalm 51:1-12", "Psalm 91:1-7",
    "Psalm 100:1-5", "Psalm 103:1-5", "Psalm 121:1-8", "Psalm 139:1-6",
    "Psalm 145:1-7", "Psalm 150:1-6",
]

# --- PROVERBS (wisdom, practical living) ---
PROVERBS = [
    "Proverbs 1:7", "Proverbs 2:6", "Proverbs 3:1-2", "Proverbs 3:3-4",
    "Proverbs 3:5-6", "Proverbs 3:7-8", "Proverbs 3:9-10", "Proverbs 3:11-12",
    "Proverbs 3:13-14", "Proverbs 3:19-20", "Proverbs 4:7", "Proverbs 4:23",
    "Proverbs 4:25-27",
    "Proverbs 6:6", "Proverbs 6:16-19",
    "Proverbs 9:10", "Proverbs 10:12", "Proverbs 10:22", "Proverbs 10:27",
    "Proverbs 11:2", "Proverbs 11:14", "Proverbs 11:25", "Proverbs 11:30",
    "Proverbs 12:1", "Proverbs 12:15", "Proverbs 12:25", "Proverbs 13:3",
    "Proverbs 13:12", "Proverbs 13:20", "Proverbs 13:24",
    "Proverbs 14:12", "Proverbs 14:26", "Proverbs 14:29", "Proverbs 14:34",
    "Proverbs 15:1", "Proverbs 15:3", "Proverbs 15:13", "Proverbs 15:22",
    "Proverbs 15:33", "Proverbs 16:3", "Proverbs 16:7", "Proverbs 16:9",
    "Proverbs 16:18", "Proverbs 16:24", "Proverbs 16:32",
    "Proverbs 17:17", "Proverbs 17:22", "Proverbs 18:10", "Proverbs 18:21",
    "Proverbs 18:24", "Proverbs 19:17", "Proverbs 19:21", "Proverbs 20:7",
    "Proverbs 21:2", "Proverbs 21:21", "Proverbs 22:1", "Proverbs 22:6",
    "Proverbs 22:9", "Proverbs 23:7", "Proverbs 24:16", "Proverbs 25:11",
    "Proverbs 25:21-22", "Proverbs 27:1", "Proverbs 27:2", "Proverbs 27:6",
    "Proverbs 27:9", "Proverbs 27:17", "Proverbs 28:1", "Proverbs 28:13",
    "Proverbs 29:11", "Proverbs 29:18", "Proverbs 29:25",
    "Proverbs 30:5", "Proverbs 31:8-9", "Proverbs 31:10", "Proverbs 31:25-26",
    "Proverbs 31:30",
    # Longer proverbs passages
    "Proverbs 1:1-7", "Proverbs 2:1-6", "Proverbs 3:1-8", "Proverbs 3:5-10",
    "Proverbs 4:1-9", "Proverbs 6:6-11", "Proverbs 6:16-19", "Proverbs 31:25-31",
]

# --- WORDS OF JESUS (Gospels - direct speech) ---
WORDS_OF_JESUS = [
    # Matthew
    "Matthew 4:4", "Matthew 4:19", "Matthew 5:3", "Matthew 5:4", "Matthew 5:5",
    "Matthew 5:6", "Matthew 5:7", "Matthew 5:8", "Matthew 5:9",
    "Matthew 5:14", "Matthew 5:16", "Matthew 5:44",
    "Matthew 6:6", "Matthew 6:9-13", "Matthew 6:19-21", "Matthew 6:25-27",
    "Matthew 6:33", "Matthew 6:34",
    "Matthew 7:1", "Matthew 7:7", "Matthew 7:7-8", "Matthew 7:12",
    "Matthew 7:13-14", "Matthew 7:24-27",
    "Matthew 9:12-13", "Matthew 10:28", "Matthew 10:29-31", "Matthew 10:39",
    "Matthew 11:28", "Matthew 11:28-30",
    "Matthew 12:36-37", "Matthew 16:24-26", "Matthew 16:26",
    "Matthew 18:3", "Matthew 18:20", "Matthew 19:14", "Matthew 19:26",
    "Matthew 20:26-28", "Matthew 22:37-40",
    "Matthew 24:35", "Matthew 25:21", "Matthew 25:35-36", "Matthew 25:40",
    "Matthew 28:18-20",
    # Mark
    "Mark 1:15", "Mark 2:17", "Mark 8:34-36", "Mark 8:36",
    "Mark 9:23", "Mark 10:27", "Mark 10:43-45",
    "Mark 11:24", "Mark 11:25", "Mark 12:30-31",
    # Luke
    "Luke 4:18-19", "Luke 6:27-28", "Luke 6:31", "Luke 6:35-36",
    "Luke 6:37", "Luke 6:38", "Luke 9:23", "Luke 9:62",
    "Luke 10:27", "Luke 11:9-10", "Luke 12:15",
    "Luke 12:22-24", "Luke 12:34", "Luke 14:11",
    "Luke 15:7", "Luke 15:10", "Luke 18:16-17",
    "Luke 21:33", "Luke 23:34",
    # John
    "John 3:3", "John 3:16", "John 3:17", "John 4:14",
    "John 5:24", "John 6:35", "John 6:47",
    "John 7:37-38", "John 8:12", "John 8:31-32", "John 8:36",
    "John 10:10", "John 10:11", "John 10:27-28", "John 10:30",
    "John 11:25-26", "John 12:46", "John 13:34-35",
    "John 14:1-3", "John 14:6", "John 14:13-14", "John 14:15",
    "John 14:27", "John 15:5", "John 15:9-11", "John 15:12-13",
    "John 16:33",
    # Longer words of Jesus
    "Matthew 5:3-12", "Matthew 5:43-48", "Matthew 6:9-15", "Matthew 6:25-34",
    "Matthew 7:7-12", "Matthew 7:24-27", "Matthew 25:34-40",
    "Luke 6:27-36", "Luke 12:22-31", "Luke 15:3-7",
    "John 14:1-6", "John 15:1-8", "John 15:9-17",
]

# --- OTHER POPULAR VERSES (rest of Bible) ---
OTHER_POPULAR = [
    # Exodus
    "Exodus 14:14", "Exodus 15:2", "Exodus 20:3", "Exodus 20:12",
    "Exodus 33:14",
    # Leviticus
    "Leviticus 19:18",
    # Numbers
    "Numbers 6:24-26",
    # Deuteronomy
    "Deuteronomy 6:5", "Deuteronomy 7:9", "Deuteronomy 28:6",
    "Deuteronomy 31:6", "Deuteronomy 31:8",
    # Joshua
    "Joshua 1:8", "Joshua 1:9", "Joshua 24:15",
    # Ruth
    "Ruth 1:16",
    # 1 Samuel
    "1 Samuel 16:7",
    # 2 Samuel
    "2 Samuel 22:31",
    # 1 Chronicles
    "1 Chronicles 16:11", "1 Chronicles 16:34",
    # 2 Chronicles
    "2 Chronicles 7:14",
    # Nehemiah
    "Nehemiah 8:10",
    # Job
    "Job 1:21", "Job 19:25", "Job 42:2",
    # Ecclesiastes
    "Ecclesiastes 3:1", "Ecclesiastes 3:11", "Ecclesiastes 4:9-10",
    "Ecclesiastes 7:8-9", "Ecclesiastes 12:13",
    # Song of Solomon
    "Song of Solomon 2:4", "Song of Solomon 8:6-7",
    # Isaiah
    "Isaiah 1:18", "Isaiah 6:8", "Isaiah 9:6",
    "Isaiah 25:8", "Isaiah 26:3", "Isaiah 30:18",
    "Isaiah 35:4", "Isaiah 40:8", "Isaiah 40:28-31",
    "Isaiah 41:10", "Isaiah 41:13", "Isaiah 43:1-2",
    "Isaiah 43:18-19", "Isaiah 44:22", "Isaiah 46:4",
    "Isaiah 49:15-16", "Isaiah 53:4-6", "Isaiah 54:10",
    "Isaiah 54:17", "Isaiah 55:6", "Isaiah 55:8-9",
    "Isaiah 58:11", "Isaiah 61:1-3",
    # Jeremiah
    "Jeremiah 17:7-8", "Jeremiah 29:11", "Jeremiah 29:12-13",
    "Jeremiah 31:3", "Jeremiah 32:17", "Jeremiah 33:3",
    # Lamentations
    "Lamentations 3:22-23", "Lamentations 3:25-26",
    # Ezekiel
    "Ezekiel 36:26",
    # Daniel
    "Daniel 2:20-21", "Daniel 3:17-18",
    # Hosea
    "Hosea 6:6",
    # Joel
    "Joel 2:25", "Joel 2:28",
    # Micah
    "Micah 6:8", "Micah 7:18-19",
    # Nahum
    "Nahum 1:7",
    # Habakkuk
    "Habakkuk 2:3", "Habakkuk 3:17-19",
    # Zephaniah
    "Zephaniah 3:17",
    # Zechariah
    "Zechariah 4:6",
    # Malachi
    "Malachi 3:6", "Malachi 3:10",
    # Acts
    "Acts 1:8", "Acts 2:38", "Acts 4:12", "Acts 17:28", "Acts 20:35",
    # Romans
    "Romans 1:16", "Romans 3:23", "Romans 5:1", "Romans 5:3-5",
    "Romans 5:8", "Romans 6:23", "Romans 8:1", "Romans 8:18",
    "Romans 8:26", "Romans 8:28", "Romans 8:31", "Romans 8:35-37",
    "Romans 8:37-39", "Romans 10:9-10", "Romans 10:17",
    "Romans 12:1-2", "Romans 12:9-12", "Romans 12:12", "Romans 12:21",
    "Romans 13:8", "Romans 15:13",
    # 1 Corinthians
    "1 Corinthians 1:18", "1 Corinthians 2:9", "1 Corinthians 6:19-20",
    "1 Corinthians 9:24", "1 Corinthians 10:13",
    "1 Corinthians 12:27", "1 Corinthians 13:1-3", "1 Corinthians 13:4-7",
    "1 Corinthians 13:13", "1 Corinthians 15:55-57", "1 Corinthians 16:13-14",
    # 2 Corinthians
    "2 Corinthians 1:3-4", "2 Corinthians 3:17", "2 Corinthians 4:16-18",
    "2 Corinthians 5:7", "2 Corinthians 5:17", "2 Corinthians 5:21",
    "2 Corinthians 9:7", "2 Corinthians 12:9", "2 Corinthians 12:10",
    # Galatians
    "Galatians 2:20", "Galatians 5:1", "Galatians 5:22-23",
    "Galatians 6:2", "Galatians 6:7", "Galatians 6:9",
    # Ephesians
    "Ephesians 2:8-9", "Ephesians 2:10", "Ephesians 3:20-21",
    "Ephesians 4:2-3", "Ephesians 4:26-27", "Ephesians 4:29",
    "Ephesians 4:32", "Ephesians 5:25", "Ephesians 6:10-11",
    "Ephesians 6:12", "Ephesians 6:13-17",
    # Philippians
    "Philippians 1:6", "Philippians 1:21", "Philippians 2:3-4",
    "Philippians 2:5-8", "Philippians 2:14-15",
    "Philippians 3:13-14", "Philippians 4:4", "Philippians 4:6-7",
    "Philippians 4:8", "Philippians 4:11-12", "Philippians 4:13",
    "Philippians 4:19",
    # Colossians
    "Colossians 1:16-17", "Colossians 3:2", "Colossians 3:12-14",
    "Colossians 3:15", "Colossians 3:23",
    # 1 Thessalonians
    "1 Thessalonians 5:11", "1 Thessalonians 5:16-18",
    # 2 Thessalonians
    "2 Thessalonians 3:3",
    # 1 Timothy
    "1 Timothy 4:12", "1 Timothy 6:6-8", "1 Timothy 6:10",
    # 2 Timothy
    "2 Timothy 1:7", "2 Timothy 2:15", "2 Timothy 3:16-17", "2 Timothy 4:7",
    # Titus
    "Titus 3:5",
    # Hebrews
    "Hebrews 4:12", "Hebrews 4:15-16", "Hebrews 10:23", "Hebrews 10:24-25",
    "Hebrews 11:1", "Hebrews 11:6", "Hebrews 12:1-2", "Hebrews 12:11",
    "Hebrews 13:5-6", "Hebrews 13:8",
    # James
    "James 1:2-4", "James 1:5", "James 1:12", "James 1:17", "James 1:19-20",
    "James 1:22", "James 2:17", "James 4:7", "James 4:8", "James 4:10",
    "James 5:16",
    # 1 Peter
    "1 Peter 2:9", "1 Peter 3:15", "1 Peter 4:8", "1 Peter 5:6-7",
    "1 Peter 5:8-9",
    # 2 Peter
    "2 Peter 1:3-4", "2 Peter 3:9",
    # 1 John
    "1 John 1:9", "1 John 3:1", "1 John 3:18", "1 John 4:4",
    "1 John 4:7-8", "1 John 4:16", "1 John 4:18-19", "1 John 5:14",
    # Jude
    "Jude 1:24-25",
    # Revelation
    "Revelation 1:8", "Revelation 3:20", "Revelation 21:1-4",
    "Revelation 21:5", "Revelation 22:13",
    # Longer passages
    "Isaiah 40:28-31", "Isaiah 53:1-6", "Isaiah 55:8-11",
    "Romans 8:28-32", "Romans 8:35-39", "Romans 12:1-2", "Romans 12:9-18",
    "1 Corinthians 13:1-8", "1 Corinthians 13:4-13",
    "Ephesians 6:10-18", "Philippians 2:1-11", "Philippians 4:4-9",
    "Colossians 3:12-17", "Hebrews 11:1-6", "Hebrews 12:1-3",
    "James 1:2-8",
]


def parse_reference(ref: str):
    """Parse 'Book Chapter:Verse' or 'Book Chapter:Start-End' into components."""
    # Match: book name (may start with digit), chapter, verse (optionally -end)
    m = re.match(r'^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$', ref)
    if not m:
        return None
    book = m.group(1)
    chapter = int(m.group(2))
    start_verse = int(m.group(3))
    end_verse = int(m.group(4)) if m.group(4) else start_verse
    return book, chapter, start_verse, end_verse


def download_book(book_name: str, cache: dict) -> dict | None:
    """Download a book JSON from GitHub. Caches in memory."""
    if book_name in cache:
        return cache[book_name]

    filename = BOOK_FILES.get(book_name)
    if not filename:
        print(f"  WARNING: No file mapping for book '{book_name}'", file=sys.stderr)
        return None

    url = f"{GITHUB_RAW}/{filename}"
    print(f"  Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "monkeytype-quote-gen/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cache[book_name] = data
        return data
    except Exception as e:
        print(f"  FAILED to download {filename}: {e}", file=sys.stderr)
        return None


def extract_verses(book_data: dict, chapter: int, start_verse: int, end_verse: int) -> str | None:
    """Extract verse text from downloaded book data."""
    for ch in book_data.get("chapters", []):
        if int(ch["chapter"]) == chapter:
            texts = []
            for v in ch.get("verses", []):
                vnum = int(v["verse"])
                if start_verse <= vnum <= end_verse:
                    texts.append(v["text"].strip())
            if texts:
                return " ".join(texts)
            break
    return None


def format_source(book: str, chapter: int, start_verse: int, end_verse: int) -> str:
    """Format a nice source string like 'Psalm 23:1-6'."""
    if start_verse == end_verse:
        return f"{book} {chapter}:{start_verse}"
    return f"{book} {chapter}:{start_verse}-{end_verse}"


def main():
    all_refs = []
    seen = set()

    for category_name, category in [
        ("Genesis", GENESIS),
        ("Psalms", PSALMS),
        ("Proverbs", PROVERBS),
        ("Words of Jesus", WORDS_OF_JESUS),
        ("Other Popular", OTHER_POPULAR),
    ]:
        for ref in category:
            if ref not in seen:
                seen.add(ref)
                all_refs.append(ref)
        print(f"  {category_name}: {len(category)} refs ({len(seen)} unique total)")

    print(f"\nTotal unique references: {len(all_refs)}")

    # Figure out which books we need to download
    books_needed = set()
    for ref in all_refs:
        parsed = parse_reference(ref)
        if parsed:
            books_needed.add(parsed[0])
    print(f"Books to download: {len(books_needed)}\n")

    # Download all needed books
    book_cache = {}
    for book_name in sorted(books_needed):
        download_book(book_name, book_cache)

    print(f"\nDownloaded {len(book_cache)} books. Extracting verses...\n")

    # Extract all verses
    quotes = []
    for ref in all_refs:
        parsed = parse_reference(ref)
        if not parsed:
            print(f"  SKIP (bad format): {ref}", file=sys.stderr)
            continue

        book, chapter, start_v, end_v = parsed
        book_data = book_cache.get(book)
        if not book_data:
            print(f"  SKIP (no book data): {ref}", file=sys.stderr)
            continue

        text = extract_verses(book_data, chapter, start_v, end_v)
        if not text:
            print(f"  SKIP (verses not found): {ref}", file=sys.stderr)
            continue

        source = format_source(book, chapter, start_v, end_v)
        quotes.append({
            "text": text,
            "source": source,
            "length": len(text),
        })

    # Categorize by length
    short = [q for q in quotes if q["length"] <= 100]
    medium = [q for q in quotes if 101 <= q["length"] <= 300]
    long_ = [q for q in quotes if q["length"] > 300]

    print(f"Extracted {len(quotes)} quotes:")
    print(f"  Short  (<=100 chars): {len(short)}")
    print(f"  Medium (101-300 chars): {len(medium)}")
    print(f"  Long   (301-600 chars): {len([q for q in long_ if q['length'] <= 600])}")
    print(f"  Thicc  (601+ chars): {len([q for q in long_ if q['length'] > 600])}")

    # Assign sequential IDs
    for i, q in enumerate(quotes, start=1):
        q["id"] = i

    # Build output in Monkeytype format
    output = {
        "language": "english",
        "groups": [
            [0, 100],
            [101, 300],
            [301, 600],
            [601, 9999]
        ],
        "quotes": quotes
    }

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "static", "quotes", "english.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(quotes)} quotes to {out_path}")


if __name__ == "__main__":
    main()
