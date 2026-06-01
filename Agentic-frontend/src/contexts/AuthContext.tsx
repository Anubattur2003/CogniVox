import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { toast } from "react-hot-toast";
import { API_ENDPOINTS, apiCall, verifyAuthToken } from "../services/api";

interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  signup: (userData: SignupData) => Promise<boolean>;
  logout: () => void;
  handleTokenExpiration: () => void;
  validateToken: () => Promise<boolean>;
  loading: boolean;
  isAuthenticated: boolean;
}

interface SignupData {
  firstName?: string;
  lastName?: string;
  username?: string;
  email: string;
  password: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Global token expiration handler - will be set by the Auth wrapper component
let globalTokenExpirationHandler: (() => void) | null = null;

export const setGlobalTokenExpirationHandler = (handler: () => void) => {
  globalTokenExpirationHandler = handler;
};

export const triggerGlobalTokenExpiration = () => {
  if (globalTokenExpirationHandler) {
    globalTokenExpirationHandler();
  }
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check for stored token on app load and verify it's still valid
    const storedToken = localStorage.getItem("auth_token");
    const storedUser = localStorage.getItem("user_data");

    if (storedToken && storedUser) {
      // Verify token is still valid by calling /me endpoint
      verifyToken(storedToken)
        .then((userData) => {
          if (userData) {
            setToken(storedToken);
            setUser(userData);
          } else {
            // Token is invalid, clear storage
            clearAuthData();
          }
        })
        .catch(() => {
          // Token verification failed, clear storage
          clearAuthData();
        });
    }
  }, []);

  // Periodic token validation (every 5 minutes)
  useEffect(() => {
    if (!token || !user) return;

    const validateToken = async () => {
      const isValid = await verifyAuthToken();
      if (!isValid) {
        console.log("Periodic token validation failed, triggering logout...");
        handleTokenExpiration();
      }
    };

    // Set up interval for periodic validation
    const interval = setInterval(validateToken, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [token, user]);

  // Validate token when window regains focus
  useEffect(() => {
    if (!token || !user) return;

    const handleFocus = async () => {
      console.log("Window focused, validating token...");
      const isValid = await verifyAuthToken();
      if (!isValid) {
        console.log("Token validation on focus failed, triggering logout...");
        handleTokenExpiration();
      }
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [token, user]);

  const clearAuthData = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_data");
    setUser(null);
    setToken(null);
  };

  const verifyToken = async (token: string): Promise<User | null> => {
    try {
      const response = await apiCall(API_ENDPOINTS.AUTH.ME);

      if (response.data && response.status === 200) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error("Token verification failed:", error);
      return null;
    }
  };

  const handleTokenExpiration = () => {
    console.log("Token expired, logging out user...");
    clearAuthData();
    toast.error("Your session has expired. Please log in again.");
    // The actual navigation will be handled by the Auth wrapper component
  };

  const validateTokenManually = async (): Promise<boolean> => {
    if (!token) return false;
    const isValid = await verifyAuthToken();
    if (!isValid) {
      handleTokenExpiration();
    }
    return isValid;
  };

  const login = async (
    username: string,
    password: string
  ): Promise<boolean> => {
    setLoading(true);
    try {
      console.log("Login attempt:", { username, password: "***" });
      console.log("API Endpoint:", API_ENDPOINTS.AUTH.LOGIN);

      // Django backend expects JSON format
      const requestBody = {
        username: username,
        password: password,
      };

      console.log("FormData contents:");
      console.log("username:", username);
      console.log("password:", "***");

      const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      console.log("Response status:", response.status);
      console.log(
        "Response headers:",
        Object.fromEntries(response.headers.entries())
      );

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Login error response:", errorData);
        throw new Error(errorData.detail || "Invalid credentials");
      }

      const data = await response.json();
      const { access_token, token_type } = data;

      // Store token temporarily so apiCall can use it
      localStorage.setItem("auth_token", access_token);

      // Get user info with the token
      const userResponse = await apiCall(API_ENDPOINTS.AUTH.ME);

      if (userResponse.data && userResponse.status === 200) {
        const userData = userResponse.data;
        setUser(userData);
        setToken(access_token);
        localStorage.setItem("user_data", JSON.stringify(userData));
        toast.success("Welcome back!");
        return true;
      } else {
        // Clean up token if user info fetch failed
        clearAuthData();
        throw new Error("Failed to get user information");
      }
    } catch (error) {
      console.error("Login error:", error);
      // Clean up any stored token on login failure
      clearAuthData();
      const errorMessage =
        error instanceof Error ? error.message : "Login failed";
      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (userData: SignupData): Promise<boolean> => {
    setLoading(true);
    try {
      console.log("Signup attempt:", {
        email: userData.email,
        username: userData.username,
        firstName: userData.firstName,
        lastName: userData.lastName,
        password: "***",
      });
      console.log("API Endpoint:", API_ENDPOINTS.AUTH.REGISTER);

      const requestBody = {
        email: userData.email,
        username: userData.username || userData.email, // Auto-generate from email if not provided
        password: userData.password,
        first_name: userData.firstName,
        last_name: userData.lastName,
        role: "user", // Default role (lowercase to match backend enum)
      };

      console.log("Request body:", { ...requestBody, password: "***" });

      const response = await apiCall(API_ENDPOINTS.AUTH.REGISTER, {
        method: "POST",
        body: JSON.stringify(requestBody),
      });

      console.log("Signup response:", response);

      if (
        response.data &&
        (response.status === 200 || response.status === 201)
      ) {
        toast.success("Account created successfully! Please sign in.");
        return true;
      } else {
        console.error("Signup failed:", response);
        // Handle detailed error messages from validation errors
        let errorMessage = "Registration failed";
        if (response.error) {
          if (typeof response.error === "string") {
            errorMessage = response.error;
          } else {
            // Convert object/array errors to string
            errorMessage = JSON.stringify(response.error);
          }
        }
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error("Signup error:", error);
      let errorMessage = "Registration failed";

      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === "object" && error !== null) {
        // Handle case where error is an object
        errorMessage = JSON.stringify(error);
      }

      toast.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearAuthData();
    toast.success("Logged out successfully");
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    signup,
    logout,
    loading,
    isAuthenticated: !!token && !!user,
    handleTokenExpiration,
    validateToken: validateTokenManually,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
