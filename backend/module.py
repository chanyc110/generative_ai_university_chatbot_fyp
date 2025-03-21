from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone
import os
import json


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



# Module information
module_info = {
    'academic_year': '2025',
    'module_code': 'COMP2032',
    'total_credits': 10.00,
    'level': 2,
    'offering_school': 'Computer Science',
    'module_convenor': 'Dr Tissa Chandesa',
    'taught_semesters': 'Spring Malaysia',
    'target_students': 'Available to Level 2 students in the School of Computer Science. Available to inter-campus mobility students and other exchange students in computer science. This module is not available to students not listed above, without explicit approval from the module convenor(s). This module is part of the Artificial Intelligence, Modelling and Optimisation theme in the School of Computer Science. Available to JYA/Erasmus students',
    'summary_of_content': 'Name of Module: Introduction to Image Processing | This module introduces the field of digital image processing, a fundamental component of digital photography, television, computer graphics and computer vision. Topics include: image processing and its applications; fundamentals of digital images; digital image processing theory and practice; and applications of image processing. Approximately three hours are spent in lectures and computer classes each week.',
    'educational_aims': 'To introduce the fundamentals of digital image processing theory and practice. To gain practical experience in writing programs for manipulating digital images. To lay the foundation for studying advanced topics in related fields.',
    'course_structure': [
        {
            'course_component': 'Lecture',
            'number_of_weeks': '12 weeks',
            'number_of_sessions': '1 per week',
            'duration_of_session': '2 hours'
        },
        {
            'course_component': 'Computing',
            'number_of_weeks': '12 weeks',
            'number_of_sessions': '1 per week',
            'duration_of_session': '1 hour'
        }
    ],
    'assessment': [
        {
            'assessment_type': 'Coursework 1',
            'weight': 100.0,
            'requirements': '1) A group coursework consisting of an application creation, supported with a 2000-word report; 2) In-classroom exams'
        }
    ],
    'learning_outcomes': {
        'knowledge_and_understanding': [
            'Experience implementing programs that manipulate images',
            'Understanding fundamental techniques in image processing and analysis, and their limitations',
            'Appreciation of the underlying mathematical principles of the field'
        ],
        'intellectual_skills': [
            'Apply knowledge of image processing techniques to particular tasks',
            'Evaluate different techniques in the context of image manipulation and processing'
        ],
        'professional_skills': [
            'Evaluate the applicability of various algorithms and operators to particular tasks'
        ],
        'transferable_skills': [
            'Address real problems and assess the value of proposed solutions',
            'Retrieve and analyse information from a variety of sources',
            'Produce detailed written reports on results to support the United Nations Sustainable Development Goals (SDGs)'
        ]
    }
}

module_content = f"""
Module Code: {module_info['module_code']}
Module Name: Introduction to Image Processing
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
{json.dumps(module_info['learning_outcomes'], indent=2)}

"""

metadata = {
    "content": module_content,  # ✅ Everything in content
    "source_url": "https://campus.nottingham.ac.uk/psc/csprd_pub/EMPLOYEE/HRMS/c/UN_PROG_AND_MOD_EXTRACT.UN_PLN_EXTRT_FL_CP.GBL?PAGE=UN_CRS_EXT4_FPG&CAMPUS=M&TYPE=Module&YEAR=2025&TITLE=Introduction%20to%20Image%20Processing&MODULE=COMP2032&CRSEID=019457&LINKA=&LINKB=&LINKC=MSC-CS&"
}


embedding = get_embedding(module_content)


# Upsert into Pinecone
index.upsert([(module_info['module_code'], embedding, metadata)], namespace="school_of_CS_modules")

