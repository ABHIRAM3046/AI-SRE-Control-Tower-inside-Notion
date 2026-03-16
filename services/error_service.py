import random
import time
import argparse
from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_API_KEY)

service_names = [
    "auth-service", 
    "payment-service", 
    "user-service", 
    "inventory-service",
    "order-service",
]

errors=[
    "503 Service Unavailable - database connection timeout",
    "Pod crash due to OOMKilled",
    "Pod crash loop Detected",
    "Connection refused to Redis",
    "Memory Limit exceeded",
    "Disk I/O error on database",
    "High latency detected in payment processing",
    "Kafka consumer lag increasing rapidly",
    "External API timeout causing request failures",
    "Spike in error rates after recent deployment"
]

severities = ["low", "medium", "high", "critical"]

def create_incident():
    service_name = random.choice(service_names)
    error_log = random.choice(errors)
    severity = random.choice(severities)

    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "Service Name": {
                "title": [{"text": {"content": service_name}}]
            },
            "Service Status": {
                "select": {"name": "Open"}
            },
            "Error Logs": {
                "rich_text": [{"text": {"content": error_log}}]
            },
            "Severity": {
                "select": {"name": severity}
            }
        }
    )   
    
    print(f"Incident Created: {service_name} -> {error_log}")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic incidents in Notion")
    parser.add_argument("--once", action="store_true", help="Create one incident and exit")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between incidents")
    args = parser.parse_args()

    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID are required in .env")

    if args.once:
        create_incident()
        return

    while True:
        create_incident()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
    