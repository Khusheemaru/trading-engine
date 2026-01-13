import psycopg2
import config

class DatabaseHandler:
    def __init__(self):
        self.conn = None
        self.cur = None

    def connect(self):
        """Establish connection to the PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASS,
                host=config.DB_HOST,
                port=config.DB_PORT
            )
            self.conn.autocommit = True # Auto-save data
            self.cur = self.conn.cursor()
            print(">> [DB] Connected to PostgreSQL")
        except Exception as e:
            print(f"!! [DB] Connection Error: {e}")

    def insert_signal(self, symbol, signal_type, price, sma):
        """Save a trade signal to the database"""
        if not self.conn:
            self.connect()
        
        try:
            query = """
                INSERT INTO trade_signals (symbol, signal_type, price, sma) 
                VALUES (%s, %s, %s, %s)
            """
            self.cur.execute(query, (symbol, signal_type, price, sma))
            # Optional: Uncomment to confirm every save
            # print(f"   [DB] Saved {signal_type} for {symbol}")
            
        except Exception as e:
            print(f"!! [DB] Insert Error: {e}")
            # If connection dropped, try to reconnect once
            self.connect()

    def close(self):
        if self.cur: self.cur.close()
        if self.conn: self.conn.close()