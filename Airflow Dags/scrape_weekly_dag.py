from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import os
from sqlalchemy import create_engine
from google.cloud import bigquery
import sys
import scrape

sys.path.append('/opt/airflow/dags')  # modify to your own path


# PostgreSQL connection
pg_engine = create_engine("postgresql+psycopg2://root:root@pgdatabase:5432/project1")

# BigQuery connection
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/config/zhenxin-project1-5cf4852febfb.json"  # your GCP auth file path
bq_client = bigquery.Client()
bq_project = "zhenxin-project1"   # replace with your own GCP project ID
bq_dataset = "sports_analysis"      # replace with your BigQuery Dataset

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
    'scrape_weekly',
    default_args=default_args,
    description='Weekly scrape for sports data',
    schedule_interval='0 7 * * 0',  # 每周日7点执行
    catchup=False,
)

# define scraping functions
load_funcs = {
    'player_table': scrape.player_table,
    'all_time_table': scrape.all_time_table,
    'all_time_winner_club': scrape.all_time_winner_club,
    'top_scorers_seasons': scrape.top_scorers_seasons,
    'goals_per_season': scrape.goals_per_season
}

# data type mapping
numeric_columns_mapping = {
    'player_table': [],
    'all_time_table': ["pos", "Matches", "wins", "Draws", "Losses", "Dif", "Points"],
    'all_time_winner_club': [],
    'top_scorers_seasons': ["goals"],
    'goals_per_season': ["Goals", "Matches", "Average Goals"]
}

def load_table_to_db(table_func, table_name, expected_cols):
    df = table_func()
    if df.empty:
        print(f"No data for {table_name}")
        return
    
    df.columns = expected_cols
    df['ingestion_time'] = pd.to_datetime('now')

    # data type conversion
    if table_name in numeric_columns_mapping:
        num_cols = numeric_columns_mapping[table_name]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int64')
    
    # upload data
    df.to_sql(name=table_name, con=pg_engine, if_exists='append', index=False)
    df.to_gbq(destination_table=f"{bq_dataset}.{table_name}", project_id=bq_project, if_exists='append')
    print(f"{table_name} loaded successfully.")

expected_cols_mapping = {
    'player_table': ["Player", "Team", "born", "Height", "Position"],
    'all_time_table': ["pos", "Team", "Matches", "wins", "Draws", "Losses", "Goals", "Dif", "Points"],
    'all_time_winner_club': ["Year", "Winner", "Country"],
    'top_scorers_seasons': ["Season", "Top scorer", "Team", "goals"],
    'goals_per_season': ["Season", "Goals", "Matches", "Average Goals"]
}


for table_name, func in load_funcs.items():
    expected_cols = expected_cols_mapping[table_name]
    
    PythonOperator(
        task_id=f'load_{table_name}_weekly',
        python_callable=load_table_to_db,
        op_args=[func, table_name, expected_cols],
        dag=dag,
    )
