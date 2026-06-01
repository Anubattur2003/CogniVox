import React from "react";
import { useAuth } from "../../contexts/AuthContext";
import AnimatedAvatar from "../AnimatedAvatar/AnimatedAvatar";
interface HeaderProps {
  toggleSidebar: () => void;
  isOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ toggleSidebar, isOpen }) => {
  const { user } = useAuth();
  
  return (
    <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
      <div className="flex items-center">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold">P</span>
          </div>
          <h1 className="text-xl font-bold ml-2">Cognivox</h1>
        </div>
      </div>
      <div className="flex items-center">
        <button onClick={toggleSidebar} className="p-2 bg-gray-700 rounded">
          {isOpen ? "✖" : "☰"}
        </button>
        <div className="ml-4 flex items-center">
          <AnimatedAvatar 
            name={user?.firstName || user?.username || 'User'} 
            size="md" 
          />
          <div className="ml-2">
            <span className="block text-sm font-semibold">
              {user?.firstName && user?.lastName 
                ? `${user.firstName} ${user.lastName}` 
                : user?.username || 'User'}
            </span>
            <span className="block text-xs text-gray-300">
              {user?.email || 'user@example.com'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
