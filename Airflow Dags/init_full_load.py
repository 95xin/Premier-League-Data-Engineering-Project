import pandas as pd
import scrape
from sqlalchemy import create_engine
from google.cloud import bigquery
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta


import sys
sys.path.append('/opt/airflow/dags')  # modify to your own path


# PostgreSQL connection
pg_engine = create_engine("postgresql+psycopg2://root:root@pgdatabase:5432/project1")

# BigQuery connection
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/config/zhenxin-project1-5cf4852febfb.json"
bq_client = bigquery.Client()
bq_project = "zhenxin-project1"
bq_dataset = "sports_analysis"

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'initial_full_load',
    default_args=default_args,
    description='Initial full load DAG for sports data',
    schedule_interval=None,
)

# all scraping functions
load_funcs = {
    'league_table': scrape.league_table,
    'top_scorers': scrape.top_scorers,
    'detail_top': scrape.detail_top,
    'player_table': scrape.player_table,
    'all_time_table': scrape.all_time_table,
    'all_time_winner_club': scrape.all_time_winner_club,
    'top_scorers_seasons': scrape.top_scorers_seasons,
    'goals_per_season': scrape.goals_per_season
}

# define columns that need to be converted to numeric
numeric_columns_mapping = {
    'league_table': ["Played", "Won", "Drawn", "Lost", "Goals For", "Goals Against", "Goal Difference", "Points"],
    'detail_top': ["Goals", "Penalty"],
    'all_time_table': ["pos", "Matches", "wins", "Draws", "Losses", "Dif", "Points"],
    'top_scorers_seasons': ["goals"],
    'goals_per_season': ["Goals", "Matches", "Average Goals"]
}

def initial_full_load():
    for table_name, func in load_funcs.items():
        print(f"Loading {table_name}...")
        df = func()
        if df.empty:
            print(f"No data for {table_name}")
            continue

        # add ingestion_time
        df['ingestion_time'] = pd.to_datetime('now')

        # type handling
        if table_name in numeric_columns_mapping:
            num_cols = numeric_columns_mapping[table_name]
            for col in num_cols:
                if col in df.columns:
                    if col == "Average Goals":
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('float64')
                    else:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')

        # upload to PostgreSQL
        df.to_sql(name=table_name, con=pg_engine, if_exists='replace', index=False)
        # upload to BigQuery
        df.to_gbq(destination_table=f"{bq_dataset}.{table_name}", project_id=bq_project, if_exists='append')
        print(f"{table_name} loaded successfully.")

initial_load_task = PythonOperator(
    task_id='initial_full_load_task',
    python_callable=initial_full_load,
    dag=dag,
)
