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
    

module_urls = [ "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Software%20Engineering&MODULE=COMP1023&CRSEID=019451&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Computer%20Vision&MODULE=COMP3029&CRSEID=019459&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=C++%20Programming&MODULE=COMP2034&CRSEID=019648&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Software%20Quality%20Assurance&MODULE=COMP3033&CRSEID=019650&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Operating%20Systems%20&%20Concurrency&MODULE=COMP2035&CRSEID=020245&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Mathematics%20for%20Computer%20Scientists%201&MODULE=COMP1017&CRSEID=018256&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Machine%20Learning&MODULE=COMP3038&CRSEID=020250&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Computer%20Fundamentals&MODULE=COMP1027&CRSEID=020404&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Programming%20and%20Algorithms&MODULE=COMP1028&CRSEID=020405&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Programming%20Paradigms&MODULE=COMP1029&CRSEID=020407&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Systems%20and%20Architecture&MODULE=COMP1030&CRSEID=020408&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Fundamentals%20of%20Artificial%20Intelligence&MODULE=COMP1032&CRSEID=020410&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Software%20Engineering%20Group%20Project&MODULE=COMP2019&CRSEID=018266&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Computer%20Science%20First%20Year%20Tutorial&MODULE=COMP1033&CRSEID=020458&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                #"https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Artificial%20Intelligence%20Methods&MODULE=COMP2039&CRSEID=023058&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Languages%20and%20Computation&MODULE=COMP2040&CRSEID=023059&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Software%20Specification&MODULE=COMP2041&CRSEID=023060&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Developing%20Maintainable%20Software&MODULE=COMP2042&CRSEID=023061&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Mobile%20Device%20Programming&MODULE=COMP3040&CRSEID=023063&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Individual%20Dissertation%20Single%20Honours&MODULE=COMP3025&CRSEID=018274&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Professional%20Ethics%20in%20Computing&MODULE=COMP3041&CRSEID=023064&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Development%20Experience&MODULE=COMP3043&CRSEID=023075&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Industrial%20Experience&MODULE=COMP3044&CRSEID=023076&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Parallel%20Computing&MODULE=COMP3046&CRSEID=023078&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Schools%20Experience&MODULE=COMP3047&CRSEID=023079&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Autonomous%20Robotic%20Systems&MODULE=COMP4082&CRSEID=032325&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Symbolic%20Artificial%20Intelligence&MODULE=COMP3070&CRSEID=033695&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Designing%20Intelligent%20Agents&MODULE=COMP3071&CRSEID=033696&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Computability%20and%20Computational%20Complexity&MODULE=COMP3072&CRSEID=033697&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Databases%20&%20Interfaces&MODULE=COMP1044&CRSEID=034138&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Mathematics%20for%20Computer%20Scientists%202&MODULE=COMP1045&CRSEID=034139&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Algorithms%20Data%20Structures%20and%20Efficiency&MODULE=COMP2066&CRSEID=035828&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Introduction%20to%20Formal%20Reasoning&MODULE=COMP2067&CRSEID=035829&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Data%20Visualisation&MODULE=COMP3089&CRSEID=036518&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Small-group%20Study%20in%20Computer%20Science&MODULE=COMP3090&CRSEID=036519&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                #"https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Artificial%20Intelligence%20Methods&MODULE=COMP2024&CRSEID=018957&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25",
                "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Human%20Computer%20Interaction&MODULE=COMP2025&CRSEID=019125&LINKA=%25&LINKB=%25&LINKC=%25MSC-CS%25"
                
                
                ]

for url in module_urls:
    module_info = scrape_module_page(url, div_id_mapping)
    module_content = build_module_content(module_info)
    print(module_content)
    upsert_module(module_content, module_info['module_code'], url)


