import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import HealthProfile from "./pages/HealthProfile";
import Dashboard from "./pages/Dashboard";
import FoodDiary from "./pages/FoodDiary";
import LabResults from "./pages/LabResults";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/health-profile" element={<HealthProfile />} />
      <Route path="/onboarding" element={<Navigate to="/health-profile" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/food-diary" element={<FoodDiary />} />
      <Route path="/lab-results" element={<LabResults />} />
      <Route path="/profile" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
