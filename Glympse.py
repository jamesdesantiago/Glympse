import streamlit as st
from empyrial import empyrial, Engine
import pandas as pd
import sqlite3

# Function to connect to the SQLite database
def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
    return conn

# Function to initialize the portfolio table
def init_portfolio_table(conn):
    try:
        sql_create_portfolio_table = """
        CREATE TABLE IF NOT EXISTS portfolio (
            id integer PRIMARY KEY,
            assets text NOT NULL,
            weights text,
            optimization text,
            start_date text,
            benchmark text
        );
        """
        cursor = conn.cursor()
        cursor.execute(sql_create_portfolio_table)
    except Exception as e:
        st.error(f"Error creating table: {e}")

# Function to insert a new portfolio into the portfolio table
def save_portfolio(conn, portfolio):
    sql = ''' INSERT INTO portfolio(assets,weights,optimization,start_date,benchmark)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, portfolio)
    conn.commit()
    return cur.lastrowid

# Function to load the latest portfolio
def load_latest_portfolio(conn):
    sql = ''' SELECT * FROM portfolio ORDER BY id DESC LIMIT 1 '''
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    if rows:
        return rows[0]
    else:
        return None

# Streamlit app title and database initialization
st.title('Portfolio Analysis and Optimization')
database = "portfolio.db"
conn = create_connection(database)
init_portfolio_table(conn)

# Sidebar inputs for user interaction
st.sidebar.header('Portfolio Configuration')

# Load the latest portfolio if available
latest_portfolio = load_latest_portfolio(conn)
default_assets = 'SPTM,SPAB,SPDW' if not latest_portfolio else latest_portfolio[1]
default_weights = '0.46,0.37,0.14' if not latest_portfolio else latest_portfolio[2]

# Allowing users to input ticker symbols
assets = st.sidebar.text_input('Enter ticker symbols (comma separated)', default_assets).split(',')

# Allowing users to input weights, converting the string input into a list of floats
weights = list(map(float, st.sidebar.text_input('Enter portfolio weights (comma separated)', default_weights).split(',')))

# Predefined options
optimization_options = ['EF', 'MEANVAR', 'HRP', 'MINVAR']
benchmark_options = ['Income', 'Conservative Growth', 'Moderate Growth', 'Growth']

# Selection for optimization strategy
optimization = st.sidebar.selectbox('Select optimization strategy', optimization_options, index=optimization_options.index(latest_portfolio[3]) if latest_portfolio else 0)

# Start date input
default_start_date = pd.to_datetime('2018-01-01') if not latest_portfolio else pd.to_datetime(latest_portfolio[4])
start_date = st.sidebar.date_input('Start date', default_start_date)

# Allowing users to select a benchmark risk strategy
portfolio_benchmark = st.sidebar.selectbox('Select benchmark risk strategy', benchmark_options, index=benchmark_options.index(latest_portfolio[5]) if latest_portfolio else 2)

# Button to perform analysis and save the configuration
if st.sidebar.button('Analyze and Save Portfolio'):
    try:
        # Define the portfolio with user inputs
        portfolio = Engine(
            start_date=start_date,
            portfolio=assets,
            weights=weights,
            optimizer=optimization,
            benchmark=[portfolio_benchmark]
        )
        
        # Perform analysis
        empyrial(portfolio)

        # Display recommended weights
        st.write('Recommended Portfolio Weights:', portfolio.weights)
        
        # Save the portfolio to the database
        save_portfolio(conn, (','.join(assets), ','.join(map(str, weights)), optimization, start_date.strftime('%Y-%m-%d'), portfolio_benchmark))
        st.success("Portfolio saved successfully!")
    except Exception as e:
        st.error(f'An error occurred: {e}')

# Instructions or additional information
st.markdown('''
This application allows users to analyze and optimize their investment portfolios based on selected tickers, weights, optimization strategy, and benchmark risk strategy.
Your portfolio configurations are saved for future reference.
''')

if conn:
    conn.close()
