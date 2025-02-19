import sqlite3
import pandas as pd
import bcrypt

def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Таблиця користувачів
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Таблиця оцінок лише зареєстрованих користувачів
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER NOT NULL,
            movieId INTEGER NOT NULL,
            rating REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userId) REFERENCES users(id),
            FOREIGN KEY (movieId) REFERENCES movies(movieId)
        )
    """)

    # Таблиця фільмів
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
        movieId INTEGER PRIMARY KEY,
        title TEXT,
        genres TEXT,
        imdbId INTEGER,
        tmdbId INTEGER,
        popularity REAL,
        budget REAL,
        revenue REAL,
        original_title TEXT,
        cast TEXT,
        homepage TEXT,
        director TEXT,
        tagline TEXT,
        keywords TEXT,
        overview TEXT,
        runtime INTEGER,
        production_companies TEXT,
        release_date TEXT,
        vote_count INTEGER,
        vote_average REAL,
        release_year INTEGER,
        budget_adj REAL,
        revenue_adj REAL,
        tag TEXT,
        content TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("✅ База даних створена!")

def load_movies():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Завантажуємо CSV
    movies = pd.read_csv("data/processed_movies.csv")

    # Вставляємо всі необхідні колонки
    for _, row in movies.iterrows():
        try:
            cursor.execute("""
                INSERT INTO movies (
                    movieId, title, genres, imdbId, tmdbId, popularity, budget, revenue,
                    original_title, cast, homepage, director, tagline, keywords, overview,
                    runtime, production_companies, release_date, vote_count, vote_average,
                    release_year, budget_adj, revenue_adj, tag, content
                )
                VALUES (?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["movieId"], row["title"], row["genres"], row["imdbId"], row["tmdbId"],
                row["popularity"], row["budget"], row["revenue"], row["original_title"],
                row["cast"], row["homepage"], row["director"], row["tagline"], row["keywords"],
                row["overview"], row["runtime"], row["production_companies"], row["release_date"],
                row["vote_count"], row["vote_average"], row["release_year"], row["budget_adj"],
                row["revenue_adj"], row["tag"], row["content"]
            ))
        except sqlite3.IntegrityError:
            print(f"⚠️ Фільм '{row['title']}' (ID: {row['movieId']}) вже є в базі")

    conn.commit()
    conn.close()
    print("✅ Завантаження фільмів завершено!")

# Функція для хешування паролів
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

create_database()
load_movies()