import { Navigate, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import HealthProfile from "./pages/HealthProfile";
import Dashboard from "./pages/Dashboard";
import FoodDiary from "./pages/FoodDiary";
import LabResults from "./pages/LabResults";
import Assessment from "./pages/Assessment";
import Profile from "./pages/Profile";
import MealPlan from "./pages/MealPlan";
import Progress from "./pages/Progress";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/health-profile" element={<HealthProfile />} />
      <Route path="/onboarding" element={<Navigate to="/health-profile" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/food-diary" element={<FoodDiary />} />
      <Route path="/lab-results" element={<LabResults />} />
      <Route path="/assessment" element={<Assessment />} />
      <Route path="/meal-plan" element={<MealPlan />} />
      <Route path="/progress" element={<Progress />} />
      <Route path="/profile" element={<Profile />} />
    </Routes>
  );
}

export default App;
