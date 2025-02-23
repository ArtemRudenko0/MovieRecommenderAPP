import { useState } from "react";
import axios from "axios";
import User from "../classes/User.js"; // Імпортуємо клас User

function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [message, setMessage] = useState("");

  const fetchRecommendations = async () => {
    if (!User.isAuthenticated()) {
      setMessage("Будь ласка, увійдіть у систему");
      return;
    }
  
    try {
      const response = await axios.get(`/recommendations?user_id=${User.userId}`, {
        headers: { Authorization: `Bearer ${User.token}` },
      });
  
      setRecommendations(response.data);
      setMessage("");
    } catch (error) {
      setMessage("Не вдалося отримати рекомендації");
      setRecommendations([]);
    }
  };

  return (
    <div>
      <h2>Рекомендовані фільми</h2>
      <button onClick={fetchRecommendations}>Отримати рекомендації</button>

      {message && <p>{message}</p>}

      {recommendations.length > 0 && (
        <ul>
          {recommendations.map((movie, index) => (
            <li key={index}>
              <strong>{movie.title}</strong> 
              <strong>🔹 Жанри: {movie.genres}</strong>
              <strong>🔹 Передісторія: {movie.overview}</strong>
              <p>⭐ Оцінка від інших користувачів: {movie.svd_score.toFixed(2)}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default Recommendations;