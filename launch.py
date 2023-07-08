import sys

from dotenv import load_dotenv

import main

if len(sys.argv) != 2:
    print("Usage: python launch.py <product>")
    exit(1)

load_dotenv()
r = main.Bot().execute({"product": sys.argv[1]})
print(r)
