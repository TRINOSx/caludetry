import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ParcelaDetailPage from './pages/ParcelaDetailPage';
import SensorsPage from './pages/SensorsPage';
import InsightsPage from './pages/InsightsPage';
import BillingPage from './pages/BillingPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/parcela/:id" element={<ParcelaDetailPage />} />
        <Route path="/sensors" element={<SensorsPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
