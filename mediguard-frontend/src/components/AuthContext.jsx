
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    // Check for existing session on mount
    const storedUser = localStorage.getItem('mediguard_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    try {
      // MOCK IMPLEMENTATION - In production, use Supabase
      // Supabase Integration:
      // const { data, error } = await supabase.auth.signInWithPassword({
      //   email: credentials.email,
      //   password: credentials.password,
      // });
      // const { data: profile } = await supabase.from('users').select('username').eq('id', data.user.id).single();

      // Mock user object
      const storedUsers = JSON.parse(localStorage.getItem('mediguard_mock_users') || '[]');
      const foundUser = storedUsers.find(u => u.email === credentials.email || u.phone === credentials.email);
      
      const mockUser = foundUser || {
        id: 'user_' + Math.random().toString(36).substr(2, 9),
        username: 'User' + Math.floor(Math.random() * 1000),
        email: credentials.email || credentials.phone,
        gender: 'Female', // Default mock gender
        age: 30,
        token: 'mock_jwt_token_123',
      };

      setUser(mockUser);
      localStorage.setItem('mediguard_user', JSON.stringify(mockUser));
      
      toast({
        title: "Login Successful",
        description: "Welcome back to MediGuard Bamenda.",
      });
      return true;
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Login Failed",
        description: "Please check your credentials and try again.",
      });
      return false;
    }
  };

  const signup = async (userData) => {
    try {
      // MOCK IMPLEMENTATION
      // Supabase Integration:
      // 1. Sign up user:
      // const { data, error } = await supabase.auth.signUp({
      //   email: userData.email,
      //   password: userData.password,
      // });
      // 2. Insert profile with username:
      // await supabase.from('users').insert({
      //   id: data.user.id,
      //   username: userData.username,
      //   gender: userData.gender, 
      //   age: userData.age
      // });

      const mockUser = {
        id: 'user_' + Math.random().toString(36).substr(2, 9),
        username: userData.username,
        email: userData.email || userData.phone,
        gender: userData.gender,
        age: userData.age,
        token: 'mock_jwt_token_456',
      };

      // Save to mock users list to retrieve username on login later
      const storedUsers = JSON.parse(localStorage.getItem('mediguard_mock_users') || '[]');
      storedUsers.push(mockUser);
      localStorage.setItem('mediguard_mock_users', JSON.stringify(storedUsers));

      setUser(mockUser);
      localStorage.setItem('mediguard_user', JSON.stringify(mockUser));
      
      toast({
        title: "Account Created",
        description: `Welcome to MediGuard Bamenda, ${userData.username}!`,
      });
      return true;
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Signup Failed",
        description: "There was an error creating your account.",
      });
      return false;
    }
  };

  const logout = () => {
    // Supabase Integration:
    // await supabase.auth.signOut();
    
    setUser(null);
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
