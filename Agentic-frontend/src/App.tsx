import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from "./contexts/ThemeContext";
import { SidebarProvider } from "./contexts/SidebarContext";
import { AuthProvider } from "./contexts/AuthContext";
import { SettingsProvider } from "./contexts/SettingsContext";
import { SpaceProvider } from "./contexts/SpaceContext";
import AuthWrapper from "./components/AuthWrapper";
import Layout from "./Layout";
import Home from "./components/pages/Home/Home";
import Thread from "./components/pages/Thread/Thread";
import Chat from "./components/pages/Chat/Chat";
import LandingPage from "./pages/LandingPage/LandingPage";
import Login from "./pages/LandingPage/Login/Login";
import Signup from "./pages/LandingPage/Signup/Signup";
import Discover from "./components/pages/Discover/Discover";
import Library from "./components/pages/Library/Library";
import Profile from "./components/pages/Profile/Profile";
import Settings from "./components/pages/Settings/Settings";
import ProtectedRoute from "./components/ProtectedRoute";

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <SpaceProvider>
          <SettingsProvider>
            <SidebarProvider>
              <AuthWrapper>
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
              }}
            />
            <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
            {/* Protected routes wrapped in Layout */}
            <Route path="/home" element={
              <ProtectedRoute>
                <Layout>
                  <Home />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/discover" element={
              <ProtectedRoute>
                <Layout>
                  <Discover />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/library" element={
              <ProtectedRoute>
                <Layout>
                  <Library />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <Layout>
                  <Profile />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Layout>
                  <Settings />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/thread/:id" element={
              <ProtectedRoute>
                <Layout>
                  <Thread />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/chat" element={
              <ProtectedRoute>
                <Layout>
                  <Chat />
                </Layout>
              </ProtectedRoute>
            } />
            
            {/* Redirect any unknown routes to landing page */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
              </AuthWrapper>
            </SidebarProvider>
          </SettingsProvider>
        </SpaceProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
