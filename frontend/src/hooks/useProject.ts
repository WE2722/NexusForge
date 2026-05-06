import { useState, useEffect } from 'react'
import axios from 'axios'
import { useProjectStore } from '../stores/projectStore'

export function useProjects() {
  const { projects, setProjects, activeProject, setActiveProject } = useProjectStore()
  const [loading, setLoading] = useState(false)

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const { data } = await axios.get('/api/projects')
      setProjects(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const createProject = async (prompt: string) => {
    const { data } = await axios.post('/api/projects', { prompt })
    return data
  }

  const fetchProjectDetail = async (id: string) => {
    const { data } = await axios.get(`/api/projects/${id}`)
    setActiveProject(data)
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  return { projects, loading, createProject, fetchProjectDetail, activeProject }
}
