import { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import ChatArea from './ChatArea'

// Convert raw index.json format → sidebar schema format
function parseSchema(indexJson) {
  return [
    {
      name: 'california_schools',
      tables: Object.entries(indexJson).map(([tableName, meta]) => ({
        name: tableName,
        rowCount: meta.row_count,
        columns: (meta.columns || []).map(col => ({
          name: col[1],
          type: col[2],
          pk: col[5] === 1,
        })),
        foreignKeys: meta.foreign_keys || [],
      })),
    },
  ]
}

export default function ChatInterface() {
  const [schema, setSchema] = useState(null)

  useEffect(() => {
    // Fetch schema from backend (or fall back to a static mock)
    fetch('/api/schema')
      .then(r => r.json())
      .then(data => setSchema(parseSchema(data)))
      .catch(() => {
        // Fallback mock so the UI is still usable without a backend
        setSchema([
          {
            name: 'california_schools',
            tables: [
              {
                name: 'frpm',
                rowCount: 9986,
                columns: [
                  { name: 'CDSCode', type: 'TEXT', pk: true },
                  { name: 'Academic Year', type: 'TEXT', pk: false },
                  { name: 'County Name', type: 'TEXT', pk: false },
                  { name: 'School Name', type: 'TEXT', pk: false },
                  { name: 'Enrollment (K-12)', type: 'REAL', pk: false },
                  { name: 'Free Meal Count (K-12)', type: 'REAL', pk: false },
                  { name: 'Charter School (Y/N)', type: 'INTEGER', pk: false },
                ],
              },
              {
                name: 'satscores',
                rowCount: 2269,
                columns: [
                  { name: 'cds', type: 'TEXT', pk: true },
                  { name: 'sname', type: 'TEXT', pk: false },
                  { name: 'dname', type: 'TEXT', pk: false },
                  { name: 'cname', type: 'TEXT', pk: false },
                  { name: 'enroll12', type: 'INTEGER', pk: false },
                  { name: 'AvgScrMath', type: 'INTEGER', pk: false },
                  { name: 'AvgScrRead', type: 'INTEGER', pk: false },
                  { name: 'AvgScrWrite', type: 'INTEGER', pk: false },
                  { name: 'NumGE1500', type: 'INTEGER', pk: false },
                ],
              },
              {
                name: 'schools',
                rowCount: 17686,
                columns: [
                  { name: 'CDSCode', type: 'TEXT', pk: true },
                  { name: 'County', type: 'TEXT', pk: false },
                  { name: 'District', type: 'TEXT', pk: false },
                  { name: 'School', type: 'TEXT', pk: false },
                  { name: 'City', type: 'TEXT', pk: false },
                  { name: 'Zip', type: 'TEXT', pk: false },
                  { name: 'FundingType', type: 'TEXT', pk: false },
                  { name: 'Latitude', type: 'REAL', pk: false },
                  { name: 'Longitude', type: 'REAL', pk: false },
                ],
              },
            ],
          },
        ])
      })
  }, [])

  if (!schema) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-muted)' }}>
        Loading schema…
      </div>
    )
  }

  return (
    <div className="chat-layout">
      <Sidebar schema={schema} />
      <ChatArea />
    </div>
  )
}
