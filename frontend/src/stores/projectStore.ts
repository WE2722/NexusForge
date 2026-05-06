import { create } from 'zustand'
import { Project, ProjectSummary } from '../types'

interface ProjectStore {
  projects: ProjectSummary[]
  activeProject: Project | null
  setProjects: (projects: ProjectSummary[]) => void
  setActiveProject: (project: Project | null) => void
  addProject: (project: ProjectSummary) => void
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  activeProject: null,
  setProjects: (projects) => set({ projects }),
  setActiveProject: (activeProject) => set({ activeProject }),
  addProject: (project) => set((state) => ({ projects: [project, ...state.projects] })),
}))
