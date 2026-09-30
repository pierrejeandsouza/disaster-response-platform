"""
backend/database.py

Real Supabase-backed persistence, replacing the in-memory dicts from
main.py's first version. Reads credentials from a local .env file --
never hardcode these directly in source code.

Requires two tables in your Supabase project (SQL to create them is in
schema.sql in this same folder -- run that in Supabase's SQL Editor
before this will work).
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()  # reads SUPABASE_URL and SUPABASE_KEY from .env

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in a .env file "
        "in the project root -- see .env.example for the format."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def insert_request(request_dict: dict) -> dict:
    result = supabase.table("emergency_requests").insert(request_dict).execute()
    return result.data[0]


def update_request(request_id: str, updates: dict) -> dict:
    result = supabase.table("emergency_requests").update(updates).eq("id", request_id).execute()
    return result.data[0] if result.data else None


def get_all_requests(status: str = None) -> list[dict]:
    query = supabase.table("emergency_requests").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    return query.execute().data


def get_request_by_id(request_id: str) -> dict:
    result = supabase.table("emergency_requests").select("*").eq("id", request_id).execute()
    return result.data[0] if result.data else None


def insert_resource(resource_dict: dict) -> dict:
    result = supabase.table("resources").insert(resource_dict).execute()
    return result.data[0]


def update_resource(resource_id: str, updates: dict) -> dict:
    result = supabase.table("resources").update(updates).eq("id", resource_id).execute()
    return result.data[0] if result.data else None


def get_all_resources(available_only: bool = False) -> list[dict]:
    query = supabase.table("resources").select("*")
    if available_only:
        query = query.eq("available", True)
    return query.execute().data
