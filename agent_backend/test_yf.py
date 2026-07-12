import yfinance as yf
print("AAPL", yf.Ticker("AAPL").history(period="1d"))
print("RELIANCE.NS", yf.Ticker("RELIANCE.NS").history(period="1d"))
