import os
import google.generativeai as genai
import json

# IMPORTANT: To use the Gemini AI features, you must set the GEMINI_API_KEY environment variable.
# This key is used to authenticate with the Google Gemini API.
# Example: export GEMINI_API_KEY="YOUR_API_KEY_HERE" (for Linux/macOS)
# or set it in your .env file if your Django setup uses python-dotenv.

# --- Helper function to configure the API ---
def configure_gemini_api():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None, "GEMINI_API_KEY environment variable not found. Please set it to your API key."
    try:
        genai.configure(api_key=api_key)
        # Using 'gemini-pro' model. This can be updated to other compatible models 
        # like 'gemini-1.5-pro-latest' if available and preferred.
        return genai.GenerativeModel('gemini-pro'), None 
    except Exception as e:
        return None, f"Failed to configure Gemini API: {str(e)}"

# --- Service Functions ---

def get_topic_tree(keywords: str):
    """
    Generates a hierarchical topic tree using the Gemini API.
    """
    model, error_msg = configure_gemini_api()
    if error_msg:
        return {"error": error_msg}

    # Prompt designed to ask Gemini for a hierarchical topic tree in a specific JSON format.
    # The JSON structure includes "topic" and "children" keys.
    prompt = f"""
    Generate a hierarchical topic tree for the keywords: "{keywords}".
    The tree should represent a structured breakdown of topics related to the keywords.
    Provide the output as a JSON object with the following structure:
    {{
        "topic": "Main Topic/Keywords",
        "children": [
            {{"topic": "Subtopic 1", "children": [...]}},
            {{"topic": "Subtopic 2", "children": [...]}}
        ]
    }}
    Ensure the output is only the JSON object.
    Example for "Python Programming":
    {{
        "topic": "Python Programming",
        "children": [
            {{"topic": "Fundamentals", "children": [
                {{"topic": "Variables and Data Types", "children": []}},
                {{"topic": "Control Flow", "children": []}}
            ]}},
            {{"topic": "Advanced Topics", "children": [
                {{"topic": "Decorators", "children": []}},
                {{"topic": "Generators", "children": []}}
            ]}}
        ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        # Attempt to extract JSON from the response text.
        # Gemini responses might have ```json ... ``` markdown or just raw JSON.
        raw_text = response.text
        if raw_text.strip().startswith("```json"):
            json_str = raw_text.strip().split("```json")[1].split("```")[0].strip()
        elif raw_text.strip().startswith("```"): # Generic markdown block
             json_str = raw_text.strip().split("```")[1].strip()
        else:
            json_str = raw_text.strip()
        
        parsed_json = json.loads(json_str)
        return parsed_json
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse AI response as JSON: {str(e)}. Response was: {response.text[:200]}..."}
    except Exception as e:
        return {"error": f"Gemini API call failed for topic tree: {str(e)}"}


def generate_slide_outline(topic: str, existing_content: str = None):
    """
    Generates a slide outline using the Gemini API.
    'existing_content' can be used for context if desired.
    """
    model, error_msg = configure_gemini_api()
    if error_msg:
        return {"error": error_msg} # Return error as a dict for consistency in views

    # Prompt designed to ask Gemini for a slide outline in Markdown format.
    # The outline should follow standard presentation structure.
    prompt = f"""
    Generate a Markdown-formatted slide outline for the topic: "{topic}".
    The outline should be suitable for a presentation.
    Start with a Level 1 heading for the topic itself.
    Use Level 2 headings for main sections and bullet points for details.
    
    Example for "Effective Time Management":
    # Effective Time Management

    ## I. Introduction
       - What is time management?
       - Importance in personal and professional life

    ## II. Key Principles
       - Prioritization (Eisenhower Matrix)
       - Goal Setting (SMART goals)
       - Planning

    ## III. Tools & Techniques
       - Calendars and Planners
       - To-Do Lists
       - Time Blocking

    ## IV. Overcoming Procrastination
       - Identifying causes
       - Strategies to overcome

    ## V. Conclusion
       - Recap of key strategies
       - Benefits of mastering time management
    
    Provide only the Markdown outline.
    """
    
    if existing_content: # Optionally add existing content to prompt for context
        prompt += f"\nConsider the following existing content for context (optional):\n{existing_content}"

    try:
        response = model.generate_content(prompt)
        # The response text should be direct Markdown.
        # Split into lines to match the expected list[str] format.
        outline_markdown = response.text.strip()
        return outline_markdown.split('\n')
    except Exception as e:
        return {"error": f"Gemini API call failed for outline generation: {str(e)}"}
