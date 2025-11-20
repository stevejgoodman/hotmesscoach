"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Paperclip, Send, Sparkles } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  imageUrl?: string
}

interface UploadedFile {
  name: string
  size: number
  type: string
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hey there! 👋 I'm your Hot Mess Coach - here to help you untangle life's chaos and get things organized. What's on your mind today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  // Cleanup blob URLs when component unmounts
  useEffect(() => {
    return () => {
      messages.forEach((message) => {
        if (message.imageUrl && message.imageUrl.startsWith("blob:")) {
          URL.revokeObjectURL(message.imageUrl)
        }
      })
    }
  }, [])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("/api/uploadfile/", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        setUploadedFile({
          name: file.name,
          size: file.size,
          type: file.type,
        })
      } else {
        console.error("File upload failed")
      }
    } catch (error) {
      console.error("Error uploading file:", error)
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() && !uploadedFile) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage.content,
          model: "gpt-4o-mini",
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Check if response is an image
      const contentType = response.headers.get("content-type")
      if (contentType && contentType.startsWith("image/")) {
        // Handle image response
        const blob = await response.blob()
        const imageUrl = URL.createObjectURL(blob)
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Here's your chart:",
          imageUrl: imageUrl,
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, assistantMessage])
      } else {
        // Handle JSON response
        const data = await response.json()

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response || "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
        }

        setMessages((prev) => [...prev, assistantMessage])
      }
      setUploadedFile(null)
    } catch (error) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Oops! Something went wrong. Please try again.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-primary/10 via-secondary/10 to-accent/10">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Sparkles className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-card-foreground">Hot Mess Coach</h1>
              <p className="text-sm text-muted-foreground">Your chaos-to-clarity companion</p>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="container mx-auto flex flex-1 flex-col px-4 py-6">
        <Card className="flex flex-1 flex-col overflow-hidden border-border/50 bg-card/80 backdrop-blur-sm shadow-xl">
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-card-foreground"
                    }`}
                  >
                    {message.content && (
                      <p className="text-sm leading-relaxed">{message.content}</p>
                    )}
                    {message.imageUrl && (
                      <div className="mt-2">
                        <img
                          src={message.imageUrl}
                          alt="Chart"
                          className="max-w-full rounded-lg"
                        />
                      </div>
                    )}
                    <p
                      className={`mt-1 text-xs ${
                        message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-2xl bg-muted px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 animate-bounce rounded-full bg-primary"></div>
                      <div className="h-2 w-2 animate-bounce rounded-full bg-secondary delay-100"></div>
                      <div className="h-2 w-2 animate-bounce rounded-full bg-accent delay-200"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* File Upload Preview */}
          {uploadedFile && (
            <div className="border-t border-border/50 bg-muted/30 px-4 py-2">
              <div className="flex items-center gap-2 text-sm">
                <Paperclip className="h-4 w-4 text-primary" />
                <span className="text-muted-foreground">{uploadedFile.name}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setUploadedFile(null)}
                  className="ml-auto h-6 px-2 text-xs"
                >
                  Remove
                </Button>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t border-border/50 p-4">
            <div className="flex items-end gap-2">
              <input ref={fileInputRef} type="file" onChange={handleFileSelect} className="hidden" accept="*/*" />
              <Button
                size="icon"
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                className="h-10 w-10 shrink-0 border-border/50"
              >
                <Paperclip className="h-5 w-5" />
              </Button>
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Share what's on your mind..."
                disabled={isLoading}
                className="flex-1 border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground"
              />
              <Button
                size="icon"
                onClick={handleSendMessage}
                disabled={isLoading || (!input.trim() && !uploadedFile)}
                className="h-10 w-10 shrink-0 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
