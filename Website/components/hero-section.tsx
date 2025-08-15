"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Mic, Send } from "lucide-react"

interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
}

export function HeroSection() {
  const [prompt, setPrompt] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: prompt,
      role: "user",
      timestamp: new Date(),
    }

    setMessages((prev: Message[]) => [...prev, userMessage])
    setPrompt("")
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:5000', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.output || data.error || 'No response from agent',
        role: "assistant",
        timestamp: new Date(),
      };
      
      setMessages((prev: Message[]) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        role: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev: Message[]) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  if (messages.length > 0) {
    return (
      <section className="min-h-[calc(100vh-80px)] bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col">
        <div className="flex-1 container mx-auto px-4 py-8 max-w-3xl">
          <div className="space-y-6 mb-8">
            {messages.map((message) => (
              <div key={message.id}>
                {message.role === "user" ? (
                  <div className="flex justify-end">
                    <div className="max-w-[80%] bg-white/10 backdrop-blur-md border border-white/20 text-white shadow-lg rounded-2xl px-4 py-3">
                      <p className="text-sm leading-relaxed">{message.content}</p>
                    </div>
                  </div>
                ) : (
                  <div className="w-full">
                    <div className="text-gray-100 text-base leading-relaxed py-4 px-2">{message.content}</div>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="w-full">
                <div className="text-gray-300 py-4 px-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">AI is thinking</span>
                    <div className="flex space-x-1">
                      <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
                      <div
                        className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-white/10 bg-black/20 backdrop-blur-md p-4">
          <form onSubmit={handleSubmit} className="container mx-auto max-w-3xl">
            <div className="relative">
              <div className="flex items-center bg-white/10 backdrop-blur-md border border-white/20 rounded-full p-1 focus-within:bg-white/15 focus-within:border-white/30 transition-all duration-200 shadow-lg">
                <Input
                  type="text"
                  placeholder="Message..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="flex-1 bg-transparent border-0 text-white placeholder-gray-300 text-sm px-4 py-2 focus-visible:ring-0 focus-visible:ring-offset-0"
                />
                <Button
                  type="submit"
                  size="sm"
                  className={`rounded-full w-8 h-8 p-0 transition-all duration-200 ${
                    prompt.trim() && !isLoading
                      ? "bg-white/20 backdrop-blur-md hover:bg-white/30 text-white border border-white/30 shadow-lg"
                      : "bg-white/5 text-gray-500 cursor-not-allowed border border-white/10"
                  }`}
                  disabled={!prompt.trim() || isLoading}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </form>
        </div>
      </section>
    )
  }

  return (
    <section className="min-h-[calc(100vh-80px)] bg-gray-900 flex items-center">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Hero Content */}
          <div className="mb-12">
            <h1 className="text-5xl md:text-6xl font-serif font-bold text-white mb-6 leading-tight">
              What's on the agenda today?
            </h1>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto leading-relaxed">
              Chat with our advanced AI agent for intelligent conversations, creative assistance, and problem-solving
              support.
            </p>
          </div>

          {/* Prompt Input */}
          <form onSubmit={handleSubmit} className="mb-8">
            <div className="relative max-w-2xl mx-auto">
              <div className="flex items-center bg-white/10 backdrop-blur-md border border-white/20 rounded-full p-2 focus-within:border-white/30 focus-within:bg-white/15 transition-all duration-200 shadow-lg">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-gray-300 hover:text-white hover:bg-white/10 p-3 rounded-full transition-all duration-200"
                >
                  <span className="text-lg">+</span>
                </Button>
                <Input
                  type="text"
                  placeholder="Ask anything"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="flex-1 bg-transparent border-0 text-white placeholder-gray-300 text-lg px-4 py-3 focus-visible:ring-0 focus-visible:ring-offset-0"
                />
                <div className="flex items-center space-x-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-gray-300 hover:text-white hover:bg-white/10 p-3 rounded-full transition-all duration-200"
                  >
                    <Mic className="h-5 w-5" />
                  </Button>
                  <Button
                    type="submit"
                    variant="ghost"
                    size="sm"
                    className="text-gray-300 hover:text-white hover:bg-white/10 p-3 rounded-full transition-all duration-200"
                    disabled={!prompt.trim()}
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </div>
              </div>
            </div>
          </form>

          {/* CTA Button */}
          <div className="space-y-4">
            <Button
              size="lg"
              className="bg-green-500 hover:bg-green-600 text-gray-900 font-semibold px-8 py-4 text-lg rounded-full"
              onClick={async () => {
                try {
                  const response = await fetch('http://localhost:5000', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: 'Test message' }),
                  });
                  const data = await response.json();
                  console.log('Test response:', data);
                } catch (error) {
                  console.error('Test error:', error);
                }
              }}
            >
              Test API Connection
            </Button>
            <Button
              size="lg"
              className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-8 py-4 text-lg rounded-full ml-4"
              onClick={() => setMessages([{
                id: '1',
                content: 'Test message',
                role: 'user',
                timestamp: new Date()
              }])}
            >
              Test UI
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="mt-12 flex items-center justify-center space-x-8 text-gray-400 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Powered by advanced AI</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>Secure & private</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>24/7 available</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
