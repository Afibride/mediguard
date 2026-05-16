
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { getMe, login as loginRequest, register as registerRequest } from '@/services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const storedUser = localStorage.getItem('mediguard_user');
    const token = localStorage.getItem('mediguard_token');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }

    if (token) {
      getMe()
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('mediguard_user', JSON.stringify(res.data));
        })
        .catch(() => {
          localStorage.removeItem('mediguard_token');
          localStorage.removeItem('mediguard_user');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (credentials) => {
    try {
      const email = credentials.email || credentials.phone;
      const res = await loginRequest({ email, password: credentials.password });
      localStorage.setItem('mediguard_token', res.data.access_token);
      localStorage.setItem('mediguard_user', JSON.stringify(res.data.user));
      setUser(res.data.user);
      
      toast({
        title: "Login Successful",
        description: "Welcome back to MediGuard Bamenda.",
      });
      return true;
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Login Failed",
        description: error.message || "Please check your credentials and try again.",
      });
      return false;
    }
  };

  const signup = async (userData) => {
    try {
      const email = userData.email || userData.phone;
      const res = await registerRequest({
        email,
        password: userData.password,
        full_name: userData.username,
        username: userData.username,
      });

      localStorage.setItem('mediguard_token', res.data.access_token);
      localStorage.setItem('mediguard_user', JSON.stringify(res.data.user));
      setUser(res.data.user);
      
      toast({
        title: "Account Created",
        description: `Welcome to MediGuard Bamenda, ${userData.username}!`,
      });
      return true;
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Signup Failed",
        description: error.message || "There was an error creating your account.",
      });
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('mediguard_token');
    localStorage.removeItem('mediguard_user');
    toast({
      title: "Logged Out",
      description: "You have been successfully logged out.",
    });
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
