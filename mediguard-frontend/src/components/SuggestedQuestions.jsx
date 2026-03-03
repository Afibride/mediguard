
import React, { useRef, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const SuggestedQuestions = ({ onSelectQuestion }) => {
  const scrollRef = useRef(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);

  const questions = [
    "I have a fever and cough",
    "I'm experiencing stomach pain",
    "I have a rash",
    "I'm feeling dizzy and weak"
  ];

  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 5);
    }
  };

  useEffect(() => {
    handleScroll();
    window.addEventListener('resize', handleScroll);
    return () => window.removeEventListener('resize', handleScroll);
  }, []);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const { clientWidth } = scrollRef.current;
      const scrollAmount = direction === 'left' ? -clientWidth / 2 : clientWidth / 2;
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  return (
    <div className="relative w-full mb-4 group">
      {/* Left Arrow */}
      {showLeftArrow && (
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm p-1.5 rounded-full shadow-md border hover:bg-background transition-colors"
        >
          <ChevronLeft className="w-5 h-5 text-primary" />
        </button>
      )}

      {/* Scrollable Container */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex gap-3 overflow-x-auto snap-x hide-scrollbar scroll-smooth px-2 py-2"
      >
        {questions.map((question, index) => (
          <motion.button
            key={index}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSelectQuestion(question)}
            className="flex-shrink-0 snap-center bg-primary text-primary-foreground px-5 py-3 rounded-xl shadow-sm hover:shadow-md transition-all font-medium text-sm border border-primary/20 hover:bg-primary/90 min-w-[200px] w-[80vw] sm:w-auto text-left"
          >
            "{question}"
          </motion.button>
        ))}
      </div>

      {/* Right Arrow */}
      {showRightArrow && (
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm p-1.5 rounded-full shadow-md border hover:bg-background transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-primary" />
        </button>
      )}
    </div>
  );
};

export default SuggestedQuestions;
