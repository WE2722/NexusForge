import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import type { ChatMessage, ChatResponse } from '../types'

interface UseChatReturn {
  messages: ChatMessage[]
  sendMessage: (msg: string) => Promise<void>
  isLoading: boolean
  isStreaming: boolean
  error: string | null
  clearHistory: () => Promise<void>
  reconnect: () => void
}

export function useChat(projectId: string): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const messageIdsRef = useRef<Set<string>>(new Set())

  // Load history on mount
  useEffect(() => {
    if (!projectId) return
    loadHistory()
  }, [projectId])

  // WebSocket connection
  useEffect(() => {
    if (!projectId) return
    connectWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
    }
  }, [projectId])

  const loadHistory = async () => {
    try {
      const { data } = await axios.get(`/api/projects/${projectId}/chat/history`)
      if (data.messages) {
        setMessages(data.messages)
      }
    } catch (e) {
      console.error('Failed to load chat history:', e)
    }
  }

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://${window.location.hostname}:8000/api/ws/projects/${projectId}/chat`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setError(null)
        setIsStreaming(false)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'status') {
            // Update loading state with status messages
            setIsStreaming(true)
          } else if (data.type === 'agent_activity') {
            // Could update UI with agent progress
            setIsStreaming(true)
          } else if (data.type === 'response') {
            // Final response
            const assistantMsg: ChatMessage = {
              role: 'assistant',
              content: data.content,
              timestamp: data.timestamp || new Date().toISOString(),
              intent: data.intent,
              changes: data.changes,
              agents_involved: data.agents_involved,
              status: data.status,
            }

            // Deduplication
            const msgKey = `${assistantMsg.role}-${assistantMsg.content.slice(0, 50)}-${assistantMsg.timestamp}`
            if (!messageIdsRef.current.has(msgKey)) {
              messageIdsRef.current.add(msgKey)
              setMessages(prev => [...prev, assistantMsg])
            }

            setIsLoading(false)
            setIsStreaming(false)
          } else if (data.type === 'error') {
            setError(data.content)
            setIsLoading(false)
            setIsStreaming(false)
          }
        } catch (e) {
          console.error('WS message parse error:', e)
        }
      }

      ws.onclose = () => {
        setIsStreaming(false)
        // Auto-reconnect after 3 seconds
        reconnectTimerRef.current = setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.CLOSED) {
            connectWebSocket()
          }
        }, 3000)
      }

      ws.onerror = () => {
        // WebSocket failed, will fallback to REST
        setIsStreaming(false)
      }

      wsRef.current = ws
    } catch {
      // WebSocket not available, REST fallback is fine
    }
  }

  const sendMessage = useCallback(async (msg: string) => {
    if (!msg.trim() || isLoading) return

    setError(null)
    setIsLoading(true)

    // Optimistic UI: show user message immediately
    const userMsg: ChatMessage = {
      role: 'user',
      content: msg,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])

    // Try WebSocket first
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ message: msg }))
        // Response will come via ws.onmessage
        return
      } catch {
        // Fall through to REST
      }
    }

    // REST fallback
    try {
      const { data } = await axios.post<ChatResponse>(
        `/api/projects/${projectId}/chat`,
        { message: msg }
      )

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        intent: data.intent,
        changes: data.changes,
        agents_involved: data.agents_involved,
        status: data.status,
      }

      setMessages(prev => [...prev, assistantMsg])
    } catch (e: any) {
      const errMsg = e.response?.data?.detail || e.message || 'Failed to send message'
      setError(errMsg)

      // Add error message to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${errMsg}`,
        timestamp: new Date().toISOString(),
        status: 'failed',
      }])
    } finally {
      setIsLoading(false)
    }
  }, [projectId, isLoading])

  const clearHistory = useCallback(async () => {
    try {
      await axios.delete(`/api/projects/${projectId}/chat/history`)
      setMessages([])
      messageIdsRef.current.clear()
    } catch (e) {
      console.error('Failed to clear history:', e)
    }
  }, [projectId])

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    connectWebSocket()
  }, [projectId])

  return {
    messages,
    sendMessage,
    isLoading,
    isStreaming,
    error,
    clearHistory,
    reconnect,
  }
}
