from flask import Flask, request, jsonify, render_template
import pandas as pd
import pickle
import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from surprise import SVD, Dataset, Reader
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_user_watch_history, get_user_ratings, add_movie_rating, login_user, register_user  # Імпортуємо з db.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "supersecretkey"  # Замініть на безпечний ключ
jwt = JWTManager(app)
# ✅ Завантаження моделей та даних при старті
#movies = pd.read_csv("data/processed_movies.csv")
#ratings = pd.read_csv("data/ratings.csv")
# Функція для завантаження фільмів з бази
def get_movies_from_db():
    conn = sqlite3.connect("database.db")
    query = "SELECT * FROM movies"
    movies_df = pd.read_sql_query(query, conn)
    conn.close()
    return movies_df

# Завантажуємо фільми з бази
movies = get_movies_from_db()
# Перевіряємо типи даних у DataFrame з бази

print(movies.dtypes)

with open("models/nearest_neighbors.pkl", "rb") as f:
    nn = pickle.load(f)

with open("models/tfidf.pkl", "rb") as f:
    tfidf = pickle.load(f)

with open("models/tfidf_matrix.pkl", "rb") as f:
    tfidf_matrix = pickle.load(f)

with open("models/svd_model.pkl", "rb") as f:
    svd_model = pickle.load(f)


# ✅ Векторизація назв фільмів для швидкого пошуку
vectorizer = TfidfVectorizer(stop_words="english")
title_matrix = vectorizer.fit_transform(movies["title"].fillna(""))
#user_mean_ratings = ratings.groupby("userId")["rating"].mean().to_dict()
print("✅ Дані та моделі завантажені!")
# Тест реєстрації та входу
# Реєстрація та вхід користувача
register_user("user123", "pass123")
user_id = login_user("user123", "pass123")
if user_id:
    print(f"🔹 Успішний вхід! Ваш ID: {user_id}")

    # Додаємо оцінки фільмів
   
    add_movie_rating(user_id, 85020, 5.0)
    add_movie_rating(user_id, 5574, 5.0) 
    add_movie_rating(user_id, 47200, 5.0) 
    
else:
    print("❌ Вхід не вдався.")

def find_best_match(movie_title):
    input_vector = vectorizer.transform([movie_title])
    similarities = cosine_similarity(input_vector, title_matrix).flatten()
    best_match_idx = np.argmax(similarities)
    best_match_title = movies.iloc[best_match_idx]["title"]
    best_match_id = movies.iloc[best_match_idx]["movieId"]
    return best_match_title, best_match_id

# 📌 Функція для отримання рекомендацій
def get_recommendations_for_user(user_id, watched_movies, top_n=10, weight_knn=0.8, weight_svd=0.2):
    recommendation_scores = defaultdict(lambda: {"knn": 0, "svd": 0, "count": 0})

    for movie_title in watched_movies:
        try:
            best_match, movie_id = find_best_match(movie_title)
            movie_idx = movies[movies["movieId"] == movie_id].index[0]
            distances, indices = nn.kneighbors(tfidf_matrix[movie_idx], n_neighbors=top_n + 1)
            print(best_match)
            for i, rec_movie_id in enumerate(movies.iloc[indices[0][1:]]["movieId"]):
                knn_score = 1 - distances[0][i+1]
                svd_score = svd_model.predict(user_id, rec_movie_id).est
                
                recommendation_scores[rec_movie_id]["knn"] += knn_score
                recommendation_scores[rec_movie_id]["svd"] += svd_score
                recommendation_scores[rec_movie_id]["count"] += 1
        except Exception as e:
            print(f"Помилка для {movie_title}: {e}")

    final_recommendations = []
    for movie_id, scores in recommendation_scores.items():
        avg_knn = scores["knn"] / scores["count"]
        avg_svd = scores["svd"] / scores["count"]
        final_score = (weight_knn * avg_knn) + (weight_svd * avg_svd)
        final_recommendations.append((movie_id, avg_knn, avg_svd, final_score))

    final_df = pd.DataFrame(final_recommendations, columns=["movieId", "knn_score", "svd_score", "final_score"])
    watched_movie_ids = set(movies[movies["title"].isin(watched_movies)]["movieId"])
    final_df = final_df[~final_df["movieId"].isin(watched_movie_ids)]
    final_df = final_df.sort_values(by="final_score", ascending=False).head(top_n)

    # Додаємо назви фільмів
    final_df = final_df.merge(movies[["movieId", "title"]], on="movieId", how="left")

    return final_df[["title", "knn_score", "svd_score", "final_score"]].to_dict(orient="records")


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Для отримання результатів у вигляді словників
    return conn

# 📌 Реєстрація користувача
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

# 📌 Логін користувача
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        access_token = create_access_token(identity=user["id"])
        return jsonify({"access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# 📌 Захищений маршрут (тільки з токеном)
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    return jsonify({"message": f"Welcome User {user_id}!"}), 200
@app.route("/user_history", methods=["GET"])
def user_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id обов'язковий"}), 400
    
    history = get_user_watch_history(user_id)
    return jsonify(history)

@app.route("/user_ratings", methods=["GET"])
def user_ratings():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id обов'язковий"}), 400
    
    ratings = get_user_ratings(user_id)
    return jsonify(ratings)


@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    user_id = data.get("user_id")
    watched_movies = data.get("watched_movies", [])

    if not user_id or not watched_movies:
        return jsonify({"error": "Необхідні user_id і watched_movies"}), 400

    recommendations = get_recommendations_for_user(user_id, watched_movies)
    return jsonify(recommendations)
@app.route("/watch", methods=["POST"])
def add_to_history():
    data = request.json
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")

    if not user_id or not movie_id:
        return jsonify({"error": "user_id і movie_id обов'язкові"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO history (userId, movieId) VALUES (?, ?)", (user_id, movie_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Фільм додано в історію переглядів!"})

@app.route("/recommend_from_db", methods=["POST"])
def recommend_from_db():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id обов'язковий"}), 400

    conn = sqlite3.connect("database.db")
    ratings_df = pd.read_sql_query("SELECT userId, movieId, rating FROM user_ratings", conn)
    conn.close()

    if ratings_df.empty:
        return jsonify({"error": "Немає оцінок у базі"}), 400

    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings_df[['userId', 'movieId', 'rating']], reader)
    trainset = data.build_full_trainset()

    with open("models/svd_model.pkl", "rb") as f:
        svd_model = pickle.load(f) #Долго

    all_movies = ratings_df["movieId"].unique()
    user_ratings = {movie_id: svd_model.predict(user_id, movie_id).est for movie_id in all_movies}
    sorted_movies = sorted(user_ratings.items(), key=lambda x: x[1], reverse=True)

    top_movies = [movies[movies["movieId"] == movie_id]["title"].values[0] for movie_id, _ in sorted_movies[:10]]

    return jsonify({"recommendations": top_movies})
# ✅ Ендпоінт для отримання рекомендацій
@app.route("/recommendations/<int:user_id>", methods=["GET"])
def recommendations(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Отримуємо фільми, які користувач переглянув
    cursor.execute("SELECT movieId FROM user_ratings WHERE userId = ?", (user_id,))
    watched_movie_ids = [row[0] for row in cursor.fetchall()]

    # Отримуємо їхні назви
    watched_movies = movies[movies["movieId"].isin(watched_movie_ids)]["title"].tolist()
    print(watched_movies)
    
    conn.close()

    if not watched_movies:
        return jsonify({"message": "Користувач не має переглянутих фільмів"}), 400

    recommendations = get_recommendations_for_user(user_id, watched_movies)
    return jsonify(recommendations)

# ✅ Ендпоінт для збереження оцінки фільму
@app.route("/rate_movie", methods=["POST"])
def rate_movie():
    data = request.get_json()
    user_id = data.get("user_id")
    movie_title = data.get("movie_title")
    rating = data.get("rating")

    if not user_id or not movie_title or not rating:
        return jsonify({"error": "Необхідно передати user_id, movie_title і rating"}), 400

    # Шукаємо ID фільму
    try:
        _, movie_id = find_best_match(movie_title)
        print(movie_id)
        print("Знайдено")
        try:
            add_movie_rating(user_id, movie_id, rating)
        
        except Exception as e:
            return jsonify({"error": f"Сталася помилка: {str(e)}"}), 500
    except:
        return jsonify({"error": "Фільм не знайдено"}), 400
    
    return jsonify({"message": "Оцінка збережена", "movie_id": int(movie_id), "rating": rating})

    
    #conn = sqlite3.connect("database.db")
    #cursor = conn.cursor()

    # Перевіряємо, чи є вже оцінка
    #cursor.execute("SELECT * FROM user_ratings WHERE userId = ? AND movieId = ?", (user_id, movie_id))
    #existing_rating = cursor.fetchone()

    #if existing_rating:
    #    cursor.execute("UPDATE user_ratings SET rating = ? WHERE userId = ? AND movieId = ?", (rating, user_id, movie_id))
    #else:
    #    cursor.execute("INSERT INTO user_ratings (userId, movieId, rating) VALUES (?, ?, ?)", (user_id, movie_id, rating))

    #conn.commit()
   # conn.close()

    

if __name__ == "__main__":
    app.run(debug=True)
# 📌 API ендпоінти
@app.route("/find_movie", methods=["POST"])
def find_movie():
    data = request.json
    movie_title = data.get("movie_title")

    if not movie_title:
        return jsonify({"error": "Введіть назву фільму"}), 400

    best_match, idx = find_best_match(movie_title)
    movie_id = movies.iloc[idx]["movieId"]

    return jsonify({"movie_id": int(movie_id), "title": best_match})
@app.route("/")
def home():
    return render_template("index.html")
# 📌 Запуск сервера
if __name__ == "__main__":
    app.run(debug=True)
