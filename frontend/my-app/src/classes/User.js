import axios from "axios";

class User {
  constructor() {
    this.userId = localStorage.getItem("userId") || null;
    this.username = localStorage.getItem("username") || null;
    this.token = localStorage.getItem("token") || null;
  }

  async login(username, password) {
    try {
      const response = await axios.post("/login", { username, password });
      console.log("Відповідь від сервера:", response.data); // Дебаг
  
      if (response.data.access_token) { // 🔥 Тепер токен є!
        this.userId = response.data.user_id;
        this.username = username;
        this.token = response.data.access_token;
  
        localStorage.setItem("userId", this.userId);
        localStorage.setItem("username", this.username);
        localStorage.setItem("token", this.token);
  
        return true;
      } else {
        console.error("Помилка: токен не отримано");
        return false;
      }
    } catch (error) {
      console.error("Помилка входу:", error);
      return false;
    }
  }


  isAuthenticated() {
    return !!this.token;
  }

  async fetchUserData() {
    if (!this.token) return null;

    try {
      const response = await axios.get(`/user/${this.userId}`, {
        headers: { Authorization: `Bearer ${this.token}` },
      });

      this.username = response.data.username;
      return response.data;
    } catch (error) {
      console.error("Не вдалося отримати дані користувача:", error);
      return null;
    }
  }
  async register(username, password) {
    try {
      const response = await axios.post("/register", { username, password });
      console.log("Відповідь від сервера:", response.data); // Дебаг
  
      if (response.data.access_token) {
        this.userId = response.data.user_id;
        this.username = username;
        this.token = response.data.access_token;
  
        localStorage.setItem("userId", this.userId);
        localStorage.setItem("username", this.username);
        localStorage.setItem("token", this.token);
  
        return true;
      } else {
        console.error("Помилка: токен не отримано");
        return false;
      }
    } catch (error) {
      console.error("Помилка реєстрації:", error);
      return false;
    }
  }
  logout() {
    this.userId = null;
    this.username = null;
    this.token = null;

    localStorage.removeItem("userId");
    localStorage.removeItem("username");
    localStorage.removeItem("token");
  }
}

const userInstance = new User();
export default userInstance;