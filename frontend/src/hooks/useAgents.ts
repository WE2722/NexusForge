import { useState, useEffect } from 'react'
import axios from 'axios'
import { AgentInfo } from '../types'

export function useAgents() {
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const { data } = await axios.get('/api/agents')
        setAgents(data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchAgents()
  }, [])

  return { agents, loading }
}
