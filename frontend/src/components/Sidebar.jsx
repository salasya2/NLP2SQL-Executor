import { useState } from 'react'

const TYPE_COLOR = {
  TEXT: '#818cf8',
  INTEGER: '#34d399',
  REAL: '#fbbf24',
  DATE: '#f472b6',
}

function ColumnList({ columns }) {
  return (
    <div className="table-columns">
      {columns.map(col => (
        <div className="col-item" key={col.name}>
          {col.pk && <span className="col-pk" title="Primary Key">🔑</span>}
          <span className="col-name">{col.name}</span>
          <span
            className="col-type"
            style={{ color: TYPE_COLOR[col.type] || 'var(--text-muted)' }}
          >
            {col.type || '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

function TableItem({ table }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={`table-item ${open ? 'open' : ''}`}>
      <div className="table-item-header" onClick={() => setOpen(o => !o)}>
        <span className="table-icon">▦</span>
        <span className="table-name">{table.name}</span>
        <span className="table-row-count">{table.rowCount?.toLocaleString() ?? ''}</span>
        <span className="table-chevron">▶</span>
      </div>
      <ColumnList columns={table.columns} />
    </div>
  )
}

function DbItem({ db }) {
  const [open, setOpen] = useState(true)
  return (
    <div className={`db-item ${open ? 'open' : ''}`}>
      <div className="db-item-header" onClick={() => setOpen(o => !o)}>
        <span className="db-icon">🗄️</span>
        <span className="db-name">{db.name}</span>
        <span className="db-badge">{db.tables.length} tables</span>
        <span className="db-chevron">▶</span>
      </div>
      <div className="db-tables">
        {db.tables.map(t => <TableItem key={t.name} table={t} />)}
      </div>
    </div>
  )
}

export default function Sidebar({ schema }) {
  return (
    <aside className="sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo-icon">🔍</div>
        <div>
          <div className="sidebar-logo-text">CHESS SQL</div>
          <div className="sidebar-subtitle">Schema Explorer</div>
        </div>
      </div>

      {/* Body */}
      <div className="sidebar-body">
        <div className="sidebar-section-label">Databases</div>
        {schema.map(db => <DbItem key={db.name} db={db} />)}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="index-status">
          <span className="index-status-dot" />
          index.json loaded
        </div>
      </div>
    </aside>
  )
}
