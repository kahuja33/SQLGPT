from sqlalchemy import create_engine, text
import pandas as pd
import psycopg2

# Replace with your actual database details
DB_HOST = "aws-0-ap-northeast-2.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.nrgkpbjgqwwvejwqyojo"
DB_PASSWORD = "oWrWR7gituTcBi46"
DB_PORT = "6543"

# SQLAlchemy connection string format
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def execute_query(query):
    with engine.connect() as conn:
        if isinstance(query, str):
            query = text(query)
        result = conn.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df

def get_schema(table_name):
        query = text(f"""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        schema = execute_query(query)
        return schema