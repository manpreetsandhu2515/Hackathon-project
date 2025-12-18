

# **Healthcare Directory Cleaner – AI-Powered Provider Data Verification**

## **Overview**

Healthcare provider directories are a foundational component of modern healthcare systems, enabling patients, insurers, and regulators to connect with medical professionals. However, these directories frequently contain outdated, incomplete, or inconsistent information, leading to poor user experience, operational inefficiencies, and compliance risks.

This project presents an **AI-powered web application** that automatically cleans, validates, and enriches healthcare provider directory data using **Google Gemini** as the core reasoning engine.

The application allows users to upload provider data in CSV format and returns verified, normalized records along with accuracy scores and identified issues.

---

## **Problem Statement**

Healthcare provider directories often suffer from the following issues:

- Incorrect or outdated clinic addresses  
- Invalid or incomplete phone numbers  
- Non-standard medical specialty naming  
- Missing or inconsistent provider credentials  

Manual verification of such data is slow, resource-intensive, and difficult to scale. Despite repeated efforts, errors frequently reappear, resulting in unreliable healthcare data pipelines.

---

## **Solution Description**

This system uses an **AI agent powered by Google Gemini** to automate healthcare provider data verification.

Each provider record is processed by the agent, which performs intelligent reasoning to:

- Normalize and correct provider details  
- Detect missing or suspicious fields  
- Standardize specialties and contact information  
- Assign an accuracy score reflecting data reliability  

The cleaned and enriched data is then presented through a simple web interface.

Gemini acts as the **core intelligence layer**, enabling context-aware decisions that go beyond traditional rule-based validation.

---

## **System Workflow**

1. User uploads a CSV file containing healthcare provider data  
2. Flask backend parses the CSV file  
3. Each provider record is passed to a Gemini-powered AI agent  
4. The agent:
   - Cleans and normalizes the data  
   - Identifies data quality issues  
   - Generates an accuracy score  
5. The verified results are rendered on the web interface  

---

## **Dataset Input Format**

The application accepts CSV files containing healthcare provider information.  
Example format:

```csv
name,address,phone,specialty,license
Dr. Amit Sharma,Near City Mall,987654,heart doctor,
Column names are flexible, as the AI agent handles interpretation and normalization.

Technology Stack

Backend: Python, Flask

AI Model: Google Gemini (gemini-2.5-flash)

Data Processing: Pandas

Validation & Schema Enforcement: Pydantic

Frontend: HTML, CSS

Environment Management: python-dotenv

Project Structure
provider-directory-prototype/
│
├── app.py                  # Flask application entry point
├── agents/
│   ├── __init__.py
│   └── main.py              # Gemini-powered AI agent
│
├── templates/
│   ├── index.html           # Upload interface
│   └── results.html         # Results display
│
├── static/
│   └── style.css            # Frontend styling
│
├── uploads/                 # Uploaded CSV files
├── .env.example             # Environment variable template
├── requirements.txt
└── README.md

Setup Instructions
1. Clone the Repository
git clone <repository-url>
cd provider-directory-prototype

2. Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

3. Install Dependencies
pip install -r requirements.txt

4. Configure Environment Variables

Create a .env file in the project root:

GEMINI_API_KEY=your_gemini_api_key_here


Do not commit your actual API key to version control.

5. Run the Application
python app.py


Open your browser and navigate to:

http://127.0.0.1:5000

API Usage Notes

This project uses the Gemini API free tier. For demonstration purposes, it is recommended to process small CSV files. In a production environment, batching, rate limiting, and asynchronous processing would be implemented to handle large-scale datasets efficiently.

Why Google Gemini

Google Gemini is used as the primary reasoning engine due to its ability to:

Understand unstructured, real-world healthcare data

Perform context-aware validation and normalization

Generate meaningful accuracy scores and issue explanations

This enables a level of intelligence not achievable through static rules alone.

Future Enhancements

Batch processing to reduce API calls

Persistent database storage for verified providers

Export cleaned data in CSV or PDF format

Administrative dashboards for healthcare organizations

Analytics and visualization of data quality trends

Author

Manu
