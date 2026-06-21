import time
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.dependencies import get_historical_df_from_db

start = time.time()
print("Querying historical data from DB...")
df = get_historical_df_from_db(product_id="P001")
print(f"Loaded dataframe with shape: {df.shape} in {time.time() - start:.2f} seconds.")
