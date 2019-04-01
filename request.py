import requests

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ciGC4lMaLH8yZ2DyCAgKw", "isbns": "1632168146"})
print(res.json())
