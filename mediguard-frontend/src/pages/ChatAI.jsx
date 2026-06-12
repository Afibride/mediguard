import React, { useState, useRef, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Send, Bot, User, RefreshCw,
  Plus, MessageSquare, Trash2, X,
  PanelLeftClose, PanelLeftOpen, Share2, Clock,
  ThumbsUp, ThumbsDown, ImagePlus, Loader2, MapPin,
  HelpCircle, ChevronDown, Baby, CornerUpLeft, Activity
} from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';
import SuggestedQuestions from '@/components/SuggestedQuestions';
import SourceCitation from '@/components/SourceCitation';
import SeasonalBanner from '@/components/SeasonalBanner';
import VoiceInput from '@/components/VoiceInput';
import SpeakButton from '@/components/SpeakButton';
import { analyzeImage, saveChatHistory, sendChatMessage, submitChatFeedback } from '@/services/api';
import { useLanguage } from '@/contexts/LanguageContext';

// ── Swipe-to-reply wrapper (mobile touch only) ───────────────────────────────
function SwipeableMessage({ onReply, children }) {
  const [swipeX, setSwipeX] = React.useState(0);
  const startX = useRef(0);
  const startY = useRef(0);
  const swiping = useRef(false);

  function onTouchStart(e) {
    startX.current = e.touches[0].clientX;
    startY.current = e.touches[0].clientY;
    swiping.current = false;
  }

  function onTouchMove(e) {
    const dx = e.touches[0].clientX - startX.current;
    const dy = e.touches[0].clientY - startY.current;
    if (!swiping.current) {
      if (Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy) * 1.5) swiping.current = true;
      else if (Math.abs(dy) > 8) return;
    }
    if (swiping.current && dx > 0) setSwipeX(Math.min(dx, 65));
  }

  function onTouchEnd() {
    if (swipeX > 42) onReply();
    setSwipeX(0);
    swiping.current = false;
  }

  const iconOpacity = Math.min(Math.max((swipeX - 10) / 40, 0), 1);

  return (
    <div
      className="relative touch-pan-y w-full"
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      {/* Reply icon revealed as user swipes right */}
      <div
        className="absolute left-0 inset-y-0 flex items-center pointer-events-none text-primary"
        style={{ opacity: iconOpacity }}
        aria-hidden
      >
        <CornerUpLeft className="h-3.5 w-3.5" />
      </div>
      <div
        style={{
          transform: `translateX(${swipeX}px)`,
          transition: swipeX === 0 ? 'transform 0.25s ease' : 'none',
        }}
      >
        {children}
      </div>
    </div>
  );
}

// ── Inline markdown renderer ──────────────────────────────────────────────────
// Handles: **bold**, *italic*, `code`
function renderInline(text) {
  const parts = text.split(/(\*\*[^*\n]+\*\*|\*[^*\n]+\*|`[^`\n]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2)
      return <em key={i} className="italic">{part.slice(1, -1)}</em>;
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2)
      return <code key={i} className="px-1 py-0.5 rounded bg-muted text-[0.85em] font-mono">{part.slice(1, -1)}</code>;
    return part;
  });
}

function MarkdownMessage({ content }) {
  if (!content) return null;

  // Split into blocks on blank lines
  const blocks = content.split(/\n{2,}/);

  return (
    <div className="space-y-2 max-w-full min-w-0 break-words [overflow-wrap:anywhere]">
      {blocks.map((block, bi) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Horizontal rule
        if (/^---+$/.test(trimmed)) {
          return <hr key={bi} className="border-border my-1" />;
        }

        const lines = trimmed.split('\n').filter(Boolean);

        // Heading: ## or ###
        if (lines.length === 1) {
          const h3Match = lines[0].match(/^###\s+(.+)/);
          const h2Match = lines[0].match(/^##\s+(.+)/);
          const h1Match = lines[0].match(/^#\s+(.+)/);
          if (h1Match) return <h3 key={bi} className="font-bold text-base mt-1 leading-snug text-foreground">{renderInline(h1Match[1])}</h3>;
          if (h2Match) return <h3 key={bi} className="font-bold text-sm mt-1 leading-snug text-foreground">{renderInline(h2Match[1])}</h3>;
          if (h3Match) return <h4 key={bi} className="font-semibold text-sm mt-0.5 leading-snug text-foreground">{renderInline(h3Match[1])}</h4>;
        }

        const listMarker = /^(?:\d+[.)]|[•\-\*])\s/;
        const isList = lines.length > 1 && lines.every(l => listMarker.test(l.trim()));
        const isSingleBullet = lines.length === 1 && listMarker.test(lines[0].trim());
        const isNumbered = lines.every(l => /^\d+[.)]\s/.test(l.trim()));

        // Handle headings inside multi-line blocks
        const headingLine = lines.find(l => /^#{1,3}\s/.test(l));
        const nonHeadingLines = lines.filter(l => !/^#{1,3}\s/.test(l));

        if (headingLine && nonHeadingLines.length > 0) {
          const headingText = headingLine.replace(/^#{1,3}\s+/, '');
          return (
            <div key={bi} className="space-y-1.5">
              <h4 className="font-bold text-sm text-foreground">{renderInline(headingText)}</h4>
              <p className="leading-relaxed break-words [overflow-wrap:anywhere]">
                {nonHeadingLines.map((line, li) => (
                  <React.Fragment key={li}>{li > 0 && <br />}{renderInline(line)}</React.Fragment>
                ))}
              </p>
            </div>
          );
        }

        if (isList || isSingleBullet) {
          const ListTag = isNumbered ? 'ol' : 'ul';
          return (
            <ListTag key={bi} className={`space-y-1 ${isNumbered ? 'list-decimal pl-5' : 'pl-1'}`}>
              {lines.map((line, li) => {
                const lineText = line.replace(/^(?:\d+[.)]|[•\-\*])\s*/, '');
                // Sub-heading check within list item (bold-only line)
                const boldOnly = lineText.startsWith('**') && lineText.endsWith('**') && !lineText.slice(2,-2).includes('**');
                return (
                  <li key={li} className={isNumbered ? 'leading-relaxed' : 'flex items-start gap-2'}>
                    {!isNumbered && <span className="text-primary font-bold mt-0.5 shrink-0 text-xs">•</span>}
                    <span className={`leading-relaxed ${boldOnly ? 'font-semibold text-foreground' : ''}`}>
                      {renderInline(lineText)}
                    </span>
                  </li>
                );
              })}
            </ListTag>
          );
        }

        return (
          <p key={bi} className="leading-relaxed max-w-full break-words [overflow-wrap:anywhere]">
            {lines.map((line, li) => {
              // Detect inline heading pattern (line that IS a heading)
              const h2m = line.match(/^##\s+(.+)/);
              const h3m = line.match(/^###\s+(.+)/);
              if (h2m) return <React.Fragment key={li}>{li > 0 && <br />}<strong className="font-bold text-sm block mt-1">{renderInline(h2m[1])}</strong></React.Fragment>;
              if (h3m) return <React.Fragment key={li}>{li > 0 && <br />}<strong className="font-semibold text-sm block mt-0.5">{renderInline(h3m[1])}</strong></React.Fragment>;
              return (
                <React.Fragment key={li}>
                  {li > 0 && <br />}
                  {renderInline(line)}
                </React.Fragment>
              );
            })}
          </p>
        );
      })}
    </div>
  );
}

const SYMPTOM_CHECKER_NUDGE =
  "For more accurate results when testing symptoms, please use MediGuard's Symptom Checker. It asks structured questions and compares your symptoms more carefully than chat.";

const isAssessmentDiscussionRequest = (text) =>
  /\b(explain|discuss|tell me more about).*\b(mediguard\s+)?assessment\s+result\b/i.test(text)
  || /\bmy result matched\b/i.test(text);

const isSymptomTestingRequest = (text) =>
  !isAssessmentDiscussionRequest(text)
  && /\b(symptoms?|symptom checker|diagnos(?:e|is|ing)?|what disease|what illness|what do i have|check me|test me|i have|i feel|fever|headache|cough|pain|vomit|diarrh(?:ea|e?a)|rash|malaria|typhoid|cholera|dizzy|nausea|sore throat|stomach|chest)\b/i.test(text);

const ChatAI = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const { t } = useLanguage();
  const location = useLocation();
  const messagesScrollRef = useRef(null);
  const messagesEndRef = useRef(null);
  const shouldStickToBottomRef = useRef(true);
  const programmaticScrollRef = useRef(false);
  
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [chats, setChats] = useState(() => {
    try { return JSON.parse(localStorage.getItem('mg_chats') || '[]'); } catch { return []; }
  });
  const [currentChatId, setCurrentChatId] = useState(() => {
    return localStorage.getItem('mg_current_chat') || null;
  });
  const [sharingChatId, setSharingChatId] = useState(null);
  const [ratings, setRatings] = useState({});
  const [userLocation, setUserLocation] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageAnalyzing, setImageAnalyzing] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [childMode, setChildMode] = useState(false);
  const [voiceListening, setVoiceListening] = useState(false);
  const [replyingTo, setReplyingTo] = useState(null); // { id, role, content }
  const imageInputRef = useRef(null);
  const sessionId = useRef('sess_' + Date.now()).current;

  // Voice transcript handler — inject into input, then auto-send
  const handleVoiceTranscript = (transcript) => {
    const text = childMode ? `My child: ${transcript}` : transcript;
    setInput(text);
    // Small delay so the user sees what was captured before it sends
    setTimeout(() => handleSend(text), 400);
  };

  // ── Reply-hint chips for symptom follow-up questions ─────────────────────
  const getReplyHints = (followUpQuestions) => {
    if (!followUpQuestions?.length) return [];
    const q = (followUpQuestions[0] || '').toLowerCase();
    if (q.includes('how long have you had'))
      return ['1 day', '2–3 days', 'About a week', 'More than 2 weeks'];
    if (q.includes('mild, moderate, or severe'))
      return ['Mild', 'Moderate', 'Severe'];
    if (q.includes('what is your temperature') || q.includes('fever come with'))
      return ["Don't know my temp", 'About 38 °C', 'About 39 °C', 'Very high — above 40 °C'];
    if (q.includes('other symptoms') || q.includes('additional changes'))
      return ['No other symptoms', 'Nausea', 'Vomiting', 'Rash'];
    if (q.includes('keep fluids') || q.includes('drink fluids') || q.includes('blood in') || q.includes('dehydration'))
      return ['Yes, can drink fluids', 'No, keep vomiting', 'Signs of dehydration', 'No blood in stool'];
    if (q.includes('chest pain') || q.includes('wheezing') || q.includes('breathing'))
      return ['No chest pain', 'Yes — chest pain', 'Yes — wheezing', 'Shortness of breath'];
    if (q.includes('poor sleep') || q.includes('heavy') || q.includes('exertion') || q.includes('missed meals'))
      return ['Yes — poor sleep', 'No unusual activity', 'Stressed / missed meals', 'Heavy physical work'];
    if (q.includes('how many weeks pregnant'))
      return ['Under 12 weeks', '12–28 weeks', 'Over 28 weeks'];
    return [];
  };

  useEffect(() => {
    const previousBodyOverflow = document.body.style.overflow;
    const previousHtmlOverflow = document.documentElement.style.overflow;
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
    };
  }, []);

  // Request location silently on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => {},
        { timeout: 8000 }
      );
    }
  }, []);

  const isNearMessageBottom = () => {
    const node = messagesScrollRef.current;
    if (!node) return true;
    return node.scrollHeight - node.scrollTop - node.clientHeight < 96;
  };

  const handleMessagesScroll = () => {
    // Ignore scroll events caused by our own scrollToLatest() calls, so a
    // user manually scrolling away from the bottom (e.g. while the AI is
    // typing) isn't immediately snapped back by the next auto-scroll tick.
    if (programmaticScrollRef.current) {
      programmaticScrollRef.current = false;
      return;
    }
    shouldStickToBottomRef.current = isNearMessageBottom();
  };

  const scrollToLatest = (behavior = 'smooth', force = false) => {
    window.requestAnimationFrame(() => {
      const node = messagesScrollRef.current;
      if (!node || (!force && !shouldStickToBottomRef.current)) return;
      programmaticScrollRef.current = true;
      node.scrollTo({ top: node.scrollHeight, behavior });
    });
  };

  // Persist chats to localStorage
  useEffect(() => {
    localStorage.setItem('mg_chats', JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    if (currentChatId) localStorage.setItem('mg_current_chat', currentChatId);
  }, [currentChatId]);

  const groupChatsByDate = (chatList) => {
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();
    const groups = { Today: [], Yesterday: [], Earlier: [] };
    chatList.forEach(chat => {
      const d = new Date(chat.createdAt).toDateString();
      if (d === today) groups.Today.push(chat);
      else if (d === yesterday) groups.Yesterday.push(chat);
      else groups.Earlier.push(chat);
    });
    return groups;
  };

  const shareChat = async (chatId) => {
    const chat = chats.find(c => c.id === chatId);
    if (!chat) return;
    setSharingChatId(chatId);
    const text = `MediGuard AI Chat — ${chat.title}\n${'─'.repeat(40)}\n\n` +
      chat.messages.map(m => `${m.role === 'user' ? 'You' : 'MediGuard AI'} [${m.timestamp || ''}]:\n${m.content}`).join('\n\n') +
      `\n\n─────\nShared from MediGuard – Community Health AI, Bamenda`;
    try {
      await navigator.clipboard.writeText(text);
      toast({ title: "Chat copied!", description: "Conversation copied to clipboard." });
    } catch {
      toast({ variant: "destructive", title: "Copy failed", description: "Could not access clipboard." });
    }
    setTimeout(() => setSharingChatId(null), 1500);
  };

  const pregnancyContextFromText = (text) => {
    const lower = text.toLowerCase();
    const pregnant = /\b(pregnant|pregnancy|expecting|antenatal|prenatal|trimester)\b/.test(lower);
    const weeksMatch = lower.match(/(\d{1,2})\s*(weeks|week|wks|wk)/);
    return {
      is_pregnant: pregnant,
      pregnancy_weeks: weeksMatch ? Number(weeksMatch[1]) : null,
    };
  };

  const isFacilityRequest = (text) =>
    /\b(nearest|nearby|hospital|clinic|health facility|doctor|where can i go|where should i go|directions?)\b/i.test(text);

  const requestCurrentLocation = () => new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const location = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserLocation(location);
        resolve(location);
      },
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  });

  // Check screen size for responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) {
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
    scrollToLatest(messages.length <= 1 ? 'auto' : 'smooth');
  }, [messages, isTyping]);

  // Create a new chat
  const createNewChat = () => {
    if (chats.length === 0 || currentChatId) {
      const newChatId = 'chat_' + Date.now();
      const welcomeMessage = {
        role: 'assistant',
        content: t('chat_welcome'),
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
        let title = userMessage;
        
        if (userMessage.length > 40) {
          title = userMessage.substring(0, 40) + '...';
        }
        
        title = title.charAt(0).toUpperCase() + title.slice(1);
        
        return { ...chat, title };
      }
      return chat;
    }));
  };

  // Handle message sending
  const handleSend = async (textOverride = null, isInitial = false) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim()) return;

    const userMsgObj = {
      role: 'user',
      content: textToSend,
      id: 'msg_user_' + Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      ...(replyingTo ? { replyTo: { id: replyingTo.id, role: replyingTo.role, content: replyingTo.content } } : {}),
    };
    setReplyingTo(null);
    
    const updatedMessages = [...messages, userMsgObj];
    shouldStickToBottomRef.current = true;
    setMessages(updatedMessages);
    scrollToLatest('smooth', true);
    
    setChats(prev => prev.map(chat => {
      if (chat.id === currentChatId) {
        if (chat.title === 'New Conversation') {
          updateChatTitle(chat.id, textToSend);
        }
        
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

    try {
      const history = messages.slice(-20).map((message) => ({
        role: message.role,
        content: message.content,
      }));
      const pregnancyContext = pregnancyContextFromText(textToSend);
      const freshLocation = isFacilityRequest(textToSend) && !userLocation
        ? await requestCurrentLocation()
        : userLocation;
      const res = await sendChatMessage(textToSend, history, null, {
        ...pregnancyContext,
        ...(freshLocation ? { user_lat: freshLocation.lat, user_lng: freshLocation.lng } : {}),
        child_mode: childMode,
      });
      const rawAnswer = res.data.answer || '';
      const shouldNudgeSymptomChecker = isSymptomTestingRequest(textToSend)
        && !rawAnswer.toLowerCase().includes('symptom checker');
      const fullAnswer = shouldNudgeSymptomChecker
        ? `${rawAnswer}\n\n${SYMPTOM_CHECKER_NUDGE}`
        : rawAnswer;
      const aiMsgObj = {
        role: 'assistant',
        content: '',
        sources: res.data.sources,
        disclaimer: res.data.disclaimer,
        followUpQuestions: res.data.follow_up_questions || [],
        id: 'msg_ai_' + Date.now(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setIsTyping(false);
      const finalMessages = [...updatedMessages, aiMsgObj];
      setMessages(finalMessages);

      let typed = '';
      const chunkSize = fullAnswer.length > 500 ? 5 : 2;
      await new Promise((resolve) => {
        const interval = window.setInterval(() => {
          typed = fullAnswer.slice(0, typed.length + chunkSize);
          const typedMessages = finalMessages.map((message) => (
            message.id === aiMsgObj.id ? { ...message, content: typed } : message
          ));
          setMessages(typedMessages);
          scrollToLatest('auto');
          setChats(prev => prev.map(chat => (
            chat.id === currentChatId
              ? { ...chat, messages: typedMessages, preview: typed.substring(0, 30) + (typed.length >= 30 ? '...' : '') }
              : chat
          )));
          if (typed.length >= fullAnswer.length) {
            window.clearInterval(interval);
            resolve();
          }
        }, 35);
      });

      const completedAiMsgObj = { ...aiMsgObj, content: fullAnswer };
      const completedMessages = [...updatedMessages, completedAiMsgObj];
      setMessages(completedMessages);
      setChats(prev => prev.map(chat => (
        chat.id === currentChatId
          ? { ...chat, messages: completedMessages, preview: fullAnswer.substring(0, 30) + '...' }
          : chat
      )));
      if (user) {
        const title = textToSend.length > 48 ? `${textToSend.slice(0, 48)}...` : textToSend;
        saveChatHistory({
          title,
          message: textToSend,
          response: fullAnswer,
          sources: res.data.sources || [],
          mode: res.data.mode || null,
          pregnancy_context: res.data.pregnancy_context || pregnancyContext.is_pregnant,
          follow_up_questions: res.data.follow_up_questions || [],
        }).catch(() => {
          const key = `chat_history_${user.id}`;
          const stored = JSON.parse(localStorage.getItem(key) || '[]');
          localStorage.setItem(key, JSON.stringify([{
            id: `chat_${Date.now()}`,
            title,
            message: textToSend,
            response: res.data.answer,
            sources: res.data.sources || [],
            mode: res.data.mode || null,
            follow_up_questions: res.data.follow_up_questions || [],
            created_at: new Date().toISOString(),
          }, ...stored]));
        });
      }
    } catch (error) {
      const aiMsgObj = {
        role: 'assistant',
        content: isInitial
          ? "I see you're coming from your diagnosis results. The health assistant is offline right now, but I can still remind you to seek professional care for urgent symptoms."
          : "I could not reach the MediGuard backend. Please check that the API is running, then try again.",
        sources: [],
        id: 'msg_ai_' + Date.now(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      const finalMessages = [...updatedMessages, aiMsgObj];
      setMessages(finalMessages);
      setChats(prev => prev.map(chat => (
        chat.id === currentChatId
          ? { ...chat, messages: finalMessages, preview: aiMsgObj.content.substring(0, 30) + '...' }
          : chat
      )));
      toast({
        variant: "destructive",
        title: "Assistant unavailable",
        description: error.message || "Could not reach the backend.",
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleSelectQuestion = (question) => {
    handleSend(question);
  };

  // Card click: show a bot clarifying prompt instead of sending to AI.
  // The synthetic message IS included in history when the user next replies,
  // so the AI understands the context of what area the user is concerned about.
  const handleSelectCard = (tile) => {
    // Activate child mode for the child card
    if (tile.childCard) {
      setChildMode(true);
    }

    const syntheticMsg = {
      id: 'card_' + Date.now(),
      role: 'assistant',
      content: tile.prompt,
      sources: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      followUpQuestions: tile.followUps || [],   // camelCase matches AI message shape
      isCardPrompt: true,   // skip rating/feedback buttons
    };

    setMessages(prev => [...prev, syntheticMsg]);
    shouldStickToBottomRef.current = true;
    scrollToLatest('smooth', true);
  };

  const handleImageSend = async () => {
    if (!imageFile) return;
    const context = input.trim();
    const userText = context
      ? `[Image uploaded] ${context}`
      : '[Image uploaded — analyzing visual symptom]';

    const userMsgObj = {
      role: 'user',
      content: userText,
      imagePreview: imagePreview,
      id: 'msg_user_' + Date.now(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    const updatedMessages = [...messages, userMsgObj];
    shouldStickToBottomRef.current = true;
    setMessages(updatedMessages);
    scrollToLatest('smooth', true);
    setChats(prev => prev.map(c => c.id === currentChatId
      ? { ...c, messages: updatedMessages, preview: userText.substring(0, 30) + '…' }
      : c
    ));
    setInput('');
    setImageFile(null);
    setImagePreview(null);
    setImageAnalyzing(true);

    try {
      const res = await analyzeImage(imageFile, context);
      const fullAnswer = res.data.analysis || 'Image analysis is unavailable.';
      const aiMsgObj = {
        role: 'assistant',
        content: fullAnswer,
        sources: [],
        disclaimer: res.data.disclaimer,
        followUpQuestions: [],
        id: 'msg_ai_' + Date.now(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      const finalMessages = [...updatedMessages, aiMsgObj];
      setMessages(finalMessages);
      setChats(prev => prev.map(c => c.id === currentChatId
        ? { ...c, messages: finalMessages, preview: fullAnswer.substring(0, 30) + '…' }
        : c
      ));
    } catch (err) {
      const raw = err?.response?.data?.detail || err?.message || '';
      const isQuota = raw.includes('quota') || raw.includes('429') || raw.includes('unavailable');
      const description = isQuota
        ? 'Image analysis is temporarily unavailable (AI vision quota reached). Please describe your symptoms in the chat instead.'
        : 'Could not analyse the image. Please try again or describe your symptoms in the chat.';
      toast({ variant: 'destructive', title: 'Image analysis failed', description });
    } finally {
      setImageAnalyzing(false);
    }
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
          title: 'New Conversation'
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

  const extractKeywords = (text) => {
    const stop = new Set(['the','a','an','is','are','was','were','be','been','being','have','has','had',
      'do','does','did','will','would','could','should','may','might','can','i','you','my','your',
      'this','that','it','in','on','at','to','for','of','and','or','but','with','what','how','why',
      'when','where','who','about','from','by']);
    return [...new Set(
      text.toLowerCase().replace(/[^a-z\s]/g, ' ').split(/\s+/)
        .filter(w => w.length > 3 && !stop.has(w))
    )].slice(0, 8);
  };

  const handleRate = async (msg, isHelpful) => {
    if (ratings[msg.id] !== undefined) return;
    setRatings(prev => ({ ...prev, [msg.id]: isHelpful }));
    const prevUserMsg = messages[messages.findIndex(m => m.id === msg.id) - 1];
    try {
      await submitChatFeedback({
        session_id: sessionId,
        query: prevUserMsg?.content || '',
        response_preview: msg.content?.slice(0, 300) || '',
        rating: isHelpful,
        query_keywords: extractKeywords(prevUserMsg?.content || ''),
        mode: msg.mode || null,
      });
    } catch { /* silent */ }
  };

  return (
    <>
      <Helmet>
        <title>Chat AI Assistant — MediGuard Bamenda | Health Guidance</title>
        <meta name="description" content="Talk to MediGuard's AI health assistant. Describe your symptoms in plain language and receive personalized health guidance, disease information, and next-step advice for the Bamenda community." />
        <meta name="keywords" content="AI health chat, symptom assistant, MediGuard chat, Bamenda health AI, disease guidance, medical chatbot, Cameroon" />
        <link rel="canonical" href="https://mediguard.info/chat-ai" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://mediguard.info/chat-ai" />
        <meta property="og:title" content="Chat AI Assistant — MediGuard Bamenda" />
        <meta property="og:description" content="Describe your symptoms and get personalized AI health guidance. Available 24/7 for the Bamenda community." />
        <meta property="og:image" content="https://mediguard.info/mediguard.png" />
        <meta property="og:site_name" content="MediGuard" />
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content="Chat AI Assistant — MediGuard Bamenda" />
        <meta name="twitter:description" content="AI health assistant for the Bamenda community. Available 24/7." />
        <meta name="twitter:image" content="https://mediguard.info/mediguard.png" />
      </Helmet>

      <div className="fixed inset-x-0 bottom-0 top-16 w-full max-w-[100vw] overflow-x-hidden bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.12),transparent_22rem),linear-gradient(180deg,hsl(var(--background)),hsl(var(--muted)/0.62))] flex overflow-hidden overscroll-none">
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
                  ${isMobile ? 'fixed left-0 top-16 bottom-0 z-50 max-w-[86vw]' : 'relative'}
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
                    className="w-full bg-primary hover:bg-primary/90 text-white justify-start gap-2 rounded-lg"
                  >
                    <Plus className="h-4 w-4" />
                    New Chat
                  </Button>
                </div>

                {/* Chat List — date grouped */}
                <ScrollArea className="flex-1 px-2">
                  <div className="py-2 space-y-1">
                    {chats.length === 0 ? (
                      <p className="text-xs text-muted-foreground text-center py-6">No chats yet</p>
                    ) : (
                      Object.entries(groupChatsByDate(chats)).map(([label, group]) =>
                        group.length === 0 ? null : (
                          <div key={label}>
                            <div className="flex items-center gap-1.5 px-2 py-1.5">
                              <Clock className="h-3 w-3 text-muted-foreground/60" />
                              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">{label}</span>
                            </div>
                            {group.map((chat, i) => (
                              <motion.div
                                key={chat.id}
                                initial={{ opacity: 0, x: -12 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.04 }}
                                className={`group relative flex items-center gap-2 px-2 py-2.5 rounded-lg cursor-pointer transition-all duration-150 ${
                                  currentChatId === chat.id
                                    ? 'bg-primary/10 text-primary'
                                    : 'hover:bg-muted text-foreground'
                                }`}
                                onClick={() => switchChat(chat.id)}
                              >
                                <MessageSquare className={`h-3.5 w-3.5 flex-shrink-0 ${currentChatId === chat.id ? 'text-primary' : 'text-muted-foreground'}`} />
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs font-medium truncate">{chat.title}</p>
                                  <p className="text-[10px] text-muted-foreground truncate">{chat.preview}</p>
                                </div>
                                {/* Action buttons shown on hover */}
                                <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-5 w-5"
                                    title="Share chat"
                                    onClick={(e) => { e.stopPropagation(); shareChat(chat.id); }}
                                  >
                                    {sharingChatId === chat.id
                                      ? <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="text-[9px] text-green-500 font-bold">OK</motion.span>
                                      : <Share2 className="h-2.5 w-2.5 text-muted-foreground" />
                                    }
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-5 w-5"
                                    title="Delete chat"
                                    onClick={(e) => { e.stopPropagation(); deleteChat(chat.id); }}
                                  >
                                    <Trash2 className="h-2.5 w-2.5 text-destructive" />
                                  </Button>
                                </div>
                              </motion.div>
                            ))}
                          </div>
                        )
                      )
                    )}
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

        {/* Main Chat Area - FIXED for mobile cropping */}
        <div className="flex-1 flex flex-col min-w-0 w-full max-w-full overflow-hidden">
          {/* Chat Header — always visible, pinned to top */}
          <div className="p-3 sm:p-4 bg-background/98 backdrop-blur-md border-b shadow-sm flex items-center justify-between z-20 sticky top-0 shrink-0 max-w-full overflow-hidden">
            <div className="flex items-center gap-2 sm:gap-3 w-full min-w-0">
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
              
              <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary/10 ring-1 ring-primary/20 flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 sm:h-6 sm:w-6 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-base sm:text-xl font-bold flex items-center gap-2 text-foreground truncate">
                    MediGuard AI
                  </h1>
                  <p className="text-[10px] sm:text-xs text-muted-foreground flex items-center gap-1">
                    <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-green-500 inline-block"></span> 
                    <span className="truncate">{t('chat_online')}</span>
                  </p>
                </div>
              </div>
              
              <div className="ml-auto flex items-center gap-1 sm:gap-2 flex-shrink-0">
                {!user && (
                  <Badge variant="outline" className="hidden sm:inline-flex bg-secondary/10 text-secondary border-secondary/20 text-xs">
                    Guest Mode - <Link to="/login" className="ml-1 underline font-bold text-primary">Login</Link>
                  </Badge>
                )}
                {/* Child mode toggle */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setChildMode(v => !v)}
                  title={childMode ? 'Turn off child mode' : 'Child mode — asking about a child/infant'}
                  className={`h-8 w-8 sm:h-9 sm:w-9 ${childMode ? 'text-rose-600 bg-rose-50 dark:bg-rose-950/30' : 'text-muted-foreground hover:text-rose-600'}`}
                >
                  <Baby className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowHelp(v => !v)}
                  title="How to chat with MediGuard AI"
                  className={`h-8 w-8 sm:h-9 sm:w-9 ${showHelp ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-primary'}`}
                >
                  <HelpCircle className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
                <Button variant="ghost" size="sm" onClick={clearChat} title="Clear Chat" className="text-muted-foreground hover:text-destructive h-8 sm:h-9 px-2 sm:px-3">
                  <RefreshCw className="h-3 w-3 sm:h-4 sm:w-4 sm:mr-2" />
                  <span className="hidden sm:inline">{t('chat_clear')}</span>
                </Button>
              </div>
            </div>
          </div>

          {/* Seasonal disease banner — compact strip below header */}
          <SeasonalBanner compact className="mx-3 mt-2 mb-0" />

          {/* Child mode indicator strip */}
          {childMode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mx-3 mt-1.5 flex items-center gap-2 rounded-lg border border-rose-300 bg-rose-50 dark:bg-rose-950/30 dark:border-rose-700 px-3 py-1.5 text-[11px] text-rose-700 dark:text-rose-300"
            >
              <Baby className="h-3.5 w-3.5 shrink-0" />
              <span className="flex-1 font-medium">Child mode ON — responses adapted for children & infants</span>
              <button onClick={() => setChildMode(false)} className="opacity-60 hover:opacity-100">
                <X className="h-3 w-3" />
              </button>
            </motion.div>
          )}

          {/* Help Panel — collapsible, shown when showHelp is true */}
          <AnimatePresence>
            {showHelp && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.22, ease: 'easeInOut' }}
                className="overflow-hidden border-b border-primary/20 bg-primary/5"
              >
                <div className="px-4 py-3 max-w-2xl mx-auto">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-primary uppercase tracking-wide flex items-center gap-1.5">
                      <HelpCircle className="h-3.5 w-3.5" /> How to chat with MediGuard AI
                    </p>
                    <button onClick={() => setShowHelp(false)} className="text-muted-foreground hover:text-foreground">
                      <ChevronDown className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] sm:text-xs text-muted-foreground">
                    <div className="space-y-1.5">
                      <p className="font-semibold text-foreground">💬 Any language works</p>
                      <p>✦ English: <em>"I have fever and chills"</em></p>
                      <p>✦ Pidgin: <em>"My head dey pain me and body hot"</em></p>
                      <p>✦ Français: <em>"J'ai de la fièvre et mal à la tête"</em></p>
                      <p>✦ Or just <strong>tap a body tile</strong> — no typing needed!</p>
                    </div>
                    <div className="space-y-1.5">
                      <p className="font-semibold text-foreground">🔁 Quick answers to follow-ups</p>
                      <p>✦ Duration → <em>"3 days"</em> or <em>"about a week"</em></p>
                      <p>✦ Severity → <em>"mild"</em>, <em>"moderate"</em>, <em>"severe"</em></p>
                      <p>✦ Temperature → <em>"38 °C"</em> or <em>"no thermometer"</em></p>
                      <p>✦ No more symptoms → reply <em>"no"</em> or <em>"none"</em></p>
                    </div>
                    <div className="space-y-1.5">
                      <p className="font-semibold text-foreground">💡 Other things you can ask</p>
                      <p>✦ <em>"Can neem leaves help with fever?"</em></p>
                      <p>✦ <em>"Vaccination schedule for my pikin"</em></p>
                      <p>✦ <em>"Nearest hospital in Bamenda"</em></p>
                      <p>✦ <em>"What diseases are trending now?"</em></p>
                    </div>
                    <div className="space-y-1.5">
                      <p className="font-semibold text-foreground">🎤 Voice &amp; special modes</p>
                      <p>✦ Tap the <strong>🎤 mic button</strong> to speak your symptoms</p>
                      <p>✦ Tap the <strong>👶 baby icon</strong> for child health mode</p>
                      <p>✦ Upload an image of a rash or skin condition</p>
                      <p>✦ Start a new chat for a fresh topic</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Messages Area - FIXED: proper overflow handling */}
          <div className="flex-1 flex flex-col w-full max-w-full min-w-0 overflow-hidden">
            <div
              ref={messagesScrollRef}
              onScroll={handleMessagesScroll}
              className="flex-1 w-full max-w-full overflow-y-auto overflow-x-hidden overscroll-contain"
            >
              <div className="px-2.5 sm:px-4 py-2.5 sm:py-4 w-full max-w-full min-w-0">
                <div className="space-y-4 sm:space-y-6 w-full max-w-full">
                  <AnimatePresence>
                    {messages.map((message) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        className={`group/msg flex gap-2 sm:gap-3 w-full max-w-full min-w-0 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        {message.role === 'assistant' && (
                          <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 shadow-sm mt-auto mb-1">
                            <Bot className="h-3 w-3 sm:h-5 sm:w-5 text-primary-foreground" />
                          </div>
                        )}
                        
                        {/* FIXED: Better responsive width management */}
                        <div className={`max-w-[calc(100%-2.25rem)] sm:max-w-[75%] min-w-0 flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                          <SwipeableMessage onReply={() => setReplyingTo({ id: message.id, role: message.role, content: message.content })}>
                          <div
                            className={`rounded-2xl px-3 py-2.5 sm:px-5 sm:py-3 shadow-sm text-sm sm:text-[15px] leading-relaxed relative break-words [overflow-wrap:anywhere] w-full max-w-full ${
                              message.role === 'user'
                                ? 'bg-secondary text-secondary-foreground rounded-br-md shadow-secondary/10'
                                : message.content.includes('🚨 EMERGENCY')
                                  ? 'bg-red-50 text-red-900 border border-red-200 rounded-bl-md dark:bg-red-950/50 dark:text-red-200'
                                  : 'bg-card/95 text-foreground border border-primary/10 rounded-bl-md shadow-primary/5'
                            }`}
                          >
                            {/* ── Reply quote ── */}
                            {message.replyTo && (
                              <div className={`mb-2 rounded-lg border-l-[3px] pl-2.5 pr-2 py-1.5 text-[11px] ${
                                message.role === 'user'
                                  ? 'border-white/50 bg-white/15'
                                  : 'border-primary/40 bg-primary/5'
                              }`}>
                                <p className="font-semibold text-[10px] uppercase tracking-wide mb-0.5 opacity-70">
                                  {message.replyTo.role === 'user' ? 'You said' : 'MediGuard AI said'}
                                </p>
                                <p className="opacity-75 leading-snug line-clamp-2">
                                  {message.replyTo.content.length > 100
                                    ? message.replyTo.content.slice(0, 100) + '…'
                                    : message.replyTo.content}
                                </p>
                              </div>
                            )}
                            {message.role === 'assistant'
                              ? <MarkdownMessage content={message.content} />
                              : (
                                <>
                                  {message.imagePreview && (
                                    <img src={message.imagePreview} alt="uploaded symptom"
                                      className="mb-2 max-h-48 rounded-lg object-contain border border-white/20 max-w-full" />
                                  )}
                                  <p className="whitespace-pre-wrap break-words [overflow-wrap:anywhere]">{message.content}</p>
                                </>
                              )
                            }
                          </div>
                          </SwipeableMessage>
                          <div className={`flex items-center gap-1.5 mt-1 px-1 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <span className="text-[10px] sm:text-[11px] text-muted-foreground">
                              {message.timestamp}
                            </span>
                            {/* Reply button */}
                            <button
                              onClick={() => setReplyingTo({ id: message.id, role: message.role, content: message.content })}
                              className="opacity-0 group-hover/msg:opacity-100 focus:opacity-100 p-0.5 rounded text-muted-foreground/50 hover:text-primary transition-all"
                              title="Reply to this message"
                            >
                              <CornerUpLeft className="h-3 w-3" />
                            </button>
                          </div>
                          {message.role === 'assistant' && !message.isCardPrompt && <SourceCitation sources={message.sources} />}
                          {message.role === 'assistant' && !message.isCardPrompt && (
                            <div className="mt-1 px-1">
                              <SpeakButton text={message.content} size="sm" showSpeed />
                            </div>
                          )}
                          {message.role === 'assistant' && message.id !== messages[0]?.id && !message.isCardPrompt && (
                            <div className="flex items-center gap-1.5 mt-1.5 px-1 flex-wrap">
                              <span className="text-[10px] text-muted-foreground">Helpful?</span>
                              <button
                                onClick={() => handleRate(message, true)}
                                disabled={ratings[message.id] !== undefined}
                                className={`p-1 rounded transition-colors ${
                                  ratings[message.id] === true
                                    ? 'text-green-600'
                                    : ratings[message.id] !== undefined
                                      ? 'text-muted-foreground/30'
                                      : 'text-muted-foreground hover:text-green-600'
                                }`}
                                title="Helpful"
                              >
                                <ThumbsUp className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => handleRate(message, false)}
                                disabled={ratings[message.id] !== undefined}
                                className={`p-1 rounded transition-colors ${
                                  ratings[message.id] === false
                                    ? 'text-red-500'
                                    : ratings[message.id] !== undefined
                                      ? 'text-muted-foreground/30'
                                      : 'text-muted-foreground hover:text-red-500'
                                }`}
                                title="Not helpful"
                              >
                                <ThumbsDown className="h-3 w-3" />
                              </button>
                              {ratings[message.id] !== undefined && (
                                <motion.span
                                  initial={{ opacity: 0, scale: 0.8 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  className="text-[10px] text-muted-foreground"
                                >
                                  {ratings[message.id] ? 'Thanks!' : 'Noted, we\'ll improve.'}
                                </motion.span>
                              )}
                            </div>
                          )}
                          {/* Reply suggestion chips — last AI message only */}
                          {message.role === 'assistant' &&
                            message.id === messages.filter(m => m.role === 'assistant').at(-1)?.id &&
                            Array.isArray(message.followUpQuestions) &&
                            message.followUpQuestions.length > 0 && (() => {
                              // Card prompts: show follow-up options directly as tappable chips
                              if (message.isCardPrompt) {
                                return (
                                  <div className="mt-2.5">
                                    <p className="text-[10px] text-muted-foreground mb-1.5 px-0.5">Tap to describe, or type your own:</p>
                                    <div className="flex max-w-full flex-wrap gap-1.5 overflow-hidden">
                                      {message.followUpQuestions.map((hint) => (
                                        <button
                                          key={hint}
                                          onClick={() => handleSend(hint)}
                                          className="rounded-full border border-primary/40 bg-primary/8 hover:bg-primary hover:text-white hover:border-primary px-3 py-1 text-[11px] sm:text-xs font-medium text-primary transition-colors text-left"
                                        >
                                          {hint}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                );
                              }
                              // AI follow-up questions: map to short reply hints
                              const hints = getReplyHints(message.followUpQuestions);
                              return hints.length > 0 ? (
                                <div className="mt-2.5">
                                  <p className="text-[10px] text-muted-foreground mb-1.5 px-0.5">Quick replies:</p>
                                  <div className="flex max-w-full flex-wrap gap-1.5 overflow-hidden">
                                    {hints.map((hint) => (
                                      <button
                                        key={hint}
                                        onClick={() => handleSend(hint)}
                                        className="rounded-full border border-primary/40 bg-primary/8 hover:bg-primary hover:text-white hover:border-primary px-3 py-1 text-[11px] sm:text-xs font-medium text-primary transition-colors"
                                      >
                                        {hint}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              ) : null;
                            })()
                          }
                        </div>

                        {message.role === 'user' && (
                          <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-muted border flex items-center justify-center flex-shrink-0 shadow-sm mt-auto mb-1">
                            <User className="h-3 w-3 sm:h-5 sm:w-5 text-muted-foreground" />
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  
                  {/* Typing Indicator — bouncing dots */}
                  {isTyping && (
                    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="flex gap-2 sm:gap-3 justify-start">
                      <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 shadow-sm mt-auto mb-1">
                        <Bot className="h-3 w-3 sm:h-5 sm:w-5 text-primary-foreground" />
                      </div>
                      <div className="bg-card/95 border border-primary/10 shadow-sm rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5">
                        {[0, 1, 2].map(i => (
                          <motion.span
                            key={i}
                            className="w-2 h-2 rounded-full bg-primary/70 block"
                            animate={{ y: [0, -5, 0] }}
                            transition={{ duration: 0.55, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }}
                          />
                        ))}
                      </div>
                    </motion.div>
                  )}
                  <div ref={messagesEndRef} className="h-px" />
                </div>
              </div>
            </div>

            {/* Input Area & Suggested Questions - FIXED for mobile */}
            <div className="p-2.5 sm:p-4 bg-background/95 backdrop-blur border-t w-full max-w-full overflow-x-hidden shadow-[0_-10px_30px_hsl(var(--background)/0.85)]">
              {messages.length <= 1 && !isTyping && (
                <div className="mb-3 sm:mb-4">
                  <SuggestedQuestions onSelectQuestion={handleSelectQuestion} onSelectCard={handleSelectCard} />
                </div>
              )}

              {/* Reply preview strip */}
              {replyingTo && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 4 }}
                  className="mb-2 flex items-start gap-2 bg-primary/6 border border-primary/20 rounded-lg px-3 py-2"
                >
                  <CornerUpLeft className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-semibold text-primary uppercase tracking-wide">
                      Replying to {replyingTo.role === 'user' ? 'yourself' : 'MediGuard AI'} — correct or add more info
                    </p>
                    <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                      {replyingTo.content.length > 110 ? replyingTo.content.slice(0, 110) + '…' : replyingTo.content}
                    </p>
                  </div>
                  <button
                    onClick={() => setReplyingTo(null)}
                    className="p-0.5 text-muted-foreground/50 hover:text-destructive transition-colors shrink-0"
                    title="Cancel reply"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </motion.div>
              )}

              {/* Image preview */}
              {imagePreview && (
                <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                  className="mb-2 flex items-center gap-2 p-2 bg-muted/50 rounded-lg border flex-wrap sm:flex-nowrap">
                  <img src={imagePreview} alt="preview" className="h-12 w-12 sm:h-14 sm:w-14 rounded-md object-cover border" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{imageFile?.name}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {imageAnalyzing ? 'Analyzing image…' : 'Image ready — add a description or send directly'}
                    </p>
                  </div>
                  <button onClick={() => { setImageFile(null); setImagePreview(null); }}
                    className="p-1 rounded hover:bg-destructive/20 text-muted-foreground hover:text-destructive flex-shrink-0">
                    <X className="h-4 w-4" />
                  </button>
                </motion.div>
              )}

              {/* Location indicator */}
              {userLocation && (
                <div className="mb-1.5 flex items-center gap-1 text-[10px] text-green-600 dark:text-green-400">
                  <MapPin className="h-3 w-3" />
                  <span>{t('chat_location_hint')}</span>
                </div>
              )}

              <div className="mb-2 flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-[11px] sm:text-xs text-muted-foreground">
                <Activity className="h-3.5 w-3.5 text-primary shrink-0" />
                <span className="flex-1 min-w-0">
                  Testing symptoms in chat? Use the Symptom Checker for more accurate structured results.
                </span>
                <Link to="/symptom-checker" className="font-semibold text-primary hover:underline shrink-0">
                  Open
                </Link>
              </div>

              {/* Hidden file input */}
              <input
                ref={imageInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setImageFile(file);
                  const reader = new FileReader();
                  reader.onload = (ev) => setImagePreview(ev.target.result);
                  reader.readAsDataURL(file);
                  e.target.value = '';
                }}
              />

              <div className="flex gap-2 items-center w-full max-w-full">
                {/* Image upload button */}
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="h-10 w-10 sm:h-14 sm:w-14 shrink-0 rounded-lg border-dashed hover:border-primary hover:text-primary"
                  title="Upload image of symptom (rash, skin condition, etc.)"
                  onClick={() => imageInputRef.current?.click()}
                  disabled={isTyping || imageAnalyzing}
                >
                  {imageAnalyzing
                    ? <Loader2 className="h-3 w-3 sm:h-4 sm:w-4 animate-spin" />
                    : <ImagePlus className="h-3 w-3 sm:h-5 sm:w-5" />
                  }
                </Button>

                {/* Voice input button */}
                <VoiceInput
                  onTranscript={handleVoiceTranscript}
                  onListening={setVoiceListening}
                  lang="en-NG"
                  disabled={isTyping || imageAnalyzing}
                  size="md"
                />

                <div className="relative flex-1 min-w-0 max-w-full">
                  <Input
                    placeholder={imagePreview ? t('chat_image_placeholder') : t('chat_placeholder')}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        imageFile ? handleImageSend() : handleSend();
                      }
                    }}
                    className="bg-muted/45 border-input focus-visible:ring-primary h-10 sm:h-14 rounded-xl pl-3 sm:pl-4 pr-10 sm:pr-12 shadow-inner w-full text-base"
                    disabled={isTyping || imageAnalyzing}
                  />
                  <Button
                    onClick={() => imageFile ? handleImageSend() : handleSend()}
                    disabled={(!input.trim() && !imageFile) || isTyping || imageAnalyzing}
                    className="absolute right-1 top-1 bottom-1 rounded-md w-8 h-8 sm:w-11 sm:h-11 p-0 bg-primary hover:bg-primary/90 text-primary-foreground shadow-md transition-transform active:scale-95"
                  >
                    <Send className="h-3 w-3 sm:h-5 sm:w-5" />
                  </Button>
                </div>
              </div>

              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2 text-center px-2">
                {t('chat_info')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatAI;
