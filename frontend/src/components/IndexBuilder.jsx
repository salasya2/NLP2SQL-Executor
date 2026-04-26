import { useState, useRef } from 'react'

const STEPS = [
  'Uploading files…',
  'Connecting to database…',
  'Reading schema & tables…',
  'Sampling column values…',
  'Enriching with descriptions…',
  'Writing index.json…',
]

export default function IndexBuilder({ onComplete }) {
  const [dbFile, setDbFile] = useState(null)
  const [csvFiles, setCsvFiles] = useState([])
  const [building, setBuilding] = useState(false)
  const [progress, setProgress] = useState(0)         // 0-100
  const [stepIdx, setStepIdx] = useState(-1)          // current step
  const [done, setDone] = useState(false)
  const [errorMsg, setErrorMsg] = useState(null)

  const dbInputRef = useRef(null)
  const csvInputRef = useRef(null)

  async function handleBuild() {
    if (!dbFile) return
    setBuilding(true)
    setProgress(0)
    setStepIdx(0)
    setDone(false)
    setErrorMsg(null)

    try {
      let localStep = 0
      const stepInterval = setInterval(() => {
        localStep++
        if (localStep < STEPS.length) {
          setStepIdx(localStep)
          setProgress(Math.round((localStep / STEPS.length) * 85))
        } else {
          clearInterval(stepInterval)
        }
      }, 700)

      const formData = new FormData()
      formData.append('db_file', dbFile)
      
      if (csvFiles) {
        Array.from(csvFiles).forEach((file) => {
          formData.append('csv_files', file)
        })
      }

      const res = await fetch('/api/build-index', {
        method: 'POST',
        body: formData,
      })

      clearInterval(stepInterval)

      if (!res.ok) {
        let errMsg = 'Build failed'
        try {
            const errData = await res.json()
            errMsg = errData.detail || errMsg
        } catch(e) {}
        throw new Error(errMsg)
      }

      setStepIdx(STEPS.length - 1)
      setProgress(100)
      setDone(true)
    } catch (err) {
      setErrorMsg(err.message)
      setStepIdx(-1)
      setProgress(0)
    } finally {
      setBuilding(false)
    }
  }

  return (
    <div className="builder-page">
      <div className="builder-card">
        {/* Logo */}
        <div className="builder-logo">
          <div className="builder-logo-icon">🔍</div>
          <span className="builder-logo-text">CHESS SQL</span>
        </div>

        {/* Title */}
        <h1 className="builder-title">
          Step 1 — <span>Build Index</span>
        </h1>
        <p className="builder-desc">
          Before querying your database in natural language, you need to build a
          schema index. This process scans your SQLite database, extracts tables,
          columns, sample values, and foreign keys into a single{' '}
          <code style={{ color: 'var(--accent-light)', fontSize: '0.85em' }}>index.json</code> file.
        </p>

        {/* What it does */}
        <ul className="builder-step-list">
          {['Extract schema metadata', 'Sample column values', 'Map foreign key relationships'].map((s, i) => (
            <li className="builder-step-item" key={i}>
              <span className="builder-step-dot">{i + 1}</span>
              {s}
            </li>
          ))}
        </ul>

        {errorMsg && (
          <div className="build-error" style={{ color: 'red', marginBottom: '1rem', background: 'rgba(255,0,0,0.1)', padding: '0.5rem', borderRadius: '4px' }}>
            ⚠️ Error: {errorMsg}
          </div>
        )}

        {/* DB Upload Input */}
        <div className="builder-input-group">
          <label className="builder-input-label">SQLite Database File</label>
          <input
            type="file"
            accept=".sqlite,.db"
            ref={dbInputRef}
            onChange={e => setDbFile(e.target.files[0])}
            disabled={building || done}
            className="builder-input"
            style={{ padding: '0.5rem', cursor: 'pointer' }}
          />
        </div>

        {/* Description CSVs Input */}
        <div className="builder-input-group">
          <label className="builder-input-label">Value Description CSVs (Optional)</label>
          <input
            type="file"
            multiple
            accept=".csv"
            ref={csvInputRef}
            onChange={e => setCsvFiles(e.target.files)}
            disabled={building || done}
            className="builder-input"
            style={{ padding: '0.5rem', cursor: 'pointer' }}
          />
          <p style={{fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem'}}>
            Select multiple .csv files at once if your database has multiple tables.
          </p>
        </div>

        {/* Button */}
        {!done && (
          <button
            id="btn-build-index"
            className="btn-build"
            onClick={handleBuild}
            disabled={building || !dbFile}
          >
            {building ? '⚙️  Uploading & Building…' : '🚀  Upload & Build index.json'}
          </button>
        )}

        {/* Progress */}
        {(building || (done && progress === 100)) && (
          <div className="build-progress">
            <div className="build-progress-label">
              <span>{done ? 'Complete!' : 'Building…'}</span>
              <span>{progress}%</span>
            </div>
            <div className="build-progress-bar">
              <div className="build-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="build-progress-steps">
              {STEPS.map((s, i) => (
                <div
                  key={i}
                  className={`build-progress-step ${i < stepIdx ? 'done' : i === stepIdx ? 'active' : ''}`}
                >
                  <span className="step-icon">
                    {i < stepIdx ? '✓' : i === stepIdx ? '›' : '○'}
                  </span>
                  {s}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Success */}
        {done && (
          <>
            <div className="build-success">
              <span className="build-success-icon">✅</span>
              <span className="build-success-text">
                index.json built and Active Database updated successfully!
              </span>
            </div>
            <button id="btn-continue-to-chat" className="btn-continue" onClick={onComplete}>
              Continue to Query Interface →
            </button>
          </>
        )}
      </div>
    </div>
  )
}
