import { useState } from 'react'

export default function CodeViewer({ files }: { files: Record<string, string> }) {
  const fileNames = Object.keys(files)
  const [activeFile, setActiveFile] = useState(fileNames[0] || '')

  if (fileNames.length === 0) return <div className="text-muted-foreground text-sm italic">No files generated yet.</div>

  return (
    <div className="border border-border rounded-lg overflow-hidden bg-[#1e1e1e] flex flex-col h-[500px]">
      <div className="flex bg-[#2d2d2d] overflow-x-auto border-b border-[#404040]">
        {fileNames.map(f => (
          <button 
            key={f}
            onClick={() => setActiveFile(f)}
            className={`px-4 py-2 text-sm whitespace-nowrap transition-colors ${activeFile === f ? 'bg-[#1e1e1e] text-white border-t-2 border-primary' : 'text-gray-400 hover:text-gray-200'}`}
          >
            {f}
          </button>
        ))}
      </div>
      <div className="p-4 overflow-auto flex-1 font-mono text-sm text-gray-300 whitespace-pre">
        {files[activeFile]}
      </div>
    </div>
  )
}
