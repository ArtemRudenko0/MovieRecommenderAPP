import { BrowserRouter as Router, Route, Routes, Link, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Profile from "./pages/Profile.js";
import RateMovie from "./pages/RateMovie.js";
import Recommendations from "./pages/Recommendations.js";
import Login from "./pages/Login.js";
import userInstance from "./classes/User"; // Імпортуємо екземпляр User
import Register from "./pages/Register";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(userInstance.isAuthenticated());

  useEffect(() => {
    setIsAuthenticated(userInstance.isAuthenticated());
  }, []);

  const handleLogout = () => {
    userInstance.logout(); // Очищаємо користувача правильно
    setIsAuthenticated(false);
  };
  return (
    <Router>
      {/* Кнопка входу / виходу в лівому верхньому кутку */}
      <div className="fixed top-2 left-2">
        {isAuthenticated ? (
          <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded">
            Вийти
          </button>
        ) : (
          <Link to="/login" className="bg-blue-500 text-white px-4 py-2 rounded">
            Увійти
          </Link>
        )}
      </div>

      <nav>
        <Link to="/rate-movie">Оцінити фільм</Link> | 
        <Link to="/recommendations">Рекомендації</Link> |
        <Link to="/profile">Профіль</Link>
      </nav>

      <Routes>
        {/* Головна сторінка: якщо авторизований → профіль, інакше логін */}
        <Route path="/" element={isAuthenticated ? <Navigate to="/profile" replace /> : <Navigate to="/login" replace />} />
        <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated} />} />
        <Route path="/rate-movie" element={isAuthenticated ? <RateMovie /> : <Navigate to="/login" replace />} />
        <Route path="/recommendations" element={isAuthenticated ? <Recommendations /> : <Navigate to="/login" replace />} />
        <Route path="/profile" element={isAuthenticated ? <Profile /> : <Navigate to="/login" replace />} />
        <Route path="/register" element={<Register setIsAuthenticated={setIsAuthenticated} />} />
      </Routes>
    </Router>
  );
}

export default App;