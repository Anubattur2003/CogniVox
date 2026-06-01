import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { Meteors } from '../components/magicui/meteors';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDarkMode } = useTheme();
  const { login, loading, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [errors, setErrors] = useState({
    username: '',
    password: '',
    general: ''
  });
  const [shakeError, setShakeError] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location.state]);

  const validateUsername = (username: string) => {
    // Username should be 3-20 characters, alphanumeric and underscores only
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    return usernameRegex.test(username);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    // Clear errors when user starts typing
    if (errors[name as keyof typeof errors]) {
      setErrors({
        ...errors,
        [name]: '',
        general: ''
      });
    }

    // Clear shake effect
    setShakeError(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Reset errors
    setErrors({
      username: '',
      password: '',
      general: ''
    });

    // Validation
    const newErrors = {
      username: '',
      password: '',
      general: ''
    };

    if (!formData.username) {
      newErrors.username = 'Username is required';
    } else if (!validateUsername(formData.username)) {
      newErrors.username = 'Please enter a valid username (3-20 characters, letters, numbers, underscores only)';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    if (Object.values(newErrors).some(error => error)) {
      setErrors(newErrors);
      setShakeError(true);
      setTimeout(() => setShakeError(false), 500);
      return;
    }

    const success = await login(formData.username, formData.password);

    if (success) {
      // Redirect will be handled by useEffect when isAuthenticated changes
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    } else {
      // Show error and shake form
      setErrors({
        username: '',
        password: '',
        general: 'Invalid username or password. Please try again.'
      });
      setShakeError(true);
      setTimeout(() => setShakeError(false), 500);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 relative overflow-hidden ${
      isDarkMode ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' : 'bg-gradient-to-br from-gray-50 via-white to-gray-50'
    }`}>
      {/* Animated Background */}
      <div className="absolute inset-0 w-full h-full z-0">
        {/* Gradient Overlay */}
        <div className={`absolute inset-0 w-full h-full ${isDarkMode ? 'bg-gradient-to-br from-purple-900/20 via-transparent to-blue-900/20' : 'bg-gradient-to-br from-purple-100/30 via-transparent to-blue-100/30'}`} />
        
        {/* Meteors Effect */}
        <div className="absolute inset-0 w-full h-full">
          <Meteors 
            number={30} 
            minDelay={0.1} 
            maxDelay={3} 
            minDuration={4} 
            maxDuration={10} 
            angle={215}
            className="w-full h-full"
          />
        </div>
        
        {/* Grid Pattern */}
        <div className={`absolute inset-0 ${isDarkMode ? 'bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.03)_1px,transparent_0)]' : 'bg-[radial-gradient(circle_at_1px_1px,rgba(0,0,0,0.02)_1px,transparent_0)]'} [background-size:60px_60px]`} />
      </div>

      <div className={`relative z-10 w-full max-w-sm p-8 rounded-2xl backdrop-blur-xl border transition-all duration-300 ${
        shakeError ? 'animate-pulse' : ''
      } ${
        isDarkMode 
          ? 'bg-gray-900/10 border-white/20 shadow-2xl shadow-purple-500/20' 
          : 'bg-white/10 border-white/30 shadow-2xl shadow-black/20'
      } before:absolute before:inset-0 before:rounded-2xl before:bg-gradient-to-br before:from-white/5 before:to-transparent before:pointer-events-none`}>
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className={`text-2xl font-bold mb-1 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            Welcome Back
          </h1>
          <p className={`text-xs ${
            isDarkMode ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Sign in to your account
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* General Error */}
          {errors.general && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <p className="text-red-700 text-sm">{errors.general}</p>
              </div>
            </div>
          )}

          {/* Username Field */}
          <div>
            <label htmlFor="username" className={`block text-xs font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              autoComplete="username"
              className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                errors.username 
                  ? 'border-red-500 focus:ring-red-500' 
                  : isDarkMode 
                    ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                    : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
              }`}
              placeholder="Enter your username"
            />
            {errors.username && (
              <p className="text-red-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.username}
              </p>
            )}
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className={`block text-xs font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
              className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                errors.password 
                  ? 'border-red-500 focus:ring-red-500' 
                  : isDarkMode 
                    ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                    : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
              }`}
              placeholder="Enter your password"
            />
            {errors.password && (
              <p className="text-red-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.password}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full font-medium py-2.5 px-4 text-sm rounded-lg transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:ring-offset-2 mt-5 backdrop-blur-sm ${
              loading 
                ? 'bg-purple-400/60 cursor-not-allowed border border-purple-300/30' 
                : 'bg-gradient-to-r from-purple-600/80 to-blue-600/80 hover:from-purple-700/90 hover:to-blue-700/90 hover:transform hover:scale-[1.02] active:scale-[0.98] border border-white/20 shadow-lg shadow-purple-500/25'
            } text-white`}
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Signing In...
              </div>
            ) : (
              'Sign In'
            )}
          </button>

          {/* Sign Up Link */}
          <div className="text-center mt-4">
            <p className={`text-xs ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Don't have an account?{' '}
              <Link 
                to="/signup" 
                className="text-purple-600 hover:text-purple-500 font-medium transition-colors hover:underline"
              >
                Sign up
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login; 