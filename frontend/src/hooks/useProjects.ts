import { useState, useEffect } from 'react';

export interface Project {
    id: string;
    name: string;
    chatIds: string[];
}

export function useProjects() {
    const [projects, setProjects] = useState<Project[]>([]);

    useEffect(() => {
        const saved = localStorage.getItem('benchside_projects');
        if (saved) {
            try {
                setProjects(JSON.parse(saved));
            } catch (e) {
                console.error('Failed to parse projects', e);
            }
        }
    }, []);

    const saveProjects = (newProjects: Project[]) => {
        setProjects(newProjects);
        localStorage.setItem('benchside_projects', JSON.stringify(newProjects));
    };

    const createProject = (name: string) => {
        const newProject: Project = { id: `proj_${Date.now()}`, name, chatIds: [] };
        saveProjects([...projects, newProject]);
    };

    const deleteProject = (id: string) => {
        saveProjects(projects.filter(p => p.id !== id));
    };

    const renameProject = (id: string, newName: string) => {
        saveProjects(projects.map(p => p.id === id ? { ...p, name: newName } : p));
    };

    const addChatToProject = (projectId: string, chatId: string) => {
        saveProjects(projects.map(p => {
            if (p.id === projectId) {
                if (!p.chatIds.includes(chatId)) {
                    return { ...p, chatIds: [...p.chatIds, chatId] };
                }
            } else {
                // Enforce a chat can only be in one project at a time
                return { ...p, chatIds: p.chatIds.filter(id => id !== chatId) };
            }
            return p;
        }));
    };

    const removeChatFromProject = (projectId: string, chatId: string) => {
        saveProjects(projects.map(p => p.id === projectId ? { ...p, chatIds: p.chatIds.filter(id => id !== chatId) } : p));
    };

    return { projects, createProject, deleteProject, renameProject, addChatToProject, removeChatFromProject };
}
