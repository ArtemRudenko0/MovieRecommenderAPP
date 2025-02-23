import axios from "axios";

const API_URL = "127.0.0.1:5000"; // Або твій бекенд

export const getMovies = async () => {
    const response = await axios.get(`/movies`);
    return response.data;
  };

export const addMovieToUser = async (userId, movieId) => {
  await axios.post(`${API_URL}/user/${userId}/add_movie`, { movieId });
};

export const removeMovieFromUser = async (userId, movieId) => {
  await axios.delete(`${API_URL}/user/${userId}/remove_movie`, { data: { movieId } });
};
export const getUserHistory = async (userId) => {
  try {
    const response = await axios.get(`/user_history?user_id=${userId}`);
    return response.data;  // ✅ У Axios потрібно використовувати `response.data`
  } catch (error) {
    console.error("Помилка отримання історії:", error.response?.data || error.message);
    throw error;
  }
};

export const removeMovieFromHistory = async (userId, movieId) => {
  await fetch(`/remove_from_history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, movie_id: movieId }),
  });
};


export const getUserRatedMovies = async (userId) => {
  try {
    const response = await axios.get(`/get_rated_movies`, {
      params: { user_id: userId },
    });
    return response.data;
  } catch (error) {
    console.error("Помилка отримання оцінених фільмів:", error);
    return [];
  }
};
// Видалити оцінку фільму
export const removeMovieRating = async (userId, movieId) => {
  await axios.post("/remove_movie_rating", { user_id: userId, movie_id: movieId });
};
