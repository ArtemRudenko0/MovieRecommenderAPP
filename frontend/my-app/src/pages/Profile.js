import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getUserHistory, removeMovieFromHistory, getUserRatedMovies, removeMovieRating } from "../api";
import User from "../classes/User.js"; // Імпортуємо клас User

const Profile = () => {
  const [history, setHistory] = useState([]);
  const [ratedMovies, setRatedMovies] = useState([]);
  const navigate = useNavigate();
  useEffect(() => {
    if (!User.isAuthenticated()) return;

    getUserHistory(User.userId)
      .then(setHistory)
      .catch((error) => console.error("Помилка отримання історії:", error));

    getUserRatedMovies(User.userId)
      .then(setRatedMovies)
      .catch((error) => console.error("Помилка отримання оцінених фільмів:", error));
  }, []);

  const handleRemoveHistory = async (movieId) => {
    if (!User.isAuthenticated()) return;
    try {
      await removeMovieFromHistory(User.userId, movieId);
      setHistory((prevHistory) => prevHistory.filter((movie) => movie.movieId !== movieId));
    } catch (error) {
      console.error("Помилка видалення фільму з історії:", error);
    }
  };

  const handleRemoveRatedMovie = async (movieId) => {
    if (!User.isAuthenticated()) return;
    try {
      await removeMovieRating(User.userId, movieId);
      setRatedMovies((prevRatedMovies) => prevRatedMovies.filter((movie) => movie.movieId !== movieId));
    } catch (error) {
      console.error("Помилка видалення оцінки:", error);
    }
  };
  const handleLoginRedirect = () => {
    navigate("/login"); // Перехід на сторінку логіну
};
  

  return (
    <div>
      <h1>Профіль</h1>
      {User.isAuthenticated ? (
        <>
          
          <h2>Переглянуті фільми</h2>
          {history.length === 0 ? (
            <p>Немає переглянутих фільмів</p>
          ) : (
            history.map((movie) => (
              <div key={movie.movieId}>
                <span>{movie.title}</span>
                <button onClick={() => handleRemoveHistory(movie.movieId)}>❌ Видалити</button>
              </div>
            ))
          )}

          <h2>Оцінені фільми</h2>
          {ratedMovies.length === 0 ? (
            <p>Немає оцінених фільмів</p>
          ) : (
            ratedMovies.map((movie) => (
              <div key={movie.movieId}>
                <span>
                  {movie.title} - Оцінка: {movie.rating}
                </span>
                <button onClick={() => handleRemoveRatedMovie(movie.movieId)}>❌ Видалити</button>
              </div>
            ))
          )}
        </>
      ) : (
        <button onClick={handleLoginRedirect}>Увійти</button>
      )}
    </div>
  );
};


export default Profile;