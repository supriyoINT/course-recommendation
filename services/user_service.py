import os
import json as pyjson
from flask import json
from config import Config
from openai import OpenAI
from db import get_db
from psycopg2.extras import RealDictCursor

def get_users():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users;")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return [
        {
            "userId": r["id"],
            "name": r["name"],
            "email": r["email"]
        }
        for r in rows
    ]

def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE email = %s;",(email,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return None
    return {
        "userId": row["id"],
        "name": row["name"],
        "email": row["email"]
    }
def collect_user_data(data):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        INSERT INTO user_data (userId, data)
        VALUES (%s, %s::jsonb)
    """

    cursor.execute(query, (
        101,          # userId
        json.dumps(data)  # convert Python dict → JSON string
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return True

def create_user(data):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        INSERT INTO users (name, email)
        VALUES (%s, %s)
    """

    cursor.execute(query, (
        data["name"],          # userId
        data["email"]  # convert Python dict → JSON string
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return True

def create_profile(data):
    print(data)
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        INSERT INTO user_profile (
            user_type, goal, interest_area, experience_level, background,
            current_skills, learning_purpose, preferred_learning_style,
            preferred_platforms, budget, time_available_per_week,
            timeline, user_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        data["user_type"],
        data["goal"],
        data["interest_area"],
        data["experience_level"],
        data["background"],
        data["current_skills"],
        data["learning_purpose"],
        data["preferred_learning_style"],
        data["preferred_platforms"],
        data["budget"],                     # ← you forgot this before
        data["time_available_per_week"],
        data["timeline"],
        data["user_id"],
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return True

def get_profile(user_id):

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT * FROM user_profile WHERE user_id = %s
    """
    
    cursor.execute(query, (
        user_id,
    ))
    rows = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    print("rows", rows)
    if(len(rows)>0):
      return rows[0]
    else:
     return None

def create_user_goal(data):
    conn = get_db()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO user_goals (user_id, goal)
    VALUES (%s, %s)
    RETURNING id;
    """
    cursor.execute(insert_query, (data["user_id"], data["goal"]))
    goal_id = cursor.fetchone()[0]
    print("Inserted goal ID:", goal_id)
    conn.commit()

    cursor.close()
    conn.close()

    return goal_id 

def get_goal_steps(goal_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT * FROM user_goal_path WHERE goal_id = %s
    """
    print("Executing query for goal_id:", goal_id)
    cursor.execute(query, (
        goal_id,
    ))
    rows = cursor.fetchall()
    print("Fetched rows:", rows)
    conn.commit()
    cursor.close()
    conn.close()
    return rows

def generate_mcq_prompt(skill, num_questions=18):
    prompt = f"""
        You are an expert assessment creator.

        Your task is to generate EXACTLY {num_questions} multiple choice questions (MCQs) to accurately identify a user's current proficiency level in the skill: "{skill}".

        CRITICAL: You MUST return EXACTLY {num_questions} questions. No more, no less.

        IMPORTANT RULES:

        1. Total Questions: EXACTLY {num_questions} (this is mandatory)

        2. Difficulty Distribution (MANDATORY):
        - Easy: ~{int(num_questions * 0.30)} questions
        - Medium: ~{int(num_questions * 0.40)} questions
        - Hard: ~{int(num_questions * 0.30)} questions

        3. Questions must:
        - Test practical understanding, not just theory
        - Progress from basic → advanced
        - Be scenario-based where possible
        - Avoid ambiguous answers
        - Have ONLY one correct answer

        4. Skill Adaptation:
        - If the skill is technical, include problem-solving and conceptual questions.
        - If the skill is non-technical, include situational judgment and applied knowledge questions.

        5. Output Format (STRICT JSON ONLY — NO EXTRA TEXT):

        [
        {{
            "question": "string",
            "difficulty": "easy | medium | hard",
            "options": {{
                "A": "string",
                "B": "string",
                "C": "string",
                "D": "string"
            }},
            "correct_answer": "A/B/C/D",
            "explanation": "Brief explanation of why the answer is correct"
        }}
        ]

        DO NOT include markdown.
        DO NOT include commentary.
        RETURN ONLY VALID JSON.
        """
    return prompt
def run_generate_mcq(topic):
    openai_api_key = Config.OPENAI_API_KEY
    client = OpenAI(api_key=openai_api_key)

    prompt = generate_mcq_prompt(topic)
    print("prompt", prompt)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates multiple choice questions. ALWAYS return EXACTLY the number of questions requested."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=3000,
        n=1,
        stop=None,
    )

    mcq_json_str = response.choices[0].message.content.strip()

    try:
        mcq_data = pyjson.loads(mcq_json_str)
    except pyjson.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return None

    return mcq_data
def get_user_goals(user_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT * FROM user_goals WHERE user_id = %s
    """
    
    cursor.execute(query, (
        user_id,
    ))
    rows = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return rows