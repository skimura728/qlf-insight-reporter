import os
from flask import Flask, jsonify
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
from notion_client import Client as NotionClient
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/run-report", methods=["GET"])
def run_report():
    client = bigquery.Client()
    notion_token = os.environ["NOTION_API_TOKEN"]
    notion_page_id = os.environ["NOTION_PAGE_ID"]
    notion = NotionClient(auth=notion_token)

    projects = {
        "Android": ("qlf-analytics", "analytics_484729799"),
        "Web": ("quicklearnfeed", "analytics_487953054")
    }

    report_lines = ["# 📊 QLF Insight Report"]

    for label, (project_id, dataset_id) in projects.items():
        report_lines.append(f"## 🔹 {label} 版")

        # 最新の events_YYYYMMDD テーブル取得
        latest_table_query = f"""
        SELECT
          table_id
        FROM `{project_id}.{dataset_id}.__TABLES_SUMMARY__`
        WHERE STARTS_WITH(table_id, 'events_')
        ORDER BY table_id DESC
        LIMIT 1
        """
        try:
            latest_table_id = client.query(latest_table_query).to_dataframe()["table_id"].iloc[0]
        except Exception as e:
            report_lines.append(f"⚠️ 最新テーブル取得エラー: {str(e)}\n")
            continue

        # 最新日のイベントランキング
        try:
            query_latest = f"""
                SELECT event_name, COUNT(*) AS event_count
                FROM `{project_id}.{dataset_id}.{latest_table_id}`
                GROUP BY event_name
                ORDER BY event_count DESC
                LIMIT 10
            """
            df_latest = client.query(query_latest).to_dataframe()
            report_lines.append(f"### 📅 最新: {latest_table_id}")
            report_lines.append("| event_name | count |")
            report_lines.append("|------------|-------|")
            for _, row in df_latest.iterrows():
                report_lines.append(f"| {row['event_name']} | {row['event_count']} |")
            report_lines.append("")
        except Exception as e:
            report_lines.append(f"⚠️ 最新データ取得エラー: {str(e)}\n")

        # 全期間累計のイベントランキング
        try:
            query_all = f"""
                SELECT event_name, COUNT(*) AS event_count
                FROM `{project_id}.{dataset_id}.events_*`
                GROUP BY event_name
                ORDER BY event_count DESC
                LIMIT 10
            """
            df_all = client.query(query_all).to_dataframe()
            report_lines.append("### 🗓 累計（全期間）")
            report_lines.append("| event_name | total_count |")
            report_lines.append("|------------|--------------|")
            for _, row in df_all.iterrows():
                report_lines.append(f"| {row['event_name']} | {row['event_count']} |")
            report_lines.append("")
        except Exception as e:
            report_lines.append(f"⚠️ 累計データ取得エラー: {str(e)}\n")

    markdown_report = "\n".join(report_lines)

    with open("qlf_insight_report.md", "w", encoding="utf-8") as f:
        f.write(markdown_report)

    try:
        notion.pages.create(
            parent={"page_id": notion_page_id},
            properties={
                "title": [{"type": "text", "text": {"content": f"📊 QLF Report - {datetime.today().strftime('%Y%m%d')}"}}]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": markdown_report[:2000]}}
                        ]
                    }
                }
            ]
        )
    except Exception as e:
        print(f"⚠️ Notion連携エラー: {str(e)}")

    return jsonify({"status": "ok", "message": "レポート生成＆Notion投稿完了"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)