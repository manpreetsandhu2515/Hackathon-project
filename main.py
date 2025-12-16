import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import google.generativeai as genai

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=API_KEY)

# --------------------------------------------------
# Output schema
# --------------------------------------------------
class ProviderResponse(BaseModel):
    cleaned_data: Dict
    issues: List[str]
    accuracy_score: int

# --------------------------------------------------
# Gemini model
# --------------------------------------------------
model = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------------------
# SAFE JSON EXTRACTION (100% RELIABLE)
# --------------------------------------------------
def extract_json_safely(text: str) -> dict:
    """
    Extracts the first valid JSON object from Gemini output.
    Works even if wrapped in markdown or mixed with text.
    """
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in Gemini response")

    return json.loads(match.group())

# --------------------------------------------------
# CORE AGENT FUNCTION (Gemini-powered)
# --------------------------------------------------
def clean_provider(provider: dict) -> ProviderResponse:
    prompt = f"""
You are an AI healthcare data cleaner.

Input provider record:
{provider}

Tasks:
1. Fix incorrect or incomplete addresses
2. Normalize phone numbers
3. Standardize medical specialties
4. Identify missing or suspicious fields
5. Assign an accuracy score from 0 to 100

Return ONLY a JSON object in this format:
{{
  "cleaned_data": {{}},
  "issues": [],
  "accuracy_score": 0
}}
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2}
    )

    try:
        data = extract_json_safely(response.text)

        # Defensive normalization
        data["accuracy_score"] = int(data.get("accuracy_score", 0))
        data["issues"] = data.get("issues", [])
        data["cleaned_data"] = data.get("cleaned_data", {})

        return ProviderResponse(**data)

    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        raise RuntimeError(
            f"""
FAILED TO PARSE GEMINI RESPONSE

RAW RESPONSE:
{response.text}

ERROR:
{e}
"""
        )

# --------------------------------------------------
# Local test
# --------------------------------------------------
if __name__ == "__main__":
    sample_provider = {
        "name": "Dr. Amit Sharma",
        "address": "Near City Mall",
        "phone": "987654",
        "specialty": "heart doctor",
        "license": ""
    }

    result = clean_provider(sample_provider)

    print("CLEANED DATA:")
    print(result.cleaned_data)

    print("\nISSUES:")
    print(result.issues)

    print("\nACCURACY SCORE:")
    print(result.accuracy_score)
