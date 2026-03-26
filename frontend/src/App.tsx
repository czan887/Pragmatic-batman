import { Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Profiles from './pages/Profiles';
import Tasks from './pages/Tasks';
import Stats from './pages/Stats';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import UserActions from './pages/UserActions';
import PostActions from './pages/PostActions';
import HashtagActions from './pages/HashtagActions';
import AccountActions from './pages/AccountActions';
import Bot from './pages/Bot';

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="profiles" element={<Profiles />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="stats" element={<Stats />} />
          <Route path="user-actions" element={<UserActions />} />
          <Route path="post-actions" element={<PostActions />} />
          <Route path="hashtag-actions" element={<HashtagActions />} />
          <Route path="account-actions" element={<AccountActions />} />
          <Route path="bot" element={<Bot />} />
          <Route path="logs" element={<Logs />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
