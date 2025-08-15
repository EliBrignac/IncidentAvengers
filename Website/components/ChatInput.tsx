'use client';

import { useState, useEffect, useRef } from 'react';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

export default function ChatInput() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [typingText, setTypingText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle typing effect
  useEffect(() => {
    if (typingText && isTyping) {
      const timer = setTimeout(() => {
        setTypingText(prev => prev.slice(0, -1) + (prev.slice(-1) === '|' ? '' : '|'));
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [typingText, isTyping]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typingText]);

  const typeMessage = (text: string, index = 0) => {
    if (index <= text.length) {
      const displayText = text.substring(0, index) + (index < text.length ? '|' : '');
      setTypingText(displayText);
      
      if (index < text.length) {
        setTimeout(() => typeMessage(text, index + 1), 75);
      } else {
        setIsTyping(false);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;
    
    // Add user message to chat
    const userMessage: Message = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);
    
    try {
      // Call Flask backend directly
      console.log('Sending request to backend with prompt:', message);
      const response = await fetch('http://127.0.0.1:5000', {
        method: 'POST',
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ prompt: message })
      });

      console.log('Response status:', response.status);
      const responseData = await response.json().catch(() => ({}));
      console.log('Response data:', responseData);
      
      if (!response.ok) {
        throw new Error(responseData.error || `HTTP error! status: ${response.status}`);
      }
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: responseData.error || responseData.output || 'No response from agent'
      };
      
      // Add the message to chat with empty content initially
      setMessages(prev => [...prev, { ...assistantMessage, content: '' }]);
      
      // Start typing effect after a small delay
      setTimeout(() => {
        setIsTyping(true);
        typeMessage(assistantMessage.content);
      }, 100);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto p-4">
      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="whitespace-pre-wrap">
                {index === messages.length - 1 && isTyping 
                  ? typingText 
                  : msg.content.split('\\n').map((line, i, arr) => (
                      <span key={i}>
                        {line}
                        {i < arr.length - 1 && <br />}
                      </span>
                    ))
                }
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3 text-gray-800">
              Thinking...
            </div>
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="flex-1 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          disabled={isLoading || !message.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
}
