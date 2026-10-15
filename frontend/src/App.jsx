import { Route, Routes } from 'react-router-dom'
import BottomNav from './components/BottomNav.jsx'
import TopNav from './components/TopNav.jsx'
import useDevice from './hooks/useDevice.jsx'
import AuthPage from './pages/AuthPage.jsx'
import CatalogPage from './pages/CatalogPage.jsx'
import CategoryPage from './pages/CategoryPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import HomePage from './pages/HomePage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import ResultPage from './pages/ResultPage.jsx'

function AppRoutes() {
  return (
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
  )
}

export default function App() {
  const { isDesktop } = useDevice()

  if (isDesktop) {
    return (
      <div className="flex min-h-screen flex-col">
        <TopNav />
        <main className="mx-auto w-full max-w-6xl flex-1 px-8 py-8">
          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <AppRoutes />
          </div>
        </main>
        <footer className="border-t border-gray-200 py-5 text-center text-xs text-gray-500">
          EcoVision — подскажем, куда выбросить отходы
        </footer>
      </div>
    )
  }

  return (
    <div className="mx-auto min-h-screen max-w-[480px] bg-white shadow-sm">
      <main className="px-4 pt-4 pb-28">
        <AppRoutes />
      </main>
      <BottomNav />
    </div>
  )
}
