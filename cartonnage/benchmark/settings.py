import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'benchmark.db')

AMOUNT_OF_WAREHOUSES = 5
AMOUNT_OF_PROCESSES = 2
TEST_DURATION = 60       # seconds per transaction type
PRINT_INTERVAL = 10      # seconds between progress prints
