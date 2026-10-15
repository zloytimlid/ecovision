import { Route, Routes } from 'react-router-dom'
import BottomNav from './components/BottomNav.jsx'
import AuthPage from './pages/AuthPage.jsx'
import CatalogPage from './pages/CatalogPage.jsx'
import CategoryPage from './pages/CategoryPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import HomePage from './pages/HomePage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import ResultPage from './pages/ResultPage.jsx'

export default function App() {
  return (
    <div className="mx-auto min-h-screen max-w-[480px] bg-white shadow-sm">
      <main className="px-4 pt-4 pb-28">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/result/:id" element={<ResultPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/catalog/:slug" element={<CategoryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  )
}
