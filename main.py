import os
import json
import re
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from openai import OpenAI
from httpx import HTTPError

# --------------------------------------------------
# ENV SETUP
# --------------------------------------------------
load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in .env file")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.perplexity.ai"
)

# --------------------------------------------------
# RESPONSE SCHEMA
# --------------------------------------------------
class ProviderResponse(BaseModel):
    cleaned_data: Dict
    issues: List[str]
    accuracy_score: int
    enriched_fields: List[str] = []

# --------------------------------------------------
# SIMPLE IN-MEMORY CACHE
# --------------------------------------------------
CACHE = {}
ENRICHMENT_CACHE = {}

# --------------------------------------------------
# SAFE JSON EXTRACTION
# --------------------------------------------------
def extract_json_safely(text: str) -> dict:
    """
    Extract first valid JSON object from model output
    """
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found")
    return json.loads(match.group())

# --------------------------------------------------
# PERPLEXITY CALL WITH RETRY + BACKOFF
# --------------------------------------------------
def call_perplexity_with_retry(prompt: str, model: str = "sonar-pro", retries: int = 3, wait: int = 5):
    last_error = None
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful and accurate assistant."
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Lower temperature for more consistent results
                max_tokens=800,
            )
            return resp
        except HTTPError as e:
            last_error = e
            if attempt == retries - 1:
                raise
            print(f"⚠️ Request failed. Retrying in {wait} seconds...")
            time.sleep(wait)
    raise last_error

# --------------------------------------------------
# ENRICHMENT USING PERPLEXITY AS SEARCH ENGINE
# --------------------------------------------------
def search_with_perplexity(query: str) -> Dict:
    """
    Use Perplexity's online capabilities to search for information
    """
    cache_key = f"search_{hash(query)}"
    if cache_key in ENRICHMENT_CACHE:
        return ENRICHMENT_CACHE[cache_key]
    
    print(f"🔍 Searching for: {query[:50]}...")
    
    search_prompt = f"""
    Search for accurate and current information about: "{query}"
    
    IMPORTANT: You MUST use your internet search capabilities to find REAL, CURRENT information.
    
    Focus on finding:
    1. Contact phone numbers (Indian format: +91 XXXX XXX XXX)
    2. Email addresses
    3. Complete physical addresses
    4. Official website or clinic information
    
    For healthcare providers in India, look for:
    - Clinic/hospital websites
    - Medical directories like Practo, Lybrate, or Justdial
    - Government hospital databases
    - Verified doctor profiles
    
    Return ONLY a JSON object with this structure:
    {{
        "found_info": {{
            "phone": "phone number if found, else empty string",
            "email": "email if found, else empty string", 
            "address": "complete address if found, else empty string",
            "website": "website URL if found, else empty string",
            "verified_source": "name of source where info was found"
        }},
        "confidence": "high/medium/low based on source reliability",
        "search_summary": "brief summary of what was found"
    }}
    
    If you cannot find any information, return empty strings but still provide the JSON structure.
    DO NOT make up information. If not found, leave empty.
    """
    
    try:
        response = call_perplexity_with_retry(search_prompt, model="sonar-pro-online", retries=2)
        text = response.choices[0].message.content
        
        # Extract JSON from response
        data = extract_json_safely(text)
        ENRICHMENT_CACHE[cache_key] = data
        return data
        
    except Exception as e:
        print(f"Search failed: {e}")
        return {
            "found_info": {"phone": "", "email": "", "address": "", "website": "", "verified_source": ""},
            "confidence": "low",
            "search_summary": "Search failed"
        }

def enrich_provider_with_perplexity(provider: Dict) -> Dict:
    """
    Use Perplexity to find missing contact information for a healthcare provider
    """
    name = provider.get('name', '').strip()
    specialty = provider.get('specialty', '').strip()
    city = provider.get('city', '')
    
    if not name:
        return {}
    
    # Try different search strategies
    search_queries = []
    
    # Strategy 1: Name + specialty + city
    if city:
        search_queries.append(f'"{name}" {specialty} doctor contact phone email address {city} India')
        search_queries.append(f'"{name}" clinic hospital {city} contact information')
    
    # Strategy 2: Name + medical directory
    search_queries.append(f'"{name}" doctor Practo profile contact information')
    search_queries.append(f'"{name}" Lybrate doctor profile phone email')
    
    # Strategy 3: Broader search
    search_queries.append(f'"{name}" {specialty} contact details India')
    
    # Strategy 4: If we have partial address
    if provider.get('address'):
        addr = provider['address']
        search_queries.append(f'"{name}" near "{addr}" phone number')
    
    all_found_info = {}
    
    for query in search_queries[:3]:  # Try first 3 queries
        if all(key in all_found_info and all_found_info[key] 
               for key in ['phone', 'email', 'address']):
            break  # Stop if we found all info
            
        result = search_with_perplexity(query)
        found_info = result.get('found_info', {})
        
        # Merge results, prioritizing non-empty values
        for key in ['phone', 'email', 'address', 'website']:
            if found_info.get(key) and not all_found_info.get(key):
                all_found_info[key] = found_info[key]
        
        # Also capture the source
        if found_info.get('verified_source'):
            all_found_info['verified_source'] = found_info['verified_source']
        
        # Small delay between searches
        time.sleep(1)
    
    # Clean and validate the found data
    cleaned_info = {}
    
    # Validate phone (Indian format)
    if 'phone' in all_found_info:
        phone = all_found_info['phone']
        # Extract digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            cleaned_info['phone'] = f"+91 {digits[:5]} {digits[5:]}"
        elif len(digits) > 10:
            cleaned_info['phone'] = f"+{digits}"
    
    # Validate email
    if 'email' in all_found_info:
        email = all_found_info['email'].strip()
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            cleaned_info['email'] = email
    
    # Clean address
    if 'address' in all_found_info:
        address = all_found_info['address'].strip()
        if len(address) > 10:  # Reasonable address length
            cleaned_info['address'] = address
    
    # Add website if found
    if 'website' in all_found_info and all_found_info['website']:
        cleaned_info['website'] = all_found_info['website']
    
    # Add source info
    if 'verified_source' in all_found_info:
        cleaned_info['source'] = all_found_info['verified_source']
    
    print(f"📊 Enrichment results: Found {len(cleaned_info)} fields")
    return cleaned_info

# --------------------------------------------------
# ENHANCED CORE CLEANING AGENT
# --------------------------------------------------
def clean_provider_enhanced(provider: dict) -> ProviderResponse:
    """
    Enhanced version that:
    1. Checks cache
    2. Searches for missing information using Perplexity
    3. Cleans and validates all data
    """
    # ---------- CACHE CHECK ----------
    cache_key = json.dumps(provider, sort_keys=True)
    if cache_key in CACHE:
        cached_result = CACHE[cache_key]
        print(f"Using cached result for {provider.get('name', 'Unknown')}")
        return cached_result
    
    # ---------- ENRICHMENT PHASE ----------
    enriched_data = {}
    enriched_fields = []
    
    # Check what's missing
    original_phone = provider.get('phone', '')
    original_email = provider.get('email', '')
    original_address = provider.get('address', '')
    
    needs_phone = not original_phone or len(str(original_phone).strip()) < 10
    needs_email = not original_email or '@' not in str(original_email)
    needs_address = not original_address or len(str(original_address).strip()) < 15
    
    # Only search if we need something
    if needs_phone or needs_email or needs_address:
        print(f"🔧 Enriching data for: {provider.get('name', 'Unknown')}")
        enriched_data = enrich_provider_with_perplexity(provider)
        
        # Track which fields were enriched
        for field in ['phone', 'email', 'address']:
            if field in enriched_data and field in provider and not provider[field]:
                enriched_fields.append(field)
    
    # Merge data (enriched data only fills gaps, doesn't overwrite existing good data)
    provider_to_clean = provider.copy()
    
    # Only add enriched data if the original field is empty or invalid
    for field, value in enriched_data.items():
        if field in ['phone', 'email', 'address']:
            current_value = provider.get(field, '')
            if not current_value or (field == 'phone' and len(str(current_value)) < 10):
                provider_to_clean[field] = value
    
    # ---------- CLEANING PHASE ----------
    prompt = f"""
Input provider record:
{json.dumps(provider_to_clean, indent=2)}

ENRICHMENT CONTEXT:
- Some fields may have been enhanced with online search: {enriched_fields if enriched_fields else 'None enhanced'}
- Original data had issues: Phone: {'Incomplete' if needs_phone else 'OK'}, Email: {'Missing' if needs_email else 'OK'}, Address: {'Incomplete' if needs_address else 'OK'}

TASKS:
1. VALIDATE & FIX all contact information
   - Phone: Convert to Indian format (+91 XXXXX XXXXX or 0XXXXXXXXXX)
   - Email: Ensure valid format (name@domain.com)
   - Address: Complete with city, state, PIN if possible

2. STANDARDIZE medical specialty
   - 'heart doctor' → 'Cardiology'
   - 'bone doctor' → 'Orthopedics' 
   - 'skin doctor' → 'Dermatology'
   - etc.

3. IDENTIFY issues:
   - Missing required fields
   - Inconsistent information
   - Suspicious or invalid data
   - Note if online data was used

4. SCORE accuracy (0-100):
   - Base score: 50
   - +10 for complete name
   - +15 for valid phone
   - +15 for valid email  
   - +20 for complete address
   - -20 if using unverified online data
   - -30 for major inconsistencies

Return ONLY this JSON (no other text):
{{
  "cleaned_data": {{
    "name": "full name",
    "phone": "formatted phone",
    "email": "valid email",
    "address": "complete address",
    "specialty": "standardized specialty",
    "license": "license if available",
    "source": "note if online data used"
  }},
  "issues": ["list", "of", "issues"],
  "accuracy_score": 75
}}
"""
    
    try:
        response = call_perplexity_with_retry(prompt)
        text = response.choices[0].message.content
        data = extract_json_safely(text)
        
        # Extract the cleaned data
        cleaned_data = data.get("cleaned_data", provider_to_clean)
        issues = data.get("issues", [])
        accuracy = int(data.get("accuracy_score", 50))
        
        # Add enrichment notes to issues
        if enriched_fields:
            issues.append(f"Enhanced with online search: {', '.join(enriched_fields)}")
            if 'source' in enriched_data:
                issues.append(f"Source: {enriched_data.get('source', 'Online directory')}")
        
        # Create result
        result = ProviderResponse(
            cleaned_data=cleaned_data,
            issues=issues,
            accuracy_score=accuracy,
            enriched_fields=enriched_fields
        )
        
        CACHE[cache_key] = result
        return result
        
    # ---------- FALLBACK ----------
    except (HTTPError, json.JSONDecodeError, ValidationError, ValueError) as e:
        print(f"Error in cleaning: {e}")
        
        # Simple fallback cleaning
        cleaned_data = provider_to_clean.copy()
        
        # Basic phone formatting
        if 'phone' in cleaned_data:
            digits = re.sub(r'\D', '', str(cleaned_data['phone']))
            if len(digits) == 10:
                cleaned_data['phone'] = f"+91 {digits[:5]} {digits[5:]}"
        
        # Basic specialty standardization
        specialty_map = {
            'heart': 'Cardiology',
            'bone': 'Orthopedics',
            'skin': 'Dermatology',
            'eye': 'Ophthalmology',
            'child': 'Pediatrics',
            'brain': 'Neurology'
        }
        
        current_specialty = cleaned_data.get('specialty', '').lower()
        for key, value in specialty_map.items():
            if key in current_specialty:
                cleaned_data['specialty'] = value
                break
        
        fallback = ProviderResponse(
            cleaned_data=cleaned_data,
            issues=[f"AI fallback used: {str(e)}"] + 
                   (["Used online data"] if enriched_fields else []),
            accuracy_score=40 if enriched_fields else 30,
            enriched_fields=enriched_fields
        )
        
        CACHE[cache_key] = fallback
        return fallback

# --------------------------------------------------
# LOCAL TEST
# --------------------------------------------------
if __name__ == "__main__":
    print("🧪 Testing Enhanced Healthcare Data Cleaning Agent")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Dr. Amit Sharma",
            "address": "Near City Mall",
            "phone": "987654",
            "specialty": "heart doctor",
            "license": "",
            "city": "Delhi"
        },
        {
            "name": "Dr. Priya Patel",
            "address": "",
            "phone": "",
            "email": "",
            "specialty": "dermatologist",
            "city": "Mumbai"
        },
        {
            "name": "Dr. Rajesh Kumar",
            "address": "MG Road",
            "phone": "9876543210",
            "specialty": "orthopedic surgeon",
            "city": "Bangalore"
        }
    ]
    
    for i, provider in enumerate(test_cases):
        print(f"\n{'='*40}")
        print(f"TEST CASE {i+1}: {provider['name']}")
        print(f"{'='*40}")
        
        result = clean_provider_enhanced(provider)
        
        print("\n✅ CLEANED DATA:")
        for key, value in result.cleaned_data.items():
            print(f"  {key:15}: {value}")
        
        print("\n⚠️  ISSUES:")
        for issue in result.issues:
            print(f"  • {issue}")
        
        print(f"\n📊 ACCURACY SCORE: {result.accuracy_score}/100")
        if result.enriched_fields:
            print(f"🔄 ENRICHED FIELDS: {', '.join(result.enriched_fields)}")
        
        print(f"\n⏱️  Cache size: {len(CACHE)} items")
        
        # Small delay between tests
        if i < len(test_cases) - 1:
            time.sleep(2)
    
    print(f"\n{'='*60}")
    print("✨ All tests completed!")
    print(f"Total cache entries: {len(CACHE)}")
    print(f"Enrichment cache entries: {len(ENRICHMENT_CACHE)}")