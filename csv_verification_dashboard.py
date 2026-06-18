#!/usr/bin/env python3
"""
CSV Verification Dashboard v4 - Standalone
Aligned directly with CSV_VERIFICATION_RULES.md plus additional
ground-truth reference tables (NRL/AFL/Bathurst/Oscars/ARIA #1 songs/
Australian CPI/known-bad celebrities) verified across multiple sessions.

Keep this file and CSV_VERIFICATION_RULES.md in sync -- this dashboard's
rules block is a structured, checkable restatement of that document.
"""

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from typing import Dict

st.set_page_config(
    page_title="CSV Verification Dashboard v4",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    .stApp { background-color: #000000; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .uploadedFile { background-color: #1F2937 !important; border: 2px dashed #1E3A8A !important; border-radius: 8px !important; padding: 20px !important; }
    .stButton > button { background-color: #1E3A8A; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 500; transition: all 0.2s; }
    .stButton > button:hover { background-color: #2563EB; transform: translateY(-1px); }
    .success-box { background-color: #064E3B; border-left: 4px solid #10B981; padding: 16px; border-radius: 4px; margin: 12px 0; }
    .error-box { background-color: #7F1D1D; border-left: 4px solid #EF4444; padding: 16px; border-radius: 4px; margin: 12px 0; }
    .warning-box { background-color: #78350F; border-left: 4px solid #F59E0B; padding: 16px; border-radius: 4px; margin: 12px 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #000000; }
    .stTabs [data-baseweb="tab"] { background-color: #1F2937; border-radius: 6px 6px 0 0; color: #9CA3AF; padding: 12px 24px; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A; color: #FFFFFF; }
    [data-testid="stMetricValue"] { font-size: 2rem; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GROUND-TRUTH REFERENCE TABLES
# (verified via web search across sessions; supplements CSV_VERIFICATION_RULES.md)
# ============================================================================

NRL_PREMIERS = {
    1936: "Eastern Suburbs", 1937: "South Sydney", 1944: "Balmain Tigers",
    1946: "Balmain Tigers", 1947: "Balmain Tigers", 1956: "St George",
    1960: "St George", 1961: "St George", 1964: "St George", 1965: "St George",
    1966: "St George", 1967: "South Sydney", 1971: "South Sydney",
    1972: "Manly-Warringah", 1976: "Manly-Warringah", 1977: "St George",
    1979: "St George", 1983: "Parramatta", 1986: "Parramatta",
    1989: "Canberra Raiders", 1995: "Canterbury-Bankstown Bulldogs",
    1996: "Manly-Warringah", 1999: "Melbourne Storm", 2005: "Wests Tigers",
    2010: "St George Illawarra Dragons",
}

AFL_PREMIERS = {
    1936: "Collingwood", 1937: "Geelong", 1944: "Fitzroy Football Club",
    1946: "Essendon", 1947: "Carlton", 1956: "Melbourne", 1960: "Melbourne",
    1961: "Hawthorn", 1964: "Melbourne", 1965: "Essendon", 1966: "St Kilda",
    1967: "Richmond", 1971: "Hawthorn", 1972: "Carlton", 1976: "Hawthorn",
    1977: "North Melbourne", 1979: "Carlton", 1983: "Hawthorn",
    1986: "Hawthorn", 1989: "Hawthorn", 1995: "Carlton",
    1996: "North Melbourne", 1999: "North Melbourne", 2005: "Sydney Swans",
    2010: "Collingwood",
}

BATHURST_WINNERS = {
    1961: "Bob Jane and Harry Firth - Mercedes-Benz 220SE (Phillip Island)",
    1963: "Harry Firth / Bob Jane - Ford Cortina GT",
    1964: "Bob Jane and George Reynolds - Ford Cortina GT",
    1965: "Barry Seton and Midge Bosworth - Ford Cortina 500",
    1966: "Rauno Aaltonen and Bob Holden - Morris Cooper S",
    1967: "Harry Firth and Fred Gibson - Ford Falcon GT",
    1971: "Allan Moffat (solo) - Ford Falcon XY GTHO",
    1972: "Peter Brock (solo) - Holden Torana LJ XU-1",
    1976: "Bob Morris and John Fitzpatrick - Holden Torana L34",
    1977: "Allan Moffat and Jacky Ickx - Ford Falcon XC",
    1979: "Peter Brock and Jim Richards - Holden Torana A9X",
    1983: "Peter Brock, Larry Perkins and John Harvey - Holden Commodore VH",
    1986: "Allan Grice and Graeme Bailey - Holden Commodore VK",
    1989: "Dick Johnson and John Bowe - Ford Sierra RS500",
    1995: "Larry Perkins and Russell Ingall - Holden Commodore VR",
    1996: "Craig Lowndes and Greg Murphy - Holden Commodore VR",
    1999: "Greg Murphy and Steven Richards - Holden Commodore VT",
    2005: "Mark Skaife and Todd Kelly - Holden Commodore VZ",
    2008: "Craig Lowndes and Jamie Whincup",
    2010: "Craig Lowndes and Mark Skaife - Holden Commodore VE",
    2011: "Garth Tander and Nick Percat",
    2020: "Shane van Gisbergen and Garth Tander",
}
# Years the race did not exist / was not held (pre-1963, WWII era, etc.)
BATHURST_NOT_HELD = [1936, 1937, 1944, 1946, 1947, 1956, 1960]

OSCAR_WINNERS = {
    # key = birth year = the film year the CSV should reference
    # (ceremony honoring year-Y films is held in year Y+1, but the CSV
    # shows the award FOR films released in the person's birth year)
    1936: ("Paul Muni - Story of Louis Pasteur", "Luise Rainer - The Great Ziegfeld"),
    1937: ("Spencer Tracy - Captains Courageous", "Luise Rainer - The Good Earth"),
    1944: ("Bing Crosby - Going My Way", "Ingrid Bergman - Gaslight"),
    1946: ("Ray Milland - The Lost Weekend", "Joan Crawford - Mildred Pierce"),
    1947: ("Ronald Colman - A Double Life", "Loretta Young - The Farmer's Daughter"),
    1956: ("Yul Brynner - The King and I", "Ingrid Bergman - Anastasia"),
    1960: ("Burt Lancaster - Elmer Gantry", "Elizabeth Taylor - Butterfield 8"),
    1961: ("Maximilian Schell - Judgment at Nuremberg", "Sophia Loren - Two Women"),
    1964: ("Rex Harrison - My Fair Lady", "Julie Andrews - Mary Poppins"),
    1965: ("Lee Marvin - Cat Ballou", "Julie Christie - Darling"),
    1966: ("Paul Scofield - A Man for All Seasons", "Elizabeth Taylor - Who's Afraid of Virginia Woolf?"),
    1969: ("Cliff Robertson - Charly", "Katharine Hepburn - The Lion in Winter"),
    1971: ("Gene Hackman - The French Connection", "Jane Fonda - Klute"),
    1972: ("Marlon Brando - The Godfather", "Liza Minnelli - Cabaret"),
    1976: ("Peter Finch - Network", "Faye Dunaway - Network"),
    1977: ("Richard Dreyfuss - The Goodbye Girl", "Diane Keaton - Annie Hall"),
    1979: ("Dustin Hoffman - Kramer vs. Kramer", "Sally Field - Norma Rae"),
    1983: ("Robert Duvall - Tender Mercies", "Shirley MacLaine - Terms of Endearment"),
    1986: ("Paul Newman - The Color of Money", "Marlee Matlin - Children of a Lesser God"),
    1989: ("Daniel Day-Lewis - My Left Foot", "Jessica Tandy - Driving Miss Daisy"),
    1995: ("Tom Hanks - Forrest Gump", "Jessica Lange - Blue Sky"),
    1996: ("Nicolas Cage - Leaving Las Vegas", "Susan Sarandon - Dead Man Walking"),
    1999: ("Kevin Spacey - American Beauty", "Hilary Swank - Boys Don't Cry"),
    2005: ("Jamie Foxx - Ray", "Hilary Swank - Million Dollar Baby"),
    2010: ("Jeff Bridges - Crazy Heart", "Sandra Bullock - The Blind Side"),
}

# ARIA / Kent Music Report #1 Australian singles verified this session,
# keyed by (year, month, day) of the birthdate the song must cover.
NUMBER_ONE_SONGS_VERIFIED = {
    (1995, 8, 12): "Insensitive - Jann Arden",
    (1996, 7, 7): "Killing Me Softly - Fugees",
    (1999, 10, 31): "Mambo No. 5 - Lou Bega",
    (2005, 11, 10): "Gold Digger - Kanye West featuring Jamie Foxx",
    (2010, 8, 28): "Love the Way You Lie - Eminem featuring Rihanna",
    (1989, 9, 22): "Right Here Waiting - Richard Marx",
    (1986, 9, 18): "Papa Don't Preach - Madonna",
}

# Australian annual CPI inflation rate (RBA/ABS CPI series via
# rateinflation.com), used to sanity check InflationRate per birth year.
AUSTRALIA_INFLATION_RATE = {
    1940: 3.5, 1946: 3.5, 1950: 9.07, 1951: 19.69, 1952: 17.34,
    1956: 5.95, 1957: 2.63, 1959: 1.84, 1960: 3.80, 1961: 2.54,
    1962: -0.18, 1964: 2.47, 1965: 3.79, 1966: 3.14, 1967: 3.25,
    1968: 2.66, 1971: 5.96, 1972: 6.04, 1974: 15.25, 1976: 13.32,
    1977: 12.35, 1979: 9.06, 1983: 10.05, 1986: 9.08, 1989: 7.54,
    1991: 3.22, 1995: 4.63, 1996: 2.61, 1999: 1.47, 2004: 2.33,
    2005: 2.67, 2010: 2.87, 2015: 1.50,
}

# Celebrities confirmed assigned to the WRONG date in past sessions.
# If any of these names appear anywhere in the CSV, verify the row's
# actual date against the correction note.
KNOWN_BAD_CELEBRITY_DATES = {
    "Dana Carvey": "Actual birthday June 2, 1955 (not Mar 13)",
    "Antoine Fuqua": "Actual birthday January 19, 1966 (not Aug 12)",
    "Elisabeth Murdoch": "Actual birthday August 22, 1968 (not Jun 30)",
    "Samuel Beckett": "Actual birthday April 13, 1906 (not Apr 1)",
    "Craig Nicholls": "Actual birthday August 31, 1977 (not Dec 6)",
    "Janko Tipsarević": "Actual birthday June 22, 1984 (not Dec 6)",
    "Vin Diesel": "Actual birthday July 18, 1967 (not Jul 19)",
}

# Zodiac boundaries from CSV_VERIFICATION_RULES.md
ZODIAC_BOUNDARIES = """
Aries: Mar 21-Apr 19 | Taurus: Apr 20-May 20 | Gemini: May 21-Jun 20 |
Cancer: Jun 21-Jul 22 | Leo: Jul 23-Aug 22 | Virgo: Aug 23-Sep 22 |
Libra: Sep 23-Oct 22 | Scorpio: Oct 23-Nov 21 | Sagittarius: Nov 22-Dec 21 |
Capricorn: Dec 22-Jan 19 | Aquarius: Jan 20-Feb 18 | Pisces: Feb 19-Mar 20
(Key boundary to double-check: Jun 20 is Gemini, Jun 21 is Cancer.)
"""

BIRTHSTONES = {
    "January": "Garnet", "February": "Amethyst", "March": "Aquamarine",
    "April": "Diamond", "May": "Emerald", "June": "Pearl", "July": "Ruby",
    "August": "Peridot", "September": "Sapphire", "October": "Opal",
    "November": "Topaz", "December": "Turquoise",
}

REFERENCE_DATA_BLOCK = f"""
═══════════════════════════════════════════════════════
GROUND-TRUTH REFERENCE TABLES (web-search verified, supplements
CSV_VERIFICATION_RULES.md)
═══════════════════════════════════════════════════════

NRL PREMIERS BY YEAR:
{json.dumps(NRL_PREMIERS, indent=2)}

AFL PREMIERS BY YEAR:
{json.dumps(AFL_PREMIERS, indent=2)}

BATHURST 1000 WINNERS BY YEAR:
{json.dumps(BATHURST_WINNERS, indent=2)}

BATHURST YEARS THE RACE WAS NOT HELD (a named winner here is a CRITICAL
ERROR -- the field should instead state the race wasn't held that year):
{json.dumps(BATHURST_NOT_HELD)}

OSCAR WINNERS (Best Actor / Best Actress) BY BIRTH YEAR -- the CSV's
BestActor/BestActress should reflect the award for films released in
the person's birth year (CRITICAL: do not let the ceremony-year offset
confuse this -- use this table directly):
{json.dumps(OSCAR_WINNERS, indent=2)}

ARIA/AUSTRALIA NUMBER-ONE SONGS VERIFIED for these exact
(year, month, day) birthdates -- if a row's date matches one of these
keys, Number1Song MUST equal this value exactly:
{json.dumps({f"{k[0]}-{k[1]:02d}-{k[2]:02d}": v for k, v in NUMBER_ONE_SONGS_VERIFIED.items()}, indent=2)}

AUSTRALIAN ANNUAL CPI INFLATION RATE BY YEAR (RBA/ABS CPI series) --
InflationRate should be within about +/-0.5 percentage points of this
value where the year is listed:
{json.dumps(AUSTRALIA_INFLATION_RATE, indent=2)}

CELEBRITIES CONFIRMED ASSIGNED TO THE WRONG DATE IN PAST SESSIONS:
{json.dumps(KNOWN_BAD_CELEBRITY_DATES, indent=2)}

ZODIAC SIGN BOUNDARIES:
{ZODIAC_BOUNDARIES}

BIRTHSTONES BY MONTH:
{json.dumps(BIRTHSTONES, indent=2)}
"""

# ============================================================================
# VERIFICATION PROMPT -- structured directly from CSV_VERIFICATION_RULES.md
# ============================================================================

VERIFICATION_PROMPT = f"""You are a meticulous fact-checker for The Day Archive's historical
birthday CSV files. Verify EVERY ROW, EVERY COLUMN. "Fact check and
accuracy" means checking every single row and every single field against
real sources -- not a sample, not just NRL/AFL. Never declare a sheet
"100% verified" or "ready for Canva" without having actually checked
every field in every row.

You have two sources of ground truth:
1. The reference tables below (web-search verified across sessions) --
   use these as authoritative for the categories they cover.
2. CSV_VERIFICATION_RULES.md format rules, restated in the passes below.

Do NOT rely on your own training-data memory for NRL/AFL/Bathurst/
Oscars/the specific verified Number1Song dates/the specific inflation
years listed -- check against the tables. For everything else, use your
best knowledge and flag anything you are not confident about as a
warning rather than asserting correctness.

{REFERENCE_DATA_BLOCK}

📋 CSV STRUCTURE:
OrderID, Name, DayOfWeek, MonthName, Day, Year, StarSign, Birthstone,
PrimeMinister, IncomingPM, Monarch, AverageSalary, Celebrity1-3,
NewsEvent1-4, NRLWinner, AFLWinner, BestActor, BestActress, Bathurst1000,
AusOpenWinners, Number1Song, AverageHouse, MilkPrice, BreadPrice,
EggsPrice, WorldPopulation, AustraliaPopulation, HistoricalEventDate1-4,
HistoricalEvent1-4, YearsOfWages, CadburyBarPrice, PetrolPrice,
InflationRate, StampPrice, CinemaPrice, TopBook, TopBookDescription,
TVShow, TVShowDescription, FashionTrend, FashionDescription, Technology,
TechnologyDescription, AustraliaBirths, BirthsDescription, BoyName1-10,
GirlName1-10.

═══════════════════════════════════════════════════════
PASS 1: REFERENCE-TABLE FIELDS (ground truth, not memory)
═══════════════════════════════════════════════════════
For every row: check NRLWinner against NRL_PREMIERS[Year]; AFLWinner
against AFL_PREMIERS[Year]; Bathurst1000 against BATHURST_WINNERS[Year]
(if Year is in BATHURST_NOT_HELD, a named winner is a CRITICAL ERROR --
should say race wasn't held); BestActor/BestActress against
OSCAR_WINNERS[Year]; InflationRate against AUSTRALIA_INFLATION_RATE[Year]
(flag only if listed AND differs by >0.5 points); Number1Song against
NUMBER_ONE_SONGS_VERIFIED for any (Year, MonthName, Day) match.

═══════════════════════════════════════════════════════
PASS 2: DAY OF WEEK, STAR SIGN, BIRTHSTONE
═══════════════════════════════════════════════════════
- DayOfWeek must match the actual calendar day for Day+MonthName+Year.
- StarSign must match the zodiac boundaries above. Double-check the
  Jun 20/21 Gemini-Cancer boundary specifically -- common error point.
- Birthstone must match BIRTHSTONES[MonthName] exactly.

═══════════════════════════════════════════════════════
PASS 3: CELEBRITY VERIFICATION
═══════════════════════════════════════════════════════
For EACH celebrity in Celebrity1-3:
1. Format must be "Name - [2-3 word profession]". Never 1 word. Never
   "born on this day" appended. Never a long career summary.
2. First check: is this name in KNOWN_BAD_CELEBRITY_DATES? If so, verify
   the row's date against the correction and flag as CRITICAL ERROR if
   still wrong.
3. Otherwise verify with your own knowledge whether this person was
   actually born on {{MonthName}} {{Day}}. If not highly confident, flag
   as a warning rather than asserting correctness.

═══════════════════════════════════════════════════════
PASS 4: NEWS EVENTS
═══════════════════════════════════════════════════════
Format: "On [Month] [Day] [Year] [event]" (no commas after day/year --
different from Historical Events).
- Must start with "On [Month] [Day]".
- Maximum 15 words total (date prefix counts).
- One sentence only, specific year required (no generic annual events
  like "Summer Solstice").
- Must NOT duplicate any of the 4 Historical Events in the same row --
  this means must not just be a shorter paraphrase of the same
  underlying fact; a near-identical reworded event is a CRITICAL ERROR.
- Must have actually occurred on that date. Watch known wrong-date traps:
  JFK assassination = Nov 22 1963; Berlin Wall construction = Aug 13
  1961; D-Day = Jun 6 1944; Falklands War END = Jun 14 1982; Beatles
  final concert = Aug 29 1966; Barbarossa = Jun 22 1941; Molotov-
  Ribbentrop Pact = Aug 23 1939; Berlin Blockade START = Jun 24 1948;
  Tiananmen massacre = Jun 4 1989.

═══════════════════════════════════════════════════════
PASS 5: HISTORICAL EVENTS
═══════════════════════════════════════════════════════
Format: "On [Month] [Day], [Year], [event]" -- comma after day AND after
year (different from News Events).
- HistoricalEventDate1-4 must be 4-digit years only.
- Must NOT duplicate any News Event in the same row.
- Verify factual accuracy of the event and date to the best of your
  knowledge; flag anything uncertain.

═══════════════════════════════════════════════════════
PASS 6: CURRENCY
═══════════════════════════════════════════════════════
Check AverageSalary, AverageHouse, MilkPrice, BreadPrice, EggsPrice,
PetrolPrice, StampPrice, CadburyBarPrice, CinemaPrice.
- Must be Australian dollars ($) or cents (c) only. No £, shillings (s),
  pence (d).
- Pre-1966 conversion if British currency appears: £1 -> $2, 1s -> 10c,
  1d -> 1c.

═══════════════════════════════════════════════════════
PASS 7: POPULATION
═══════════════════════════════════════════════════════
- WorldPopulation must contain "Billion" (capital B).
- AustraliaPopulation must contain "million" (lowercase m).

═══════════════════════════════════════════════════════
PASS 8: BABY NAMES
═══════════════════════════════════════════════════════
- Exactly 10 BoyName and 10 GirlName fields populated (BoyName1-10,
  GirlName1-10), no duplicates within a row, no empty fields, names
  plausible for the era.

═══════════════════════════════════════════════════════
PASS 9: CULTURE DESCRIPTION FIELDS
═══════════════════════════════════════════════════════
TopBookDescription, TVShowDescription, FashionDescription,
TechnologyDescription, BirthsDescription:
- 1 sentence only, maximum ~18 words.
- Must end cleanly -- never cut off mid-phrase or end on a filler word
  (the, a, an, and, of, in, to, as, with).
- No ellipses or incomplete thoughts.

═══════════════════════════════════════════════════════
PASS 10: AUS OPEN, PRIME MINISTER, MONARCH
═══════════════════════════════════════════════════════
- AusOpenWinners format "Men: X, Women: Y" -- verify both names against
  your knowledge of Australian Open champions for that year if confident,
  flag if not.
- PrimeMinister and Monarch must be correct for the EXACT date, not just
  the year -- check for mid-year transitions.

═══════════════════════════════════════════════════════
FINAL REPORT FORMAT
═══════════════════════════════════════════════════════
Provide ONLY valid JSON (no markdown, no preambles):

{{
  "summary": {{
    "orders_verified": number,
    "total_data_points": number,
    "critical_errors": number,
    "warnings": number,
    "accuracy_percentage": number
  }},
  "verified_correct": {{
    "nrl_afl_bathurst_oscars": "X/X matched reference tables",
    "number_one_songs": "X/X matched verified table",
    "inflation_rates": "X/X within tolerance",
    "day_of_week_star_sign_birthstone": "X/X correct",
    "celebrity_format_and_dates": "X/X verified or no contradiction found",
    "currency_aud": "X/X in AUD",
    "news_and_historical_events": "X/X verified, 0 duplicates",
    "population_format": "X/X correct",
    "baby_names": "X/X rows with 10+10 unique names",
    "description_fields": "X/X clean 1-sentence ≤18 words",
    "aus_open_pm_monarch": "X/X correct for exact date"
  }},
  "errors": [
    {{
      "order_id": "string",
      "error_type": "nrl|afl|bathurst|oscar|number_one_song|inflation_rate|day_of_week|star_sign|birthstone|celebrity_format|celebrity_birthdate|currency|news_event_format|news_event_date|news_event_duplicate|historical_event_format|historical_event_date|year_format|population_format|baby_names|description_format|aus_open|pm_monarch|other",
      "field": "exact column name",
      "csv_value": "what the CSV currently has",
      "expected_value": "what it should be, citing the reference table/rule",
      "description": "specific issue"
    }}
  ],
  "warnings": [
    {{
      "order_id": "string",
      "field": "exact column name",
      "issue": "description of uncertainty you could not confidently resolve"
    }}
  ],
  "verdict": "READY_FOR_CANVA" or "NEEDS_FIXES",
  "detailed_findings": {{
    "orders": [
      {{
        "order_id": "string",
        "name": "string",
        "birth_date": "string",
        "issues_found": ["list of issues if any, else empty list"]
      }}
    ]
  }}
}}

CRITICAL RULES:
1. For NRL/AFL/Bathurst/Oscars/Number1Song (when in table)/InflationRate
   (when in table)/zodiac boundaries/birthstones: these are ground truth.
   Any CSV mismatch is a CRITICAL ERROR, not a warning.
2. For everything else: if not highly confident, flag as a warning
   rather than asserting correctness either way.
3. Check EVERY row, EVERY field -- spot-checking is not acceptable.
4. Better to flag something uncertain than let an error through silently.
5. Return ONLY the JSON object, nothing else.
"""

# ============================================================================
# VERIFICATION FUNCTION
# ============================================================================

def verify_csv_with_claude(csv_data: str, api_key: str, progress_callback=None) -> Dict:
    """Verify CSV using Claude API against the rules-aligned prompt."""

    if progress_callback:
        progress_callback("🔍 Starting comprehensive verification...")

    full_prompt = f"""{VERIFICATION_PROMPT}

Here is the CSV data to verify:

{csv_data}

Verify this data now, row by row, field by field, and return the JSON report."""

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 16000,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": full_prompt}]
    }

    try:
        if progress_callback:
            progress_callback("📡 Calling Claude API...")

        response = requests.post(url, headers=headers, json=data, timeout=240)

        if response.status_code != 200:
            return {"error": f"API error: {response.status_code} - {response.text[:500]}"}

        result = response.json()
        text_content = result["content"][0]["text"]

        if progress_callback:
            progress_callback("📊 Processing verification results...")

        text_content = text_content.replace("```json", "").replace("```", "").strip()

        start_idx = text_content.find("{")
        end_idx = text_content.rfind("}")
        if start_idx != -1 and end_idx != -1:
            text_content = text_content[start_idx:end_idx + 1]

        verification_results = json.loads(text_content)

        if progress_callback:
            progress_callback("✅ Verification complete!")

        return verification_results

    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": text_content[:2000] if 'text_content' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# MAIN UI
# ============================================================================

def main():
    st.markdown("# 🔍 CSV Verification Dashboard v4")
    st.markdown("**Aligned with `CSV_VERIFICATION_RULES.md` + verified ground-truth reference tables**")
    st.markdown("---")

    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        api_key = st.text_input("Anthropic API Key", type="password", help="Your Anthropic API key for Claude")

        st.markdown("---")
        st.markdown("### 📖 What this checks")
        st.markdown("""
- All 10 rule sections from `CSV_VERIFICATION_RULES.md`
  (day of week, star sign, birthstone, celebrities, news events,
  historical events, currency, population, baby names, descriptions)
- Hardcoded NRL/AFL/Bathurst/Oscar tables (no guessing)
- Verified ARIA #1 songs for specific dates checked this session
- Real Australian CPI inflation rates by year
- Known-bad celebrity list (auto-flags reused errors)
- Distinguishes CRITICAL ERROR (reference-table mismatch) from
  WARNING (uncertain, needs human judgment)
        """)

        st.markdown("---")
        st.markdown("### 🎯 How to Use")
        st.markdown("""
1. Enter your API key above
2. Upload a CSV file
3. Click "Verify CSV"
4. Review results — errors vs warnings are separated
5. Download report
        """)

    if not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to begin")
        return

    st.markdown("## 📤 Upload CSV File")
    uploaded_file = st.file_uploader("Drag and drop your CSV file here", type=['csv'])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            csv_string = df.to_csv(index=False)

            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.info(f"📊 {len(df)} orders • {len(df.columns)} columns • {len(df) * len(df.columns)} data points")

            with st.expander("👀 Preview CSV Data"):
                st.dataframe(df.head(3), use_container_width=True)

            st.markdown("---")

            if st.button("🔍 Verify CSV", type="primary", use_container_width=True):
                progress_text = st.empty()
                progress_bar = st.progress(0)

                def update_progress(message):
                    progress_text.markdown(f"**{message}**")

                progress_bar.progress(10)
                update_progress("🔍 Analyzing CSV structure...")

                progress_bar.progress(30)
                results = verify_csv_with_claude(csv_string, api_key, update_progress)

                progress_bar.progress(100)
                progress_text.empty()
                progress_bar.empty()

                if "error" in results:
                    st.error(f"❌ Verification failed: {results['error']}")
                    if "raw_response" in results:
                        with st.expander("Raw response (for debugging)"):
                            st.text(results["raw_response"])
                else:
                    st.markdown("---")
                    st.markdown("## 📊 Verification Results")

                    summary = results.get("summary", {})
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Orders Verified", summary.get("orders_verified", 0))
                    with col2:
                        st.metric("Data Points", summary.get("total_data_points", 0))
                    with col3:
                        st.metric("Critical Errors", summary.get("critical_errors", 0))
                    with col4:
                        st.metric("Accuracy", f"{summary.get('accuracy_percentage', 0)}%")

                    st.markdown("---")

                    verdict = results.get("verdict", "UNKNOWN")
                    if verdict == "READY_FOR_CANVA":
                        st.markdown('<div class="success-box">✅ <strong>VERDICT: READY FOR CANVA UPLOAD</strong><br>All data verified accurate!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-box">❌ <strong>VERDICT: NEEDS FIXES</strong><br>Errors found that must be corrected before upload.</div>', unsafe_allow_html=True)

                    tab1, tab2, tab3, tab4 = st.tabs(["✅ Verified", "❌ Errors", "⚠️ Warnings", "📋 Full Report"])

                    with tab1:
                        st.markdown("### ✅ Verified Correct")
                        for key, value in results.get("verified_correct", {}).items():
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")

                    with tab2:
                        st.markdown("### ❌ Critical Errors")
                        errors = results.get("errors", [])
                        if errors:
                            for error in errors:
                                st.markdown(f"""
                                <div class="error-box">
                                    <strong>Order {error.get('order_id', 'Unknown')}</strong> — {error.get('error_type', 'Unknown')}<br>
                                    Field: <code>{error.get('field', '?')}</code><br>
                                    CSV has: {error.get('csv_value', '?')}<br>
                                    Should be: {error.get('expected_value', '?')}<br>
                                    {error.get('description', '')}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("🎉 No critical errors found!")

                    with tab3:
                        st.markdown("### ⚠️ Warnings")
                        warnings = results.get("warnings", [])
                        if warnings:
                            for warning in warnings:
                                st.markdown(f"""
                                <div class="warning-box">
                                    <strong>Order {warning.get('order_id', 'Unknown')}</strong> — <code>{warning.get('field', '?')}</code><br>
                                    {warning.get('issue', 'No description')}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("✅ No warnings!")

                    with tab4:
                        st.markdown("### 📋 Full Verification Report")
                        st.json(results)

                    st.markdown("---")
                    report_json = json.dumps(results, indent=2)
                    st.download_button(
                        label="📥 Download Verification Report (JSON)",
                        data=report_json,
                        file_name=f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")


if __name__ == "__main__":
    main()
