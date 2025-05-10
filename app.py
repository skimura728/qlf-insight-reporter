import os
from datetime import datetime
import pandas as pd
from google.cloud import bigquery
from notion_client import Client as NotionClient
from dotenv import load_dotenv

load_dotenv()

def block_heading(text, level=2):
    return {
        "object": "block",
        "type": f"heading_{level}",
        f"heading_{level}": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def block_bullet(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def block_paragraph(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def run_report():
    notion_token = os.environ["NOTION_API_TOKEN"]
    notion_page_id = os.environ["NOTION_PAGE_ID"]
    client = bigquery.Client()
    notion = NotionClient(auth=notion_token)

    today = datetime.today().strftime("%Y-%m-%d")
    projects = {
        "Android": ("qlf-analytics", "analytics_484729799"),
        "Web": ("quicklearnfeed", "analytics_487953054")
    }

    blocks = [block_heading(f"QLF Report - {today}", level=2)]

    for label, (project_id, dataset_id) in projects.items():
        blocks.append(block_heading(f"{label} 版", level=2))

        try:
            latest_query = (
                f"SELECT table_id FROM `{project_id}.{dataset_id}.__TABLES_SUMMARY__` "
                f"WHERE STARTS_WITH(table_id, 'events_') ORDER BY table_id DESC LIMIT 1"
            )
            latest_table = client.query(latest_query).to_dataframe()["table_id"].iloc[0]
        except Exception as e:
            blocks.append(block_paragraph(f"⚠️ 最新テーブル取得エラー: {str(e)}"))
            continue

        try:
            query_latest = (
                f"SELECT event_name, COUNT(*) AS event_count "
                f"FROM `{project_id}.{dataset_id}.{latest_table}` "
                f"GROUP BY event_name ORDER BY event_count DESC"
            )
            df_latest = client.query(query_latest).to_dataframe()
            blocks.append(block_heading(f"📅 最新: {latest_table}", level=3))
            for _, row in df_latest.iterrows():
                blocks.append(block_bullet(f"{row['event_name']}: {row['event_count']}"))
        except Exception as e:
            blocks.append(block_paragraph(f"⚠️ 最新データ取得エラー: {str(e)}"))

        try:
            query_all = (
                f"SELECT event_name, COUNT(*) AS event_count "
                f"FROM `{project_id}.{dataset_id}.events_*` "
                f"GROUP BY event_name ORDER BY event_count DESC"
            )
            df_all = client.query(query_all).to_dataframe()
            blocks.append(block_heading("🗓 累計（全期間）", level=3))
            for _, row in df_all.iterrows():
                blocks.append(block_bullet(f"{row['event_name']}: {row['event_count']}"))
        except Exception as e:
            blocks.append(block_paragraph(f"⚠️ 累計データ取得エラー: {str(e)}"))

    try:
        notion.pages.create(
            parent={"page_id": notion_page_id},
            properties={
                "title": [{"type": "text", "text": {"content": f"📊 QLF Report - {today}"}}]
            },
            children=blocks
        )
        print("✅ Notion投稿成功")
    except Exception as e:
        print(f"❌ Notion連携エラー: {str(e)}")

if __name__ == "__main__":
    run_report()