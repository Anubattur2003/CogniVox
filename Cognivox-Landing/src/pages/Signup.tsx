import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { Meteors } from '../components/magicui/meteors';

interface PasswordStrength {
  score: number;
  label: string;
  color: string;
  requirements: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    digit: boolean;
    special: boolean;
  };
}

const Signup = () => {
  const navigate = useNavigate();
  const { isDarkMode } = useTheme();
  const { signup, loading, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({
    firstName: '',
    lastName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    general: ''
  });
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
    score: 0,
    label: '',
    color: '',
    requirements: {
      length: false,
      uppercase: false,
      lowercase: false,
      digit: false,
      special: false,
    }
  });
  const [showPasswordStrength, setShowPasswordStrength] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateUsername = (username: string) => {
    // Username should be 3-20 characters, alphanumeric and underscores only
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    return usernameRegex.test(username);
  };

  const calculatePasswordStrength = (password: string): PasswordStrength => {
    const requirements = {
      length: password.length >= 6,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      digit: /\d/.test(password),
      special: /[^A-Za-z0-9]/.test(password),
    };

    const score = Object.values(requirements).filter(Boolean).length;
    
    let label = '';
    let color = '';

    if (score === 0) {
      label = '';
      color = '';
    } else if (score <= 2) {
      label = 'Weak';
      color = 'text-red-500';
    } else if (score <= 3) {
      label = 'Fair';
      color = 'text-yellow-500';
    } else if (score <= 4) {
      label = 'Good';
      color = 'text-blue-500';
    } else {
      label = 'Strong';
      color = 'text-green-500';
    }

    return { score, label, color, requirements };
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

    // Calculate password strength
    if (name === 'password') {
      const strength = calculatePasswordStrength(value);
      setPasswordStrength(strength);
      setShowPasswordStrength(value.length > 0);
    }

    // Validate confirm password
    if (name === 'confirmPassword' && formData.password) {
      if (value !== formData.password && value.length > 0) {
        setErrors({
          ...errors,
          confirmPassword: 'Passwords do not match',
          general: ''
        });
      }
    }

    // Auto-generate username from email if username is empty
    if (name === 'email' && !formData.username) {
      const emailUsername = value.split('@')[0].replace(/[^a-zA-Z0-9_]/g, '');
      if (emailUsername.length >= 3) {
        setFormData(prev => ({
          ...prev,
          [name]: value,
          username: emailUsername
        }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Reset errors
    setErrors({
      firstName: '',
      lastName: '',
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      general: ''
    });

    // Validation
    const newErrors = {
      firstName: '',
      lastName: '',
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      general: ''
    };

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.username) {
      newErrors.username = 'Username is required';
    } else if (!validateUsername(formData.username)) {
      newErrors.username = 'Username must be 3-20 characters (letters, numbers, underscores only)';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else {
      const strength = calculatePasswordStrength(formData.password);
      if (!strength.requirements.length) {
        newErrors.password = 'Password must be at least 6 characters long';
      } else if (!strength.requirements.uppercase) {
        newErrors.password = 'Password must contain at least one uppercase letter';
      } else if (!strength.requirements.lowercase) {
        newErrors.password = 'Password must contain at least one lowercase letter';
      } else if (!strength.requirements.digit) {
        newErrors.password = 'Password must contain at least one number';
      } else if (!strength.requirements.special) {
        newErrors.password = 'Password must contain at least one special character';
      }
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.values(newErrors).some(error => error)) {
      setErrors(newErrors);
      return;
    }

    const success = await signup({
      firstName: formData.firstName || undefined,
      lastName: formData.lastName || undefined,
      username: formData.username,
      email: formData.email,
      password: formData.password,
    });

    if (success) {
      navigate('/login');
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
        isDarkMode 
          ? 'bg-gray-900/10 border-white/20 shadow-2xl shadow-purple-500/20' 
          : 'bg-white/10 border-white/30 shadow-2xl shadow-black/20'
      } before:absolute before:inset-0 before:rounded-2xl before:bg-gradient-to-br before:from-white/5 before:to-transparent before:pointer-events-none`}>
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className={`text-2xl font-bold mb-1 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            Create Account
          </h1>
          <p className={`text-xs ${
            isDarkMode ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Sign up for a new account
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Name Fields */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="firstName" className={`block text-xs font-medium mb-1 ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                First Name
              </label>
              <input
                type="text"
                id="firstName"
                name="firstName"
                value={formData.firstName}
                onChange={handleChange}
                autoComplete="given-name"
                className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                  errors.firstName 
                    ? 'border-red-500 focus:ring-red-500' 
                    : isDarkMode 
                      ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                      : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
                }`}
                placeholder="First name"
              />
            </div>

            <div>
              <label htmlFor="lastName" className={`block text-xs font-medium mb-1 ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Last Name
              </label>
              <input
                type="text"
                id="lastName"
                name="lastName"
                value={formData.lastName}
                onChange={handleChange}
                autoComplete="family-name"
                className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                  errors.lastName 
                    ? 'border-red-500 focus:ring-red-500' 
                    : isDarkMode 
                      ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                      : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
                }`}
                placeholder="Last name"
              />
            </div>
          </div>

          {/* Email Field */}
          <div>
            <label htmlFor="email" className={`block text-xs font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              autoComplete="email"
              className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                errors.email 
                  ? 'border-red-500 focus:ring-red-500' 
                  : isDarkMode 
                    ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                    : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
              }`}
              placeholder="Enter your email"
            />
            {errors.email && (
              <p className="text-red-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.email}
              </p>
            )}
          </div>

          {/* Username Field */}
          <div>
            <label htmlFor="username" className={`block text-xs font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Username *
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
              placeholder="Choose a username"
            />
            {errors.username && (
              <p className="text-red-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.username}
              </p>
            )}
            {formData.username && !errors.username && validateUsername(formData.username) && (
              <p className="text-green-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Username looks good!
              </p>
            )}
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className={`block text-xs font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Password *
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="new-password"
              className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                errors.password 
                  ? 'border-red-500 focus:ring-red-500' 
                  : isDarkMode 
                    ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                    : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
              }`}
              placeholder="Create a password"
            />
            
            {/* Password Strength Indicator */}
            {showPasswordStrength && (
              <div className="mt-2">
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-medium ${passwordStrength.color}`}>
                    {passwordStrength.label}
                  </span>
                  <span className="text-xs text-gray-500">
                    {passwordStrength.score}/5
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                  <div 
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      passwordStrength.score === 0 ? 'bg-gray-300' :
                      passwordStrength.score <= 2 ? 'bg-red-500' :
                      passwordStrength.score <= 3 ? 'bg-yellow-500' :
                      passwordStrength.score <= 4 ? 'bg-blue-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                  ></div>
                </div>
                <div className="grid grid-cols-2 gap-1 text-xs">
                  {Object.entries(passwordStrength.requirements).map(([key, met]) => (
                    <div key={key} className={`flex items-center ${met ? 'text-green-500' : 'text-gray-400'}`}>
                      <svg className={`w-3 h-3 mr-1 ${met ? 'text-green-500' : 'text-gray-400'}`} fill="currentColor" viewBox="0 0 20 20">
                        {met ? (
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        ) : (
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        )}
                      </svg>
                      <span>
                        {key === 'length' ? '6+ chars' :
                         key === 'uppercase' ? 'Uppercase' :
                         key === 'lowercase' ? 'Lowercase' :
                         key === 'digit' ? 'Number' : 'Special'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {errors.password && (
              <p className="text-red-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.password}
              </p>
            )}
          </div>

          {/* Confirm Password Field */}
          <div>
            <label htmlFor="confirmPassword" className={`block text-xs font-medium mb-1 ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Confirm Password *
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              autoComplete="new-password"
              className={`w-full px-3 py-2 text-sm rounded-lg border transition-all duration-200 focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 backdrop-blur-sm ${
                errors.confirmPassword 
                  ? 'border-red-500 focus:ring-red-500' 
                  : formData.confirmPassword && formData.confirmPassword === formData.password
                    ? 'border-green-500 focus:ring-green-500'
                    : isDarkMode 
                      ? 'bg-white/5 border-white/10 text-white placeholder-gray-400 hover:bg-white/10 hover:border-white/20' 
                      : 'bg-white/30 border-white/30 text-gray-900 placeholder-gray-600 hover:bg-white/40 hover:border-white/40'
              }`}
              placeholder="Confirm your password"
            />
            {errors.confirmPassword && (
              <p className="text-red-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.confirmPassword}
              </p>
            )}
            {formData.confirmPassword && formData.confirmPassword === formData.password && (
              <p className="text-green-500 text-xs mt-1 flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Passwords match
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
                Creating Account...
              </div>
            ) : (
              'Sign Up'
            )}
          </button>

          {/* Sign In Link */}
          <div className="text-center mt-4">
            <p className={`text-xs ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Already have an account?{' '}
              <Link 
                to="/login" 
                className="text-purple-600 hover:text-purple-500 font-medium transition-colors hover:underline"
              >
                Sign in
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Signup; 