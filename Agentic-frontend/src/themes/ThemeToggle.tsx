// import React from 'react';
import { Sun, Moon } from 'lucide-react';

interface ThemeToggleProps {
  isDark: boolean;
  onToggle: () => void;
}

export default function ThemeToggle({ isDark, onToggle }: ThemeToggleProps) {
  return (
    <button
      onClick={onToggle}
      className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-200 transition-colors"
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun className="w-6 h-6 text-gray-200" />
      ) : (
        <Moon className="w-6 h-6 text-gray-700" />
      )}
    </button>
  );
}