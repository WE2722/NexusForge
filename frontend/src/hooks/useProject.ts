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
    try {
      const { data } = await axios.get(`/api/projects/${id}`)
      setActiveProject(data)
    } catch (e) {
      console.error(e)
    }
  }

  const launchProject = async (id: string) => {
    const { data } = await axios.post(`/api/projects/${id}/launch`)
    return data
  }

  const exportProject = async (id: string) => {
    const resp = await axios.get(`/api/projects/${id}/export`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([resp.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${id}.zip`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const pauseProject = async (id: string) => {
    await axios.post(`/api/projects/${id}/pause`)
  }

  const resumeProject = async (id: string) => {
    await axios.post(`/api/projects/${id}/resume`)
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  return {
    projects,
    loading,
    createProject,
    fetchProjectDetail,
    activeProject,
    launchProject,
    exportProject,
    pauseProject,
    resumeProject,
  }
}
