import React, { useState, useRef, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Send, Bot, User, Loader2, RefreshCw, AlertCircle, 
  Menu, Plus, MessageSquare, ChevronLeft, Trash2, X,
  PanelLeftClose, PanelLeftOpen
} from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';
import SuggestedQuestions from '@/components/SuggestedQuestions';

const ChatAI = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const location = useLocation();
  const scrollRef = useRef(null);
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);

  // Check screen size for responsive behavior
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setIsSidebarOpen(true);
      } else {
        setIsSidebarOpen(false);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Initialize with a default chat only if no chats exist
  useEffect(() => {
    if (chats.length === 0) {
      createNewChat();
    }
  }, []);

  // Load messages for current chat
  useEffect(() => {
    if (currentChatId) {
      const currentChat = chats.find(chat => chat.id === currentChatId);
      if (currentChat) {
        setMessages(currentChat.messages);
      }
    }
  }, [currentChatId, chats]);

  // If navigated from PredictionResults with state
  useEffect(() => {
    if (location.state?.initialMessage && messages.length === 0 && currentChatId) {
      handleSend(location.state.initialMessage, true);
    }
  }, [location.state, currentChatId]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Create a new chat
  const createNewChat = () => {
    // Don't create a new chat if there are no existing chats
    // This ensures we don't create duplicate chats on initial load
    if (chats.length === 0 || currentChatId) {
      const newChatId = 'chat_' + Date.now();
      const welcomeMessage = {
        role: 'assistant',
        content: 'Hello! I am your MediGuard AI health assistant. How are you feeling today? Please describe your symptoms.',
        id: 'msg_' + Date.now(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      const newChat = {
        id: newChatId,
        title: 'New Conversation',
        messages: [welcomeMessage],
        createdAt: new Date().toISOString(),
        preview: welcomeMessage.content.substring(0, 30) + '...'
      };

      setChats(prev => [newChat, ...prev]);
      setCurrentChatId(newChatId);
      setMessages([welcomeMessage]);
      
      if (isMobile) {
        setIsSidebarOpen(false);
      }
    }
  };

  // Update chat title based on user's questions
  const updateChatTitle = (chatId, userMessage) => {
    setChats(prev => prev.map(chat => {
      if (chat.id === chatId) {
        // Create a more meaningful title from the user's question
        let title = userMessage;
        
        // Clean up the message to make a better title
        if (userMessage.length > 40) {
          title = userMessage.substring(0, 40) + '...';
        }
        
        // Capitalize first letter
        title = title.charAt(0).toUpperCase() + title.slice(1);
        
        return { ...chat, title };
      }
      return chat;
    }));
  };

  // Handle message sending
  const handleSend = (textOverride = null, isInitial = false) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim()) return;

    const userMsgObj = { 
      role: 'user', 
      content: textToSend, 
      id: 'msg_user_' + Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    // Update messages
    const updatedMessages = [...messages, userMsgObj];
    setMessages(updatedMessages);
    
    // Update chat in sidebar
    setChats(prev => prev.map(chat => {
      if (chat.id === currentChatId) {
        // If this is the first user message, update the chat title with the question
        if (chat.title === 'New Conversation') {
          updateChatTitle(chat.id, textToSend);
        }
        
        // Update messages and preview
        return { 
          ...chat, 
          messages: updatedMessages,
          preview: textToSend.substring(0, 30) + '...'
        };
      }
      return chat;
    }));

    setInput('');
    setIsTyping(true);

    // Mock AI Processing Delay
    setTimeout(() => {
      let aiResponseContent = "";
      const lowerText = textToSend.toLowerCase();

      // Mock AI Logic Flow based on keywords
      if (lowerText.includes('fever') && lowerText.includes('cough')) {
        aiResponseContent = "I understand you have a fever and a cough. To help me analyze better, could you tell me how many days you've been experiencing these symptoms? Are you also feeling any chest pain or shortness of breath?";
      } 
      else if (lowerText.includes('stomach') || lowerText.includes('pain')) {
        aiResponseContent = "Stomach pain can have various causes. Is the pain sharp or dull? Are you also experiencing nausea, vomiting, or diarrhea?";
      }
      else if (lowerText.includes('rash')) {
        aiResponseContent = "A rash can be a sign of an allergic reaction or an infection. Is the rash itchy, red, or spreading? Have you tried any new foods or medications recently?";
      }
      else if (lowerText.includes('emergency') || lowerText.includes('bleeding') || lowerText.includes('breath')) {
        aiResponseContent = "🚨 EMERGENCY ALERT: Your symptoms suggest a potentially critical condition. Please stop this chat and seek immediate emergency medical care or call local emergency services right away.";
      }
      else if (lowerText.includes('days') || lowerText.includes('week') || lowerText.includes('no ')) {
        aiResponseContent = "Thank you for the additional information. Based on what you've shared, this could be related to a common seasonal infection like Malaria or a Respiratory Infection. I highly recommend using our 'Symptom Checker' for a detailed analysis or visiting a doctor for a proper clinical diagnosis. Ensure you stay hydrated and rest.";
      }
      else if (isInitial) {
        aiResponseContent = "I see you're coming from your diagnosis results. I can help clarify any terms or explain the home care recommendations. What specific part of the diagnosis would you like to discuss?";
      }
      else {
        aiResponseContent = "I hear you. Could you provide a bit more detail about when this started and if you have any other unusual feelings? The more details you provide, the better I can assist.";
      }

      const aiMsgObj = { 
        role: 'assistant', 
        content: aiResponseContent,
        id: 'msg_ai_' + Date.now(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      const finalMessages = [...updatedMessages, aiMsgObj];
      setMessages(finalMessages);
      
      // Update chat with AI response
      setChats(prev => prev.map(chat => {
        if (chat.id === currentChatId) {
          return { 
            ...chat, 
            messages: finalMessages,
            preview: aiResponseContent.substring(0, 30) + '...'
          };
        }
        return chat;
      }));

      setIsTyping(false);
    }, 1500);
  };

  const handleSelectQuestion = (question) => {
    handleSend(question);
  };

  const clearChat = () => {
    const welcomeMessage = {
      role: 'assistant',
      content: 'Chat history cleared. How can I help you today?',
      id: 'msg_' + Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages([welcomeMessage]);
    
    setChats(prev => prev.map(chat => {
      if (chat.id === currentChatId) {
        return { 
          ...chat, 
          messages: [welcomeMessage],
          preview: welcomeMessage.content.substring(0, 30) + '...',
          title: 'New Conversation' // Reset title when cleared
        };
      }
      return chat;
    }));

    toast({ title: "Chat Cleared", description: "Started a fresh conversation." });
  };

  const deleteChat = (chatId) => {
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    
    if (chatId === currentChatId) {
      if (chats.length > 1) {
        const nextChat = chats.find(chat => chat.id !== chatId);
        setCurrentChatId(nextChat.id);
        setMessages(nextChat.messages);
      } else {
        createNewChat();
      }
    }
    
    toast({ title: "Chat Deleted", description: "Conversation removed." });
  };

  const switchChat = (chatId) => {
    setCurrentChatId(chatId);
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <>
      <Helmet>
        <title>Chat AI Assistant - MediGuard Bamenda</title>
        <meta name="description" content="Conversational symptom checker and AI health assistant for personalized guidance." />
      </Helmet>

      <div className="h-[calc(100vh-64px)] bg-muted/30 flex overflow-hidden">
        {/* Sidebar */}
        <AnimatePresence mode="wait">
          {isSidebarOpen && (
            <>
              {/* Mobile Overlay */}
              {isMobile && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 bg-black/50 z-40"
                  onClick={() => setIsSidebarOpen(false)}
                />
              )}
              
              {/* Sidebar Panel */}
              <motion.div
                initial={{ x: isMobile ? -300 : 0 }}
                animate={{ x: 0 }}
                exit={{ x: -300 }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className={`
                  ${isMobile ? 'fixed left-0 top-16 bottom-0 z-50' : 'relative'}
                  w-[280px] bg-background border-r border-border flex flex-col
                `}
              >
                {/* Sidebar Header */}
                <div className="p-4 border-b border-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-primary" />
                    <h2 className="font-semibold text-foreground">MediGuard AI</h2>
                  </div>
                  {isMobile && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setIsSidebarOpen(false)}
                      className="h-8 w-8"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* New Chat Button */}
                <div className="p-3">
                  <Button
                    onClick={createNewChat}
                    className="w-full bg-primary hover:bg-primary/90 text-white justify-start gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    New Chat
                  </Button>
                </div>

                {/* Chat List */}
                <ScrollArea className="flex-1 px-3">
                  <div className="space-y-2 py-2">
                    {chats.map((chat) => (
                      <div
                        key={chat.id}
                        className={`
                          group relative flex items-center gap-3 p-3 rounded-lg cursor-pointer
                          transition-all duration-200
                          ${currentChatId === chat.id 
                            ? 'bg-primary/10 text-primary' 
                            : 'hover:bg-muted text-foreground'
                          }
                        `}
                        onClick={() => switchChat(chat.id)}
                      >
                        <MessageSquare className={`h-4 w-4 flex-shrink-0 ${
                          currentChatId === chat.id ? 'text-primary' : 'text-muted-foreground'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{chat.title}</p>
                          <p className="text-xs text-muted-foreground truncate">{chat.preview}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteChat(chat.id);
                          }}
                        >
                          <Trash2 className="h-3 w-3 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </ScrollArea>

                {/* Sidebar Footer */}
                <div className="p-4 border-t border-border">
                  <p className="text-xs text-muted-foreground text-center">
                    {chats.length} {chats.length === 1 ? 'chat' : 'chats'}
                  </p>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Chat Header */}
          <div className="p-3 sm:p-4 bg-background border-b shadow-sm flex items-center justify-between z-10 sticky top-0">
            <div className="flex items-center gap-2 sm:gap-3 w-full">
              {/* Sidebar Toggle Button */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleSidebar}
                className="h-8 w-8 sm:h-9 sm:w-9 flex-shrink-0"
                title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
              >
                {isSidebarOpen ? (
                  <PanelLeftClose className="h-4 w-4 sm:h-5 sm:w-5" />
                ) : (
                  <PanelLeftOpen className="h-4 w-4 sm:h-5 sm:w-5" />
                )}
              </Button>
              
              <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-shrink">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 sm:h-6 sm:w-6 text-primary" />
                </div>
                <div className="min-w-0">
                  <h1 className="text-base sm:text-xl font-bold flex items-center gap-2 text-foreground truncate">
                    MediGuard AI
                  </h1>
                  <p className="text-[10px] sm:text-xs text-muted-foreground flex items-center gap-1">
                    <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-green-500 inline-block"></span> 
                    <span className="truncate">Online & Ready</span>
                  </p>
                </div>
              </div>
              
              <div className="ml-auto flex items-center gap-1 sm:gap-2 flex-shrink-0">
                {!user && (
                  <Badge variant="outline" className="hidden sm:inline-flex bg-secondary/10 text-secondary border-secondary/20 text-xs">
                    Guest Mode - <Link to="/login" className="ml-1 underline font-bold text-primary">Login</Link>
                  </Badge>
                )}
                <Button variant="ghost" size="sm" onClick={clearChat} title="Clear Chat" className="text-muted-foreground hover:text-destructive h-8 sm:h-9 px-2 sm:px-3">
                  <RefreshCw className="h-3 w-3 sm:h-4 sm:w-4 sm:mr-2" />
                  <span className="hidden sm:inline">Clear</span>
                </Button>
              </div>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 flex flex-col w-full max-w-full overflow-hidden">
            <ScrollArea className="flex-1 p-3 sm:p-4" ref={scrollRef}>
              <div className="space-y-4 sm:space-y-6 pb-4 w-full">
                <AnimatePresence>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      className={`flex gap-2 sm:gap-3 w-full ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {message.role === 'assistant' && (
                        <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 shadow-sm mt-auto mb-1">
                          <Bot className="h-3 w-3 sm:h-5 sm:w-5 text-primary-foreground" />
                        </div>
                      )}
                      
                      <div className={`max-w-[85%] sm:max-w-[75%] flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                        <div
                          className={`rounded-2xl px-3 py-2 sm:px-5 sm:py-3 shadow-sm text-sm sm:text-[15px] leading-relaxed relative break-words w-full ${
                            message.role === 'user'
                              ? 'bg-secondary text-secondary-foreground rounded-br-sm'
                              : message.content.includes('🚨 EMERGENCY') 
                                ? 'bg-red-50 text-red-900 border border-red-200 rounded-bl-sm dark:bg-red-950/50 dark:text-red-200'
                                : 'bg-card text-foreground border rounded-bl-sm'
                          }`}
                        >
                          <p className="whitespace-pre-wrap break-words">{message.content}</p>
                        </div>
                        <span className="text-[10px] sm:text-[11px] text-muted-foreground mt-1 px-1">
                          {message.timestamp}
                        </span>
                      </div>

                      {message.role === 'user' && (
                        <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-muted border flex items-center justify-center flex-shrink-0 shadow-sm mt-auto mb-1">
                          <User className="h-3 w-3 sm:h-5 sm:w-5 text-muted-foreground" />
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                {/* Loading Indicator */}
                {isTyping && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-2 sm:gap-3 justify-start">
                    <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 shadow-sm mt-auto mb-1">
                      <Bot className="h-3 w-3 sm:h-5 sm:w-5 text-primary-foreground" />
                    </div>
                    <div className="bg-card border shadow-sm rounded-2xl rounded-bl-sm px-3 py-2 sm:px-5 sm:py-4 flex items-center gap-2 sm:gap-3">
                      <Loader2 className="h-3 w-3 sm:h-4 sm:w-4 animate-spin text-primary" />
                      <span className="text-xs sm:text-sm text-muted-foreground font-medium">AI is thinking...</span>
                    </div>
                  </motion.div>
                )}
              </div>
            </ScrollArea>

            {/* Input Area & Suggested Questions */}
            <div className="p-3 sm:p-4 bg-background border-t w-full">
              {messages.length <= 1 && !isTyping && (
                <div className="mb-3 sm:mb-4">
                  <SuggestedQuestions onSelectQuestion={handleSelectQuestion} />
                </div>
              )}

              <div className="flex gap-2 relative w-full">
                <Input
                  placeholder="Type your message here..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  className="bg-muted/50 border-input focus-visible:ring-primary h-12 sm:h-14 text-sm sm:text-base rounded-full pl-4 sm:pl-6 pr-12 sm:pr-14 shadow-inner w-full"
                  disabled={isTyping}
                />
                <Button 
                  onClick={() => handleSend()} 
                  disabled={!input.trim() || isTyping}
                  className="absolute right-1.5 top-1.5 bottom-1.5 rounded-full w-9 h-9 sm:w-11 sm:h-11 p-0 bg-primary hover:bg-primary/90 text-primary-foreground shadow-md transition-transform active:scale-95"
                >
                  <Send className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              </div>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2 sm:mt-3 text-center px-2">
                MediGuard AI is for informational purposes only and does not replace professional medical advice.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatAI;