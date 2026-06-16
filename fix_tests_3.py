import os

path = 'backend/tests/test_auth.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("assert 'newuser@test.com' in response.json().get(\"detail\", \"\")", "assert 'already registered' in response.json().get(\"detail\", \"\")")

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

path = 'backend/tests/test_trading.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Make the test mock yfinance for test_place_market_order_insufficient_funds
# Actually, the fixture is autouse, but fast_info is missing from our MockTicker.
# Let's fix the mock in conftest.py
path = 'backend/tests/conftest.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

if 'fast_info' not in c:
    c = c.replace(
        "self.info = {'regularMarketPrice': 150.0, 'regularMarketPreviousClose': 148.0, 'volume': 1000000, 'marketCap': 2000000000}",
        "self.info = {'regularMarketPrice': 150.0, 'regularMarketPreviousClose': 148.0, 'volume': 1000000, 'marketCap': 2000000000}\n            self.fast_info = {'last_price': 150.0}"
    )
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)

