"""
Enrichment script: regenerates a clean index.json and then injects
all manually curated value_descriptions into it.
Run: python src/enrich_index.py
"""
import json
import sys
import os

# ── Step 1: regenerate clean index ──────────────────────────────────────────
from src.index import Indexer
Indexer("data/california_schools/california_schools.sqlite").create_index("index")
print("✓ Clean index.json regenerated")

# ── Step 2: define all manually curated descriptions ────────────────────────
DESCRIPTIONS = {
    "frpm": {
        "CDSCode":
            "Unique identifier combining county (2-digit), district (5-digit), and school "
            "(7-digit) codes. Foreign key to schools.CDSCode",
        "Academic Year":
            "The academic year of the data record, e.g., 2014-2015",
        "County Code":
            "2-digit numeric code identifying the California county",
        "District Code":
            "5-digit numeric code identifying the school district",
        "County Name":
            "Name of the California county. Same as County in schools table and cname in satscores table",
        "District Name":
            "Name of the school district. Same as District in schools table and dname in satscores table",
        "School Name":
            "Name of the school. Same as School in schools table and sname in satscores table",
        "District Type":
            "Category of the school district (e.g., Unified School District, High School District, "
            "County Office of Education)",
        "School Type":
            "Category of the school type (e.g., K-12 Schools, High Schools, Elementary Schools, Charter)",
        "Educational Option Type":
            "Type of educational program offered (e.g., Traditional, Continuation School, "
            "Juvenile Court School, Alternative School of Choice)",
        "NSLP Provision Status":
            "National School Lunch Program provision type (e.g., Provision 1, Provision 2, "
            "Provision 3, CEP - Community Eligibility Provision). Null means no provision",
        "Charter School Number":
            "4-digit number assigned to a charter school.",
        "Charter Funding Type":
            "Charter school funding type. Values: Not in CS (California School) funding model / "
            "Locally funded / Directly funded. Same as FundingType in schools table",
        "Low Grade":
            "Lowest grade offered or served by the school. Values: P (Preschool), K (Kindergarten), 1-12, Adult",
        "High Grade":
            "Highest grade offered or served by the school. Values: K (Kindergarten), 1-12, Adult",
        "Percent (%) Eligible Free (K-12)":
            "Percentage of K-12 students eligible for free meals. "
            "commonsense evidence: eligible free rate = Free Meal Count / Enrollment",
        "Percent (%) Eligible FRPM (K-12)":
            "Percentage of K-12 students eligible for Free or Reduced Price Meals. "
            "commonsense evidence: eligible FRPM rate = FRPM Count / Enrollment",
        "Enrollment (Ages 5-17)":
            "Total enrollment of students aged 5 to 17",
        "Percent (%) Eligible Free (Ages 5-17)":
            "Percentage of students aged 5-17 eligible for free meals. "
            "commonsense evidence: eligible free rate = Free Meal Count / Enrollment",
        "FRPM Count (Ages 5-17)":
            "Number of students aged 5-17 eligible for Free or Reduced Price Meals. "
            "commonsense evidence: eligible FRPM rate = FRPM Count / Enrollment",
        "Percent (%) Eligible FRPM (Ages 5-17)":
            "Percentage of students aged 5-17 eligible for FRPM. "
            "commonsense evidence: eligible FRPM rate = FRPM Count / Enrollment",
        "2013-14 CALPADS Fall 1 Certification Status":
            "Certification status of the school record in CALPADS "
            "(California Longitudinal Pupil Achievement Data System) Fall 1 data collection for 2013-14",
    },
    "satscores": {
        "cds":
            "Unique California Department of Education school identifier. "
            "Same as CDSCode in frpm and schools tables. Foreign key to schools.CDSCode",
        "sname":
            "School name. Same as School Name in frpm table and School in schools table",
        "dname":
            "District name. Same as District Name in frpm table and District in schools table",
        "cname":
            "County name. Same as County Name in frpm table and County in schools table",
        "enroll12":
            "Total K-12 enrollment in the school. commonsense evidence: K-12: 1st grade - 12th grade",
    },
    "schools": {
        "CDSCode":
            "Unique identifier combining county (2-digit), district (5-digit), and school "
            "(7-digit) codes. Primary key. Same as CDSCode in frpm and cds in satscores",
        "NCESDist":
            "7-digit National Center for Educational Statistics (NCES) school district ID. "
            "First 2 digits identify the state, last 5 identify the district",
        "NCESSchool":
            "5-digit NCES school identification number. "
            "Combined with NCESDist forms a unique 12-digit ID for each school",
        "County":
            "Name of the California county. Same as County Name in frpm table and cname in satscores table",
        "District":
            "Name of the school district. Same as District Name in frpm table and dname in satscores table",
        "School":
            "Name of the school. Same as School Name in frpm table and sname in satscores table",
        "Street":
            "Physical street address of the school, district, or administrative authority",
        "City":
            "City of the school, district, or administrative authority",
        "Zip":
            "ZIP code of the school, district, or administrative authority",
        "State":
            "State abbreviation. Typically CA for California schools",
        "Phone":
            "Phone number of the school, district, or administrative authority",
        "OpenDate":
            "The date the school opened",
        "ClosedDate":
            "The date the school closed. Null if the school is still active",
    },
}

# ── Step 3: load, patch, save ────────────────────────────────────────────────
path = "index/index.json"
with open(path, "r", encoding="utf-8") as f:
    index = json.load(f)

patched = 0
for table, cols in DESCRIPTIONS.items():
    for col, desc in cols.items():
        if col in index.get(table, {}).get("sample_values", {}):
            index[table]["sample_values"][col]["value_description"] = desc
            patched += 1
        else:
            print(f"  ⚠ Not found: {table}.{col} — skipping")

with open(path, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=4, ensure_ascii=False)

print(f"✓ {patched} value_descriptions patched into index.json")
