from flask import Flask, request, jsonify, render_template
import pandas as pd
import pickle
import numpy as np

from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from surprise import SVD, Dataset, Reader
import sqlite3
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_user_watch_history, get_user_ratings, add_movie_rating, login_user, register_user, add_movie_to_history # Імпортуємо з db.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
app.config["JWT_SECRET_KEY"] = "supersecretkey"  # Замініть на безпечний ключ
jwt = JWTManager(app)
#  Завантаження моделей та даних при старті
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


#  Векторизація назв фільмів для швидкого пошуку
vectorizer = TfidfVectorizer(stop_words="english")
title_matrix = vectorizer.fit_transform(movies["title"].fillna(""))
#user_mean_ratings = ratings.groupby("userId")["rating"].mean().to_dict()
print("✅ Дані та моделі завантажені!")
# Тест реєстрації та входу
# Реєстрація та вхід користувача
register_user("user3", "pass123")
#ser_id = login_user("user2", "pass123")
#if user_id:
   # print(f"🔹 Успішний вхід! Ваш ID: {user_id}")

    # Додаємо оцінки фільмів
   
    #add_movie_rating(user_id, 85020, 5.0)
    #add_movie_rating(user_id, 5574, 5.0) 
    #add_movie_rating(user_id, 47200, 5.0) 
    
#else:
   # print(" Вхід не вдався.")

def find_best_match(movie_title):
    input_vector = vectorizer.transform([movie_title])
    similarities = cosine_similarity(input_vector, title_matrix).flatten()
    best_match_idx = np.argmax(similarities)
    best_match_title = movies.iloc[best_match_idx]["title"]
    best_match_id = movies.iloc[best_match_idx]["movieId"]
    return best_match_title, best_match_id
def find_best_matches(movie_title, top_n=10):
    input_vector = vectorizer.transform([movie_title])
    similarities = cosine_similarity(input_vector, title_matrix).flatten()

    # Отримуємо індекси фільмів, у яких схожість > 0
    best_match_indices = np.argsort(similarities)[-top_n:][::-1]
    
    results = []
    for idx in best_match_indices:
        similarity_score = float(similarities[idx])
        if similarity_score > 0:  # Фільтруємо нульові значення
            results.append({
                "movie_id": int(movies.iloc[idx]["movieId"]),
                "title": movies.iloc[idx]["title"],
                "similarity": similarity_score
            })

    return results
  
#  Функція для отримання рекомендацій
def get_recommendations_for_user(user_id, watched_movies, top_n=20, weight_knn=0.8, weight_svd=0.2):
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

  # Додаємо назву, жанр та опис фільму
    final_df = final_df.merge(movies[["movieId", "title", "genres", "overview"]], on="movieId", how="left")
    # ЗМІНЕНО
    return final_df[["title", "genres", "overview", "svd_score"]].to_dict(orient="records")


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Для отримання результатів у вигляді словників
    return conn

#  Реєстрація користувача
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user_id = register_user(username, password)

    if user_id:
        access_token = create_access_token(identity=int(user_id))  # Генеруємо токен для нового користувача
        return jsonify({
            "message": "User registered successfully!",
            "access_token": access_token,
            "user_id": user_id
        }), 201
    else:
        return jsonify({"error": "Username already exists"}), 400
    
#  Логін користувача
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    print(password)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id,  password_hash FROM users WHERE username = ?", (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    user_id, hashed_password = user[:2] # розпаковка кортежу
    print(hashed_password)
    hashed_test = generate_password_hash(password, method='pbkdf2:sha256' )
    print(hashed_test)
    # Перевірка, чи є хеш пароля
    if not hashed_password:
        return jsonify({"error": "Invalid password hash"}), 500  # Повертаємо помилку сервера

    if check_password_hash(hashed_password, password):

        access_token = create_access_token(identity=int(user_id))
        return jsonify({"message": "Login successful", "user_id": user_id, "access_token": access_token})
    else:
        return jsonify({"error": "Invalid password"}), 401  


#  Захищений маршрут (тільки з токеном)
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    return jsonify({"message": f"Welcome User {user_id}!" , }), 200
@app.route("/user_history", methods=["GET"])
def user_history():
    user_id = request.args.get("user_id")  # Отримуємо user_id з параметра запиту
    if not user_id:
        return jsonify({"error": "user_id обов'язковий"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "user_id має бути числом"}), 400
    try:
        history = get_user_watch_history(user_id)
        return jsonify(history)
    except Exception as e:
        import traceback
        print(f"Помилка отримання історії:\n{traceback.format_exc()}")
        return jsonify({"error": f"Помилка сервера: {str(e)}"}), 500


@app.route("/remove_from_history", methods=["POST"])
def remove_from_history():
    data = request.json
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")

    if not user_id or not movie_id:
        return jsonify({"error": "user_id і movie_id обов'язкові"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE userId = ? AND movieId = ?", (user_id, movie_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Фільм видалено з історії"}), 200

@app.route("/add_to_history", methods=["POST"])
def add_to_history():
    data = request.json
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")

    if not user_id or not movie_id:
        return jsonify({"error": "user_id і movie_id обов'язкові"}), 400

    try:
        response = add_movie_to_history(user_id, movie_id)
        return jsonify(response)
    except Exception as e:
        import traceback
        print(f"Помилка додавання до історії:\n{traceback.format_exc()}")
        return jsonify({"error": f"Помилка сервера: {str(e)}"}), 500

#  Ендпоінт для отримання рекомендацій
@app.route("/recommendations", methods=["GET"])
def recommendations():
   
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    user_id = request.args.get("user_id")  # Отримуємо user_id з параметра запиту
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

@app.route("/rate_movie", methods=["POST"])
def rate_movie():
    data = request.get_json()
    user_id = data.get("user_id")
    movie_id = data.get("movie_id")  # Змінено на movie_id
    rating = data.get("rating")

    if not user_id or not movie_id or not rating:
        return jsonify({"error": "Необхідно передати user_id, movie_id і rating"}), 400

    try:
        add_movie_rating(user_id, movie_id, rating)
    except Exception as e:
        return jsonify({"error": f"Сталася помилка: {str(e)}"}), 500

    return jsonify({"message": "Оцінка збережена", "movie_id": int(movie_id), "rating": rating})

@app.route("/get_rated_movies", methods=["GET"])
def user_ratings():
    user_id = request.args.get("user_id")  # Ось тут важливо!
    
    if not user_id:
        return jsonify({"error": "user_id обов'язковий"}), 400
    
    ratings = get_user_ratings(user_id)
    return jsonify(ratings)

@app.route("/remove_movie_rating", methods=["POST"])
def remove_movie_rating():
    data = request.json
    user_id = data["user_id"]
    movie_id = data["movie_id"]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_ratings WHERE userId = ? AND movieId = ?", (user_id, movie_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Оцінку видалено"})



# API ендпоінти
@app.route("/find_movie", methods=["POST"])
def find_movie():

    data = request.json
    movie_title = data.get("movie_title")

    if not movie_title:
        return jsonify({"error": "Введіть назву фільму"}), 400

    best_matches = find_best_matches(movie_title, top_n=10)

    return jsonify({"movies": best_matches})






if __name__ == "__main__":
    app.run(debug=True)

