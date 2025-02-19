import sqlite3
import bcrypt

def get_user_watch_history(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.movieId, m.title 
        FROM history h
        JOIN movies m ON h.movieId = m.movieId
        WHERE h.userId = ?
    """, (user_id,))
    
    watched_movies = cursor.fetchall()
    conn.close()
    
    return [{"movieId": movie[0], "title": movie[1]} for movie in watched_movies]

def get_user_ratings(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.movieId, m.title, r.rating
        FROM user_ratings r
        JOIN movies m ON r.movieId = m.movieId
        WHERE r.userId = ?
    """, (user_id,))
    
    user_ratings = cursor.fetchall()
    conn.close()
    
    return [{"movieId": row[0], "title": row[1], "rating": row[2]} for row in user_ratings]

def register_user(username, password):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Перевіряємо, чи існує користувач
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        print("❌ Користувач вже існує!")
        conn.close()
        return False

    # Хешуємо пароль
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Додаємо користувача
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

    print("✅ Реєстрація успішна!")
    return True

def login_user(username, password):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Отримуємо пароль з бази
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is None:
        print("❌ Користувач не знайдений!")
        conn.close()
        return None

    user_id, stored_password = user

    # Перевіряємо пароль
    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        print("✅ Успішний вхід! Ваш ID:", user_id)
        conn.close()
        return user_id
    else:
        print("❌ Неправильний пароль!")
        conn.close()
        return None

# Додавання оцінки фільму користувачем
def add_movie_rating(user_id, movie_id, rating):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Перевіряємо, чи користувач вже оцінив цей фільм
    cursor.execute("SELECT id FROM user_ratings WHERE userId = ? AND movieId = ?", (user_id, movie_id))
    existing_rating = cursor.fetchone()

    if existing_rating:
        # Оновлюємо існуючу оцінку
        cursor.execute("""
            UPDATE user_ratings 
            SET rating = ?, timestamp = CURRENT_TIMESTAMP
            WHERE userId = ? AND movieId = ?
        """, (rating, user_id, movie_id))
        print(f"✅ Оцінка фільму {movie_id} оновлена до {rating}")
    else:
        # Додаємо нову оцінку
        cursor.execute("""
            INSERT INTO user_ratings (userId, movieId, rating) 
            VALUES (?, ?, ?)
        """, (user_id, movie_id, rating))
        print(f"✅ Оцінка {rating} додана для фільму {movie_id}")

    conn.commit()
    conn.close()