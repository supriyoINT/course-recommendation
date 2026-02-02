import os
import json
import re
from config import Config
from openai import OpenAI

from db import get_db
from psycopg2.extras import RealDictCursor

from services.user_service import get_profile

def _clean_and_parse_json(content):
    """
    Clean and parse JSON response from OpenAI API.
    Handles markdown code fences, unescaped newlines, and trailing commas.
    """
    # Sometimes the model returns code fences; strip them if present
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if m:
        content = m.group(1).strip()
    elif content.startswith("```"):
        # If only opening fence, try to extract until end
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"```\s*$", "", content)

    # Clean up common JSON issues: unescaped newlines, leading/trailing whitespace
    content = content.strip()
    # Replace literal newlines inside the JSON with spaces
    content = content.replace("\n", " ")
    content = content.replace("\r", " ")

    # Try to parse JSON output
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError as parse_err:
        # If basic parsing fails, try to fix common issues
        print(f"Failed to parse JSON from model response: {parse_err}")
        print(f"Response preview: {content[:500]}...")
        
        # Try one more time with more aggressive cleanup
        try:
            # Remove any trailing commas before closing braces/brackets
            content = re.sub(r",\s*([}\]])", r"\1", content)
            data = json.loads(content)
            return data
        except Exception:
            return {
                "error": "failed_to_parse_model_output",
                "details": str(parse_err),
                "raw": content[:1000]  # Limit raw output size
            }

def get_recommendation(user_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    profile = get_profile(user_id)
    prompt_template = """
        You are an expert course recommendation engine.

        Your job is to recommend REAL online courses available on the internet
        (Coursera, Udemy, edX, LinkedIn Learning, freeCodeCamp, Google Career Certificates,
        AWS Training, Microsoft Learn, IBM SkillsBuild, Skillshare, etc).

        INPUT:
        User Profile:
        - User Type: {user_type}
        - Goal: {goal}
        - Interest Area: {interest_area}
        - Experience Level: {experience_level}
        - Background: {background}
        - Current Skills: {current_skills}
        - Learning Purpose: {learning_purpose}
        - Preferred Learning Style: {preferred_learning_style}
        - Preferred Platforms: {preferred_platforms}
        - Budget: {budget}
        - Time Available Per Week: {time_available_per_week}
        - Timeline: {timeline}

        TASK:
        1. Understand the user's background, interests, and goals.
        2. Recommend 5–10 REAL, relevant courses from well-known platforms.
        3. Include ONLY real courses — verify that each course exists.
        4. Each recommended course must include:
        - Course Name
        - Platform
        - Rating (if available)
        - Official URL
        - Why this course fits the user profile

        OUTPUT FORMAT (JSON):
        {{
            "courses": [
                {{
                    "course_name": "",
                    "platform": "",
                    "url": "",
                    "rating": "",
                    "why_recommended": ""
                }}
            ]
        }}

        Constraints:
        - Avoid duplicate courses.
        - Be specific and job-oriented.
        - Recommendations must match the user's goals, experience, and timeline.
        - If the budget is "0" or "low", prefer free/low-cost courses.
        """

    prompt = prompt_template.format(
        user_type=profile["user_type"],
        goal=profile["goal"],
        interest_area=profile["interest_area"],
        experience_level=profile["experience_level"],
        background=profile["background"],
        current_skills=profile["current_skills"],
        learning_purpose=profile["learning_purpose"],
        preferred_learning_style=profile["preferred_learning_style"],
        preferred_platforms=profile["preferred_platforms"],
        budget=profile["budget"],
        time_available_per_week=profile["time_available_per_week"],
        timeline=profile["timeline"]
    )


    # Use OpenAI to get recommendations. Requires OPENAI_API_KEY in env.
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print("OPENAI_API_KEY not set - returning mock response")
        return {
            "error": "OPENAI_API_KEY not set",
            "mock": True
        }

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that returns only valid JSON in the format described to the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )


        # The new OpenAI client returns an object with attributes, not a subscriptable dict.
        # Try attribute access first, then fall back to dict conversion.
        content = None
        try:
            content = resp.choices[0].message.content
        except Exception:
            try:
                resp_dict = resp.to_dict()
                content = resp_dict["choices"][0]["message"]["content"]
            except Exception:
                # Fallback: stringify the whole response for debugging
                content = str(resp)

        # Use helper to clean and parse JSON
        data = _clean_and_parse_json(content)
        return data

    except Exception as e:
        print("OpenAI request failed:", e)
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

def get_topics_based_on_user(user_id):    

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    profile = get_profile(user_id)
    prompt_template = """You are an AI learning assistant. 
        Analyze the following user profile and identify the most relevant topics for quiz questions. 

        User Profile:
        INPUT:
            User Profile:
            - User Type: {user_type}
            - Goal: {goal}
            - Interest Area: {interest_area}
            - Experience Level: {experience_level}
            - Background: {background}
            - Current Skills: {current_skills}
            - Learning Purpose: {learning_purpose}
            - Preferred Learning Style: {preferred_learning_style}
            - Preferred Platforms: {preferred_platforms}
            - Budget: {budget}
            - Time Available Per Week: {time_available_per_week}
            - Timeline: {timeline}

        Instructions:
        1. Identify 5–7 relevant topics the user should practice.
        2. Only return the topic names as a JSON array.
        3. Do NOT include explanations, difficulty, or any extra text.
        4. Example format:
        ["Topic 1", "Topic 2", "Topic 3"]"""
    
    prompt = prompt_template.format(
        user_type=profile["user_type"],
        goal=profile["goal"],
        interest_area=profile["interest_area"],
        experience_level=profile["experience_level"],
        background=profile["background"],
        current_skills=profile["current_skills"],
        learning_purpose=profile["learning_purpose"],
        preferred_learning_style=profile["preferred_learning_style"],
        preferred_platforms=profile["preferred_platforms"],
        budget=profile["budget"],
        time_available_per_week=profile["time_available_per_week"],
        timeline=profile["timeline"]
    )

    print(prompt)

    # Use OpenAI to get recommendations. Requires OPENAI_API_KEY in env.
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print("OPENAI_API_KEY not set - returning mock response")
        return {
            "error": "OPENAI_API_KEY not set",
            "mock": True
        }

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that returns only valid JSON in the format described to the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )


        # The new OpenAI client returns an object with attributes, not a subscriptable dict.
        # Try attribute access first, then fall back to dict conversion.
        content = None
        try:
            content = resp.choices[0].message.content
        except Exception:
            try:
                resp_dict = resp.to_dict()
                content = resp_dict["choices"][0]["message"]["content"]
            except Exception:
                # Fallback: stringify the whole response for debugging
                content = str(resp)

        # Use helper to clean and parse JSON
        data = _clean_and_parse_json(content)
        return data

    except Exception as e:
        print("OpenAI request failed:", e)
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()
        
def get_all_questions(topic_list):
    prompt_template = """You are an AI learning assistant. 
        Generate quiz questions for the following topics: {topics}

        Instructions:
        1. For each topic, generate 3 multiple-choice questions.
        2. Each question should have 4 options (A, B, C, D).
        3. Return the output as a JSON object with topics as keys and arrays of questions as values.
        4. EXPECTED OUTPUT FORMAT (JSON)::
        {{
            "Topic 1": [
                {{
                    "question": "Question text",
                    "options": {{
                        "A": "Option A",
                        "B": "Option B",
                        "C": "Option C",
                        "D": "Option D"
                    }},
                }}
            ],
            "Topic 2": [ ... ]
        }}"""
    
    prompt = prompt_template.format(
        topics=", ".join(topic_list)
    )

    print(prompt)

    # Use OpenAI to get recommendations. Requires OPENAI_API_KEY in env.
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print("OPENAI_API_KEY not set - returning mock response")
        return {
            "error": "OPENAI_API_KEY not set",
            "mock": True
        }

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that returns only valid JSON in the format described to the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )


        # The new OpenAI client returns an object with attributes, not a subscriptable dict.
        # Try attribute access first, then fall back to dict conversion.
        content = None
        try:
            content = resp.choices[0].message.content
            # print("Content received:", content)
        except Exception:
            try:
                resp_dict = resp.to_dict()
                content = resp_dict["choices"][0]["message"]["content"]
            except Exception:
                # Fallback: stringify the whole response for debugging
                content = str(resp)

        # Use helper to clean and parse JSON
        data = _clean_and_parse_json(content)
        print("Parsed JSON data:", data)
        return data

    except Exception as e:
        print("OpenAI request failed:", e)
        return {"error": str(e)}

def goal_step_map(goal_id,steps):
    try:
        print("goal_step_map",goal_id,steps)
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            INSERT INTO user_goal_path (goal_id, steps)
            VALUES (%s, %s::jsonb)
        """

        cursor.execute(query, (goal_id, json.dumps(steps)))
        conn.commit()

        cursor.close()
        conn.close()

        return True
    except Exception as e:
        print("Error in goal_step_map:", e)
        conn.rollback()
        return False

def get_recommendation_based_on_skill(payload):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    prompt_template = """
        You are an expert online course recommendation engine.

        Your task is to recommend REAL, currently available online courses
        from trusted platforms such as:
        Coursera, Udemy, edX, LinkedIn Learning, freeCodeCamp, Google Career Certificates,
        AWS Training, Microsoft Learn, IBM SkillsBuild, Skillshare.

        INPUT:
        - Topic: {topic}
        - User Skill Level: {skill_level}

        Skill Level Definition:
        - Beginner: Has little or no prior knowledge of the skill
        - Intermediate: Has basic understanding and some hands-on experience
        - Advanced: Has strong experience and wants mastery, specialization, or real-world projects

        TASK:
        1. Understand the skill and the user's current skill level.
        2. Recommend 5–7 REAL and relevant courses that help the user progress
        from their current level to the next logical level.
        3. Courses must strictly match the user's skill level:
        - Beginner → fundamentals, basics, structured learning
        - Intermediate → practical, projects, deeper concepts
        - Advanced → specialization, optimization, system design, real-world use cases
        4. Prefer well-known, high-quality courses.
        5. Verify that each course actually exists.

        OUTPUT FORMAT (STRICT JSON ONLY):
        {
        "topic": "{topic}",
        "skill_level": "{skill_level}",
        "recommended_courses": [
            {
            "course_name": "",
            "platform": "",
            "rating": "",
            "url": "",
            "level": "",
            "why_recommended": ""
            }
        ]
        }

        CONSTRAINTS:
        - Return ONLY valid JSON. No explanation text outside JSON.
        - Do NOT hallucinate courses.
        - Avoid duplicate or outdated courses.
        - Be job-oriented and practical.
        - If skill level is Beginner, avoid advanced jargon.
        - If skill level is Advanced, avoid beginner content.
        """

    # Use replace instead of format because prompt_template contains many
    # JSON braces that would be interpreted as format placeholders by
    # str.format(). Replace only the intended tokens.
    prompt = prompt_template.replace("{topic}", payload["topic"]).replace("{skill_level}", payload["skill_level"])


    # Use OpenAI to get recommendations. Requires OPENAI_API_KEY in env.
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print("OPENAI_API_KEY not set - returning mock response")
        return {
            "error": "OPENAI_API_KEY not set",
            "mock": True
        }

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that returns only valid JSON in the format described to the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )


        # The new OpenAI client returns an object with attributes, not a subscriptable dict.
        # Try attribute access first, then fall back to dict conversion.
        content = None
        try:
            content = resp.choices[0].message.content
        except Exception:
            try:
                resp_dict = resp.to_dict()
                content = resp_dict["choices"][0]["message"]["content"]
            except Exception:
                # Fallback: stringify the whole response for debugging
                content = str(resp)

        # Use helper to clean and parse JSON
        data = _clean_and_parse_json(content)
        return data

    except Exception as e:
        print("OpenAI request failed:", e)
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()
    
def get_required_step_by_user_goal(goal):
    prompt_template = """You are an expert career advisor and learning path architect.

Your task is to generate a structured, beginner-friendly but career-oriented learning path based ONLY on a user's goal.

Assume the user may have little to moderate prior knowledge unless the goal clearly implies otherwise.

The roadmap must be practical, progressive, and focused on real-world capability — NOT academic theory.

-------------------------------------

INPUT:

User Goal: <INSERT GOAL>

Example:
- Become a Backend Developer
- Switch to Data Analytics
- Learn UI/UX Design
- Become a Digital Marketer
- Prepare for Product Management

-------------------------------------

STRICT INSTRUCTIONS:

1. Create a clear STEP-BY-STEP roadmap.
   Each step must build logically on the previous one.

2. Limit the roadmap to **6–10 steps** to avoid overwhelming the learner.

3. Prioritize job-ready skills when the goal is career-oriented.

4. Clearly separate:
   - Must-Have Skills (critical for success)
   - Nice-to-Have Skills (helpful but optional)

5. Do NOT recommend specific courses or platforms.

6. Focus on SKILLS only — courses will be mapped later.

7. Keep the path realistic so an average learner can follow it.

8. Order skills from foundational → advanced.

9. Avoid overly generic steps like "practice more".

10. Make the roadmap feel like it was created by a senior career mentor.

-------------------------------------

OUTPUT FORMAT (STRICT JSON ONLY):

{
  "goal": "string",
  "assumed_starting_level": "Beginner to Intermediate",
  "estimated_time_to_goal": "string",
  "learning_path": [
    {
      "step_number": 1,
      "skill": "string",
      "type": "Must-Have | Nice-to-Have",
    }
  ],
  
}

-------------------------------------

IMPORTANT:

Return ONLY valid JSON.
Do NOT include markdown.
Do NOT add explanations outside the JSON.
"""

    prompt = prompt_template.replace("<INSERT GOAL>", goal)

    # Use OpenAI to get recommendations. Requires OPENAI_API_KEY in env.
    api_key = Config.OPENAI_API_KEY
    if not api_key:
        print("OPENAI_API_KEY not set - returning mock response")
        return {
            "error": "OPENAI_API_KEY not set",
            "mock": True
        }

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that returns only valid JSON in the format described to the user."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )


        # The new OpenAI client returns an object with attributes, not a subscriptable dict.
        # Try attribute access first, then fall back to dict conversion.
        content = None
        try:
            content = resp.choices[0].message.content
        except Exception:
            try:
                resp_dict = resp.to_dict()
                content = resp_dict["choices"][0]["message"]["content"]
            except Exception:
                # Fallback: stringify the whole response for debugging
                content = str(resp)

        # Use helper to clean and parse JSON
        data = _clean_and_parse_json(content)
        return data

    except Exception as e:
        print("OpenAI request failed:", e)
        return {"error": str(e)}