import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import './index.css';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    // Check if user has a preference saved in localStorage
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // Save dark mode preference
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    
    // Apply dark mode class to document
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <Dashboard darkMode={darkMode} onToggleDarkMode={toggleDarkMode} />
    </div>
  );
}

export default App;