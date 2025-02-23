import { useState } from "react";
import axios from "axios";
import userInstance from "../classes/User.js"; // Імпортуємо клас User
function RateMovie() {
  const [movieTitle, setMovieTitle] = useState("");
  const [foundMovies, setFoundMovies] = useState([]); // Масив знайдених фільмів
  const [ratings, setRatings] = useState({});

  const [message, setMessage] = useState("");

  const searchMovie = async () => {
    try {
      const response = await axios.post("/find_movie", { movie_title: movieTitle });
      setFoundMovies(response.data.movies); // Отримуємо список фільмів
      setMessage("");
    } catch (error) {
      setMessage("Фільм не знайдено");
      setFoundMovies([]);
    }
  };

  const rateMovie = async (movieId, title) => {
    if (!userInstance.isAuthenticated()) {
      setMessage("Будь ласка, увійдіть у систему");
      return;
    }
  
    const ratingValue = parseFloat(ratings[movieId]);
    if (!ratingValue || ratingValue < 0.5 || ratingValue > 5) {
      setMessage("Будь ласка, введіть коректну оцінку (0.5 - 5)");
      return;
    }
  
    try {
      await axios.post(
        "/rate_movie",
        {
          user_id: userInstance.userId,
          movie_id: movieId,
          rating: ratingValue,
        },
        { headers: { Authorization: `Bearer ${userInstance.token}` } }
      );
      setMessage(`Оцінка для "${title}" збережена!`);
    } catch (error) {
      setMessage("Помилка при збереженні оцінки");
    }
  };
  
  const add_to_history = async (movieId, title) => {
    if (!userInstance.isAuthenticated()) {
      setMessage("Будь ласка, увійдіть у систему");
      return;
    }
    try {
      const response = await axios.post("/add_to_history", {
        user_id: userInstance.userId,
        movie_id: movieId,
      });

      console.log("Відповідь від бекенду:", response.data);

      //if (response.data.status === "exists") {
        setMessage(response.data.message);
       //alert("Фільм уже є у вашій історії переглядів!");
      //} else if (response.data.status === "added") {
      //  setMessage(response.data.message);
      //}
    } catch (error) {
      console.error("Помилка додавання в історію:", error);
      setMessage("Помилка при збереженні фільму в історію.");
    }
};
  
  return (
    <div>
      <h2>Оцінити фільм</h2>
      <input
        type="text"
        placeholder="Введіть назву фільму"
        value={movieTitle}
        onChange={(e) => setMovieTitle(e.target.value)}
      />
      <button onClick={searchMovie}>Знайти</button>

      {foundMovies.length > 0 && (
        <ul>
          {foundMovies.map((movie) => (
            <li key={movie.movie_id} style={{ marginBottom: "10px" }}>
              <span>{movie.title}</span>
              <input
                type="number"
                min="0.5"
                max="5"
                step="0.5"
                value={ratings[movie.movie_id] || ""}
                onChange={(e) => setRatings({ ...ratings, [movie.movie_id]: e.target.value })}
                style={{ marginLeft: "10px" }}
              />
              <button onClick={() => rateMovie(movie.movie_id, movie.title)} style={{ marginLeft: "10px" }}>
                Оцінити
              </button>
              <button onClick={() => add_to_history(movie.movie_id, movie.title)} style = {{ marginLeft: "10px"}}>
                Переглянуто
              </button>
            </li>
          ))}
           
        </ul>
      )}

      {message && <p>{message}</p>}
    </div>
  );
}

export default RateMovie;