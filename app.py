from flask import Flask, jsonify, request
import requests
import sqlite3
from datetime import datetime, timezone
from uuid6 import uuid7

app = Flask(__name__)
app.json.sort_keys = False

def get_db_connection():
    conn = sqlite3.connect("profiles.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE,
    gender TEXT,
    gender_probability REAL,
    sample_size INTEGER,
    age INTEGER,
    age_group TEXT,
    country_id TEXT,
    country_probability REAL,
    created_at TEXT)""")

    conn.commit()
    conn.close()

init_db()

@app.route("/api/profiles", methods=["POST"])
def create_profile():
    data = request.get_json()

    if not data:
        return jsonify({"status": "error",
                        "message": "Request body is required"}), 400

    name = data.get("name")

    if name is None or name.strip() == "":
        return jsonify({"status": "error",
                        "message": "Missing or empty name"}), 400

    if not isinstance(name, str) or not name.isalpha():
        return jsonify({"status": "error",
                        "message": "Invalid name format"}), 422
    name = name.lower()

    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM profiles WHERE name = ?", (name,)).fetchone()

    if existing:
        conn.close()
        return jsonify({"status": "success",
                        "message": "Profile already exists",
                        "data": dict(existing)}), 200
    conn.close()

    try:
        gender_res = requests.get("https://api.genderize.io", params={"name": name}, timeout=5)

        age_res = requests.get("https://api.agify.io", params={"name": name}, timeout=5)

        nation_res = requests.get("https://api.nationalize.io", params={"name": name}, timeout=5)

        gender_data = gender_res.json()
        age_data = age_res.json()
        nation_data = nation_res.json()

        gender = gender_data.get("gender")
        gender_probability = gender_data.get("probability")
        count = gender_data.get("count")

        if gender is None or count == 0:
            return jsonify({"status": "error",
                            "message": "Genderize returned an invalid response"}), 502

        age = age_data.get("age")
        if age is None:
            return jsonify({"status": "error",
                            "message": "Agify returned an invalid response"}), 502

        countries = nation_data.get("country")
        if not countries:
            return jsonify({"status": "error",
                            "message": "Nationalize returned an invalid response"}), 502

        top_country = max(countries, key=lambda x: x["probability"])
        country_id = top_country.get("country_id")
        country_probability = top_country.get("probability")

        if age <= 12:
            age_group = "child"
        elif age <= 19:
            age_group = "teenager"
        elif age <= 59:
            age_group = "adult"
        else:
            age_group = "senior"

        profile_id = str(uuid7())
        created_at = datetime.now(timezone.utc).isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO profiles (
        id, name, gender, gender_probability,
        sample_size, age, age_group, country_id,
        country_probability, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (profile_id,
                        name.lower(),
                        gender,
                        gender_probability,
                        count,
                        age,
                        age_group,
                        country_id,
                        country_probability,
                        created_at))
        conn.commit()
        conn.close()

        return jsonify({"status": "success",
                        "data":{
                            "id": profile_id,
                            "name": name.lower(),
                            "gender": gender,
                            "gender_probability": gender_probability,
                            "sample_size" : count,
                            "age": age,
                            "age_group": age_group,
                            "country_id": country_id,
                            "country_probability": country_probability,
                            "created_at": created_at}}), 201

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error",
                        "message": str(e)}), 500

@app.route("/api/profiles/<profile_id>", methods=["GET"])
def get_profile(profile_id):
    conn = get_db_connection()

    profile = conn.execute("SELECT * FROM profiles WHERE id = ?",
                           (profile_id,)).fetchone()
    conn.close()

    if not profile:
        return jsonify({"status": "error",
                        "message": "Profile not found"}), 404

    return jsonify({"status": "success",
                    "data": dict(profile)}), 200

@app.route("/api/profiles", methods=["GET"])
def get_profiles():
    conn = get_db_connection()

    gender= request.args.get("gender")
    country_id = request.args.get("country_id")
    age_group = request.args.get("age_group")

    query = "SELECT * FROM profiles WHERE 1=1"
    params = []

    if gender:
        query += " AND LOWER(gender) = ?"
        params.append(gender.lower())

    if country_id:
        query += " AND LOWER(country_id) = ?"
        params.append(country_id.lower())

    if age_group:
        query += " AND LOWER(age_group) = ?"
        params.append(age_group.lower())

    rows = conn.execute(query, params).fetchall()
    conn.close()

    profiles = [dict(row) for row in rows]

    return jsonify({"status": "success",
                    "count": len(profiles),
                    "data": profiles})

@app.route("/api/profiles/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute("SELECT * FROM profiles WHERE id = ?",
                              (profile_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"status": "error",
                        "message": "Profile not found"}), 404

    cursor.execute("DELETE FROM profiles WHERE id = ?",
                   (profile_id,))
    conn.commit()
    conn.close()

    return "", 204


@app.after_request
def add_cors_headers(response):
    response.headers["Access-control-Allow-Origin"] = "*"
    return response


if __name__ == "__main__":
    app.run(debug=True)