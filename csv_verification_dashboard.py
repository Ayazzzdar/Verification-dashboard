#!/usr/bin/env python3
"""
CSV Verification Dashboard - Standalone
Completely independent from production dashboard
Uses Anthropic API to verify Day Archive CSV files
"""

import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os

# Page configuration
st.set_page_config(
    page_title="CSV Verification Dashboard",
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
    
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    /* Upload area */
    .uploadedFile {
        background-color: #1F2937 !important;
        border: 2px dashed #1E3A8A !important;
        border-radius: 8px !important;
        padding: 20px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1E3A8A;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #2563EB;
        transform: translateY(-1px);
    }
    
    /* Success/Error boxes */
    .success-box {
        background-color: #064E3B;
        border-left: 4px solid #10B981;
        padding: 16px;
        border-radius: 4px;
        margin: 12px 0;
    }
    
    .error-box {
        background-color: #7F1D1D;
        border-left: 4px solid #EF4444;
        padding: 16px;
        border-radius: 4px;
        margin: 12px 0;
    }
    
    .warning-box {
        background-color: #78350F;
        border-left: 4px solid #F59E0B;
        padding: 16px;
        border-radius: 4px;
        margin: 12px 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #000000;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1F2937;
        border-radius: 6px 6px 0 0;
        color: #9CA3AF;
        padding: 12px 24px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A;
        color: #FFFFFF;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# VERIFICATION PROMPT - COMPREHENSIVE
# ============================================================================

VERIFICATION_PROMPT = """You are a meticulous fact-checker for historical data. Your job is to verify the accuracy of a Day Archive CSV file.

CRITICAL MISSION: Verify EVERY data point with 100% certainty. If you're not absolutely sure about something, FLAG IT.

📋 CSV STRUCTURE:
Each row represents a person's birthday with historical data for that date.

Key fields:
- OrderID, Name, MonthName, Day, Year
- Celebrity1, Celebrity2, Celebrity3 (famous people born on that date)
- StarSign, Birthstone
- NewsEvent1-4 (news events that happened on that date)
- HistoricalEvent1-4 with HistoricalEventDate1-4 (historical events on that date)
- AverageSalary, AverageHouse, MilkPrice, BreadPrice, etc. (prices for that year)

---

🔍 VERIFICATION PROTOCOL - COMPLETE ALL PASSES:

═══════════════════════════════════════════════════════
PASS 1: CELEBRITY BIRTHDATE VERIFICATION
═══════════════════════════════════════════════════════

For EACH celebrity in Celebrity1, Celebrity2, Celebrity3:
1. Extract the person's name (before the " - ")
2. Verify: Was this person ACTUALLY born on {MonthName} {Day}?
3. Check your knowledge carefully
4. If you're NOT 100% certain → FLAG IT

Known celebrity birthdates (verify against these):
- March 21: Matthew Broderick, Gary Oldman, Rosie O'Donnell
- January 1: J.D. Salinger, Verne Troyer
- May 7: Gary Cooper, Eva Perón, Tim Russert
- May 26: John Wayne, Helena Bonham Carter, Lenny Kravitz
- June 2: Stacy Keach, Jerry Mathers, Marvin Hamlisch
- December 15: Don Johnson, Adam Brody, Michelle Dockery
- April 17: Jennifer Garner, Sean Bean, Victoria Beckham
- May 14: George Lucas, Cate Blanchett, Mark Zuckerberg
- June 19: Paula Abdul, Kathleen Turner, Salman Rushdie
- May 24: Bob Dylan, Priscilla Presley

REPORT:
- List each celebrity verified correct
- LIST ANY CELEBRITY whose birthday doesn't match (THIS IS CRITICAL ERROR #1)

═══════════════════════════════════════════════════════
PASS 2: STAR SIGN VERIFICATION
═══════════════════════════════════════════════════════

Verify StarSign matches the birth date (MonthName + Day):
- Aries: March 21-April 19
- Taurus: April 20-May 20
- Gemini: May 21-June 20
- Cancer: June 21-July 22
- Leo: July 23-August 22
- Virgo: August 23-September 22
- Libra: September 23-October 22
- Scorpio: October 23-November 21
- Sagittarius: November 22-December 21
- Capricorn: December 22-January 19
- Aquarius: January 20-February 18
- Pisces: February 19-March 20

REPORT: List any mismatches (CRITICAL ERROR #2)

═══════════════════════════════════════════════════════
PASS 3: AUSTRALIAN CURRENCY VERIFICATION
═══════════════════════════════════════════════════════

Check ALL price fields:
- AverageSalary, AverageHouse, MilkPrice, BreadPrice, EggsPrice
- PetrolPrice, StampPrice, CadburyBarPrice, CinemaPrice

✅ MUST be in Australian dollars ($) or cents (c)
❌ NO British pounds (£), shillings (s), or pence (d)

REPORT: List ANY price with British currency (CRITICAL ERROR #3)

═══════════════════════════════════════════════════════
PASS 4: HISTORICAL EVENTS DATE VERIFICATION
═══════════════════════════════════════════════════════

For EACH HistoricalEvent (1-4):
1. Read the event text
2. Check the HistoricalEventDate{N} field
3. Verify: Did this event ACTUALLY happen on {MonthName} {Day} in that year?
4. If you're NOT 100% certain → FLAG IT

Known CORRECT events (verify these):
- December 15, 1890: Sitting Bull killed
- December 15, 1939: Gone with the Wind premiered
- December 15, 1791: Bill of Rights ratified
- January 1, 1863: Emancipation Proclamation
- January 1, 1901: Commonwealth of Australia formed
- May 7, 1847: AMA founded
- May 7, 1915: Lusitania sunk
- May 7, 1945: Germany surrendered WWII
- May 26, 1865: Edmund Kirby Smith surrender
- May 26, 1897: Dracula published
- May 26, 1927: Last Ford Model T
- May 26, 1940: Dunkirk evacuation began
- April 17, 1961: Bay of Pigs invasion
- April 17, 2007: Virginia Tech shooting

Known WRONG events (REJECT THESE):
❌ Battle of Jutland on May 26 (actually May 31, 1916)
❌ Apollo 10 closest approach on May 26 (actually May 22, 1969)
❌ Phoenix Mars Lander on May 26 (actually May 25, 2008)
❌ Nixon resignation on May 7 (actually August 8, 1974)

Also check:
- Event length: 20-30 words (full sentence)
- Events span different eras

REPORT: List ANY event where the date might be wrong (CRITICAL ERROR #4)

═══════════════════════════════════════════════════════
PASS 5: YEAR FORMAT VERIFICATION
═══════════════════════════════════════════════════════

Check ALL year fields:
- Year (main birth year)
- HistoricalEventDate1, HistoricalEventDate2, HistoricalEventDate3, HistoricalEventDate4

✅ All years MUST be 4 digits (e.g., "1943" NOT "43")

REPORT: List ANY 2-digit years (CRITICAL ERROR #5)

═══════════════════════════════════════════════════════
PASS 6: NEWS EVENTS VERIFICATION
═══════════════════════════════════════════════════════

For NewsEvent1, NewsEvent2, NewsEvent3, NewsEvent4:
- Verify the event happened on {MonthName} {Day}
- Flag if you're uncertain

REPORT: List any news events with questionable dates

═══════════════════════════════════════════════════════
FINAL REPORT FORMAT
═══════════════════════════════════════════════════════

Provide ONLY valid JSON (no markdown, no preambles):

{
  "summary": {
    "orders_verified": number,
    "total_data_points": number,
    "critical_errors": number,
    "warnings": number,
    "accuracy_percentage": number
  },
  "verified_correct": {
    "celebrity_birthdates": "X/X verified",
    "star_signs": "X/X correct",
    "currency_aud": "X/X in AUD",
    "historical_events": "X/X verified",
    "year_formats": "X/X correct"
  },
  "errors": [
    {
      "order_id": "string",
      "error_type": "celebrity_birthdate|star_sign|currency|event_date|year_format",
      "description": "specific issue"
    }
  ],
  "warnings": [
    {
      "order_id": "string",
      "issue": "description of uncertainty"
    }
  ],
  "verdict": "READY_FOR_CANVA" or "NEEDS_FIXES",
  "detailed_findings": {
    "orders": [
      {
        "order_id": "string",
        "name": "string",
        "birth_date": "string",
        "celebrities_verified": ["list of verified celebrities"],
        "events_verified": ["list of verified events"],
        "issues_found": ["list of issues if any"]
      }
    ]
  }
}

CRITICAL RULES:
1. If you're NOT 100% certain about a celebrity's birthdate → FLAG IT
2. If you're NOT 100% certain about an event's date → FLAG IT
3. Check dates against the known facts provided
4. Better to flag something uncertain than let an error through
5. Return ONLY the JSON object, nothing else
"""

# ============================================================================
# VERIFICATION FUNCTION
# ============================================================================

def verify_csv_with_claude(csv_data: str, api_key: str, progress_callback=None) -> Dict:
    """Verify CSV using Claude API"""
    
    if progress_callback:
        progress_callback("🔍 Starting comprehensive verification...")
    
    # Prepare prompt with CSV data
    full_prompt = f"""{VERIFICATION_PROMPT}

Here is the CSV data to verify:

{csv_data}

Verify this data now and return the JSON report."""
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 16000,
        "temperature": 0.1,  # Very low for factual verification
        "messages": [{
            "role": "user",
            "content": full_prompt
        }]
    }
    
    try:
        if progress_callback:
            progress_callback("📡 Calling Claude API...")
        
        response = requests.post(url, headers=headers, json=data, timeout=180)
        
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}"}
        
        result = response.json()
        text_content = result["content"][0]["text"]
        
        if progress_callback:
            progress_callback("📊 Processing verification results...")
        
        # Clean up markdown
        text_content = text_content.replace("```json", "").replace("```", "").strip()
        
        # Find JSON object
        start_idx = text_content.find("{")
        end_idx = text_content.rfind("}")
        
        if start_idx != -1 and end_idx != -1:
            text_content = text_content[start_idx:end_idx+1]
        
        # Parse JSON
        verification_results = json.loads(text_content)
        
        if progress_callback:
            progress_callback("✅ Verification complete!")
        
        return verification_results
        
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# MAIN UI
# ============================================================================

def main():
    # Header
    st.markdown("# 🔍 CSV Verification Dashboard")
    st.markdown("**Standalone verification tool - completely independent from production**")
    st.markdown("---")
    
    # Sidebar - API Key
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Your Anthropic API key for Claude"
        )
        
        st.markdown("---")
        st.markdown("### 📖 About")
        st.markdown("""
This verification dashboard:
- ✅ Verifies celebrity birthdates
- ✅ Checks star signs
- ✅ Validates Australian currency
- ✅ Verifies historical event dates
- ✅ Checks year formats
- ✅ Validates news events
        """)
        
        st.markdown("---")
        st.markdown("### 🎯 How to Use")
        st.markdown("""
1. Enter your API key above
2. Upload a CSV file
3. Click "Verify CSV"
4. Review results
5. Download report
        """)
    
    # Main area
    if not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to begin")
        return
    
    # File upload
    st.markdown("## 📤 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Drag and drop your CSV file here",
        type=['csv'],
        help="Upload a Day Archive CSV file to verify"
    )
    
    if uploaded_file is not None:
        # Read CSV
        try:
            df = pd.read_csv(uploaded_file)
            csv_string = df.to_csv(index=False)
            
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.info(f"📊 {len(df)} orders • {len(df.columns)} columns • {len(df) * len(df.columns)} data points")
            
            # Preview
            with st.expander("👀 Preview CSV Data"):
                st.dataframe(df.head(3), use_container_width=True)
            
            st.markdown("---")
            
            # Verify button
            if st.button("🔍 Verify CSV", type="primary", use_container_width=True):
                # Progress placeholder
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                def update_progress(message):
                    progress_text.markdown(f"**{message}**")
                
                # Run verification
                progress_bar.progress(10)
                update_progress("🔍 Analyzing CSV structure...")
                
                progress_bar.progress(30)
                results = verify_csv_with_claude(csv_string, api_key, update_progress)
                
                progress_bar.progress(100)
                progress_text.empty()
                progress_bar.empty()
                
                # Display results
                if "error" in results:
                    st.error(f"❌ Verification failed: {results['error']}")
                else:
                    st.markdown("---")
                    st.markdown("## 📊 Verification Results")
                    
                    # Summary metrics
                    summary = results.get("summary", {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Orders Verified", summary.get("orders_verified", 0))
                    with col2:
                        st.metric("Data Points", summary.get("total_data_points", 0))
                    with col3:
                        st.metric("Critical Errors", summary.get("critical_errors", 0))
                    with col4:
                        accuracy = summary.get("accuracy_percentage", 0)
                        st.metric("Accuracy", f"{accuracy}%")
                    
                    st.markdown("---")
                    
                    # Verdict
                    verdict = results.get("verdict", "UNKNOWN")
                    if verdict == "READY_FOR_CANVA":
                        st.markdown('<div class="success-box">✅ <strong>VERDICT: READY FOR CANVA UPLOAD</strong><br>All data verified accurate!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-box">❌ <strong>VERDICT: NEEDS FIXES</strong><br>Errors found that must be corrected before upload.</div>', unsafe_allow_html=True)
                    
                    # Tabs for detailed results
                    tab1, tab2, tab3, tab4 = st.tabs(["✅ Verified", "❌ Errors", "⚠️ Warnings", "📋 Full Report"])
                    
                    with tab1:
                        st.markdown("### ✅ Verified Correct")
                        verified = results.get("verified_correct", {})
                        for key, value in verified.items():
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                    
                    with tab2:
                        st.markdown("### ❌ Critical Errors")
                        errors = results.get("errors", [])
                        if errors:
                            for error in errors:
                                st.markdown(f"""
                                <div class="error-box">
                                    <strong>Order {error.get('order_id', 'Unknown')}</strong><br>
                                    Type: {error.get('error_type', 'Unknown')}<br>
                                    {error.get('description', 'No description')}
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
                                    <strong>Order {warning.get('order_id', 'Unknown')}</strong><br>
                                    {warning.get('issue', 'No description')}
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("✅ No warnings!")
                    
                    with tab4:
                        st.markdown("### 📋 Full Verification Report")
                        st.json(results)
                    
                    # Download report
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
