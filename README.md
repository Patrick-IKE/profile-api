# Backend Wizards — Stage 1 API
Data Persistence & API Design Assessment

## Overview

This is a Flask-based REST API that creates and manages user profiles by integrating data from external services.
It processes and stores the data in a SQLite database and exposes endpoints to retrieve and manage profiles.

---

## Live URL

https://your-app-url.up.railway.app

---

## Tech Stack

- Python (Flask)
- SQLite
- Requests
- UUID v7 (uuid6)

---

## External APIs

- Genderize → predicts gender
- Agify → predicts age
- Nationalize → predicts nationality

---

## Endpoints

### Create Profile
 
POST "/api/profiles"

Request:

{ "name": "ella" }

- 201 → profile created
- 200 → profile already exists

---

## Get Profile by ID

GET "/api/profiles/{id}"

- 200 → success
- 404 → not found

---

## Get All Profiles

GET "/api/profiles"

Optional filters:

- gender
- country_id
- age_group

Example:

/api/profiles?gender=male&country_id=NG

---

## Delete Profile

DELETE "/api/profiles/{id}"

- 204 → deleted
- 404 → not found

---

## Running Locally

Clone the repo:

git clone https://github.com/your-username/your-repo.git
cd your-repo

Create virtual environment:

python -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run the server:

python app.py

---

## Requirements

Flask
requests
uuid6

---

## Notes

- All timestamps are in UTC (ISO 8601)
- IDs are generated using UUID v7
- Name input is case-insensitive
- Duplicate profiles are prevented (idempotency)
- CORS is enabled for all origins

