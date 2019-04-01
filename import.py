import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Open csv file and transfer to the database

f = open("books.csv")
reader = csv.reader(f)

for isbn,title,author,year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn,
        "title": title,
        "author": author,
        "year": year}
        )
    db.commit()
