from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone
import os
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd


# Load environment variables
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("website-chatbot")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model='text-embedding-3-small'
    )
    return response.data[0].embedding

def extract_course_structure(soup, div_id):
    grid_div = soup.find('div', id=div_id)
    if not grid_div:
        return "Not Found"

    # Find the actual grid (scrollable div) where rows are located
    grid_scroll_div = grid_div.find('div', {'class': 'ps_box-grid ps_scrollable sbar sbar_v ps_scrollable_v'})
    if not grid_scroll_div:
        return "No course structure data found"
    
    table = grid_scroll_div.find('table', class_='ps_grid-flex')
    if not table:
        return "No course structure table found"

    course_structure_list = []
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        values = [cell.get_text(strip=True).replace('\xa0', ' ') for cell in cells]
        if values and len(values) >= 4:  # Ensure at least 4 fields
            course_structure_list.append(
                f"Course Component: {values[1]}, Number of Weeks: {values[2]}, "
                f"Number of Sessions: {values[3]}, Duration of Session: {values[4]}"
            )

    if not course_structure_list:
        return "No valid course structure rows found"

    return course_structure_list


def scrape_module_page(url, div_id_mapping):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    module_info = {}
    for key, div_id in div_id_mapping.items():
        if key == "course_structure":
            module_info[key] = extract_course_structure(soup, div_id)
        elif key == "assessment":
            div = soup.find('div', id=div_id)
            if div:
                try:
                    table_html = str(div)
                    df = pd.read_html(table_html)[0]
                    module_info[key] = df.to_dict(orient="records")
                except Exception as e:
                    module_info[key] = "Table parsing failed"
            else:
                module_info[key] = "Not Found"
        else:
            div = soup.find('div', id=div_id)
            module_info[key] = div.get_text(separator=' ', strip=True) if div else "Not Found"
    return module_info

div_id_mapping = {
    "module_name": "UN_PLN_EXT2_WRK_PTS_LIST_TITLE",
    "academic_year": "win0divUN_PLN_EXT2_WRK_$13$",
    "module_code": "win0divUN_PLN_EXT2_WRK_$17$",
    "total_credits": "win0divUN_PLN_EXT2_WRK_$23$",
    "level": "win0divUN_PLN_EXT2_WRK_$28$",
    "offering_school": "win0divUN_PLN_EXT2_WRK_$34$",
    "module_convenor": "win0divUN_PLN_EXT2_WRK_$39$",
    "taught_semesters": "win0divUN_PLN_EXT2_WRK_$44$",
    "target_students": "win0divUN_PLN_EXT2_WRK_$48$",
    "summary_of_content": "win0divUN_PLN_EXT2_WRK_HTMLAREA11",
    "educational_aims": "win0divUN_PLN_EXT2_WRK_HTMLAREA12",
    "course_structure": "win0divUN_PLN_EXT2_WRK_ACA_FREQ",
    "assessment": "win0divUN_CRS_ASAI_TBL$0",
    "learning_outcomes": "win0divUN_PLN_EXT2_WRK_UN_LEARN_OUTCOME"
}


def build_module_content(module_info):
    module_content = f"""
Module Code: {module_info['module_code']}
Module Name: {module_info['module_name']}
Academic Year: {module_info['academic_year']}
Total Credits: {module_info['total_credits']}
Level: {module_info['level']}
Offering School: {module_info['offering_school']}
Module Convenor: {module_info['module_convenor']}
Taught Semesters: {module_info['taught_semesters']}
Target Students: {module_info['target_students']}

Summary of Content:
{module_info['summary_of_content']}

Educational Aims:
{module_info['educational_aims']}

Course Structure:
{json.dumps(module_info['course_structure'], indent=2)}

Assessment:
{json.dumps(module_info['assessment'], indent=2)}

Learning Outcomes:
{module_info['learning_outcomes']}
"""
    return module_content


def upsert_module(module_content, module_code, url):
    embedding = get_embedding(module_content)
    metadata = {
        "content": module_content,
        "source_url": url
    }
    index.upsert([(module_code, embedding, metadata)], namespace="school_of_CS_modules")
    print(f"✅ Upserted module: {module_code}")
    

module_urls = [ "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Computer%20Security&MODULE=COMP3028&CRSEID=018953&LINKA=&LINKB=&LINKC=MSC-CS"
                
                ]

for url in module_urls:
    module_info = scrape_module_page(url, div_id_mapping)
    module_content = build_module_content(module_info)
    print(module_content)
    upsert_module(module_content, module_info['module_code'], url)


