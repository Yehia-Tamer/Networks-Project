import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import Login from "./auth/Login";
import Register from "./auth/Register";
import MetricsPage from "./metrics/MetricsPage";
// Teammates plug their screens in here:
// import ChatList from "./chats/ChatList";   // Gelan
// import ChatWindow from "./chat/ChatWindow"; // Maryam

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/metrics" element={<RequireAuth><MetricsPage /></RequireAuth>} />
          {/* <Route path="/" element={<RequireAuth><ChatList /></RequireAuth>} /> */}
          {/* <Route path="/chat/:groupId" element={<RequireAuth><ChatWindow /></RequireAuth>} /> */}
          <Route path="*" element={<Navigate to="/metrics" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
