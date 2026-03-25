import { useEffect, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

function App() {
  const [data, setData] = useState({ items: [], total: 0 })
  const [name, setName] = useState('')
  const [color, setColor] = useState('')
  const [inSeason, setInSeason] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    const params = { page, page_size: 10 }
    if (name) params.name = name
    if (color) params.color = color
    if (inSeason !== '') params.in_season = inSeason

    axios.get(`${API}/fruit`, { params })
      .then(res => setData(res.data))
      .catch(console.error)
  }, [name, color, inSeason, page])

  const handleFilter = (setter) => (e) => {
    setter(e.target.value)
    setPage(1)
  }

  const totalPages = Math.ceil(data.total / 10) || 1

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #fdf6e3 0%, #e8f5e9 50%, #fff3e0 100%)',
      padding: '2rem 1rem',
      fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
    }}>
      <div style={{ maxWidth: 720, margin: '0 auto' }}>

        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            fontSize: '2.4rem',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #e65100, #f57c00, #43a047)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: 0,
          }}>
            Fruit App
          </h1>
          <p style={{ color: '#7c8a6e', fontSize: '0.95rem', marginTop: '0.3rem' }}>
            Search, filter &amp; explore fruits with fuzzy matching
          </p>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.85)',
          backdropFilter: 'blur(10px)',
          borderRadius: 16,
          padding: '1.5rem',
          boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
          marginBottom: '1.5rem',
        }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Search by name (e.g. app, aPp, aple)..."
              value={name}
              onChange={handleFilter(setName)}
              style={{
                flex: 2, minWidth: 180, padding: '0.7rem 1rem', fontSize: '0.95rem',
                border: '2px solid #c8e6c9', borderRadius: 10, outline: 'none',
                background: '#f1f8e9', color: '#33691e', transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = '#66bb6a'}
              onBlur={e => e.target.style.borderColor = '#c8e6c9'}
            />
            <input
              type="text"
              placeholder="Color (e.g. red)"
              value={color}
              onChange={handleFilter(setColor)}
              style={{
                flex: 1, minWidth: 120, padding: '0.7rem 1rem', fontSize: '0.95rem',
                border: '2px solid #ffe0b2', borderRadius: 10, outline: 'none',
                background: '#fff8e1', color: '#e65100', transition: 'border-color 0.2s',
              }}
              onFocus={e => e.target.style.borderColor = '#ffa726'}
              onBlur={e => e.target.style.borderColor = '#ffe0b2'}
            />
            <select
              value={inSeason}
              onChange={handleFilter(setInSeason)}
              style={{
                padding: '0.7rem 1rem', fontSize: '0.95rem',
                border: '2px solid #b3e5fc', borderRadius: 10, outline: 'none',
                background: '#e1f5fe', color: '#0277bd', cursor: 'pointer',
              }}
            >
              <option value="">All seasons</option>
              <option value="true">In season</option>
              <option value="false">Out of season</option>
            </select>
          </div>
        </div>

        <p style={{ color: '#8d6e63', marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: 600 }}>
          {data.total} result{data.total !== 1 ? 's' : ''} found
        </p>

        {data.items.length === 0 ? (
          <div style={{
            textAlign: 'center', padding: '3rem 0', color: '#a5a5a5',
            background: 'rgba(255,255,255,0.6)', borderRadius: 12,
          }}>
            <p style={{ fontSize: '2rem', margin: 0 }}>No fruits found.</p>
          </div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {data.items.map((f, i) => {
              const colors = [
                { bg: '#fff3e0', border: '#ffe0b2', accent: '#e65100' },
                { bg: '#e8f5e9', border: '#c8e6c9', accent: '#2e7d32' },
                { bg: '#e3f2fd', border: '#bbdefb', accent: '#1565c0' },
                { bg: '#fce4ec', border: '#f8bbd0', accent: '#c62828' },
                { bg: '#f3e5f5', border: '#e1bee7', accent: '#6a1b9a' },
              ]
              const c = colors[i % colors.length]
              return (
                <li key={f.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.85rem 1.2rem', marginBottom: '0.6rem',
                  border: `2px solid ${c.border}`, borderRadius: 12,
                  background: c.bg, transition: 'transform 0.15s, box-shadow 0.15s',
                }}
                  onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.08)' }}
                  onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}
                >
                  <strong style={{ fontSize: '1.08rem', color: c.accent, minWidth: 110 }}>{f.name}</strong>
                  <span style={{
                    color: '#6d4c41', textTransform: 'capitalize', fontWeight: 500,
                    background: 'rgba(255,255,255,0.7)', padding: '0.2rem 0.7rem', borderRadius: 8,
                  }}>{f.color}</span>
                  <span style={{
                    padding: '0.25rem 0.8rem', borderRadius: 20, fontSize: '0.82rem', fontWeight: 600,
                    background: f.in_season
                      ? 'linear-gradient(135deg, #a5d6a7, #66bb6a)'
                      : 'linear-gradient(135deg, #ef9a9a, #e57373)',
                    color: '#fff',
                    boxShadow: f.in_season
                      ? '0 2px 8px rgba(76,175,80,0.3)'
                      : '0 2px 8px rgba(229,115,115,0.3)',
                  }}>
                    {f.in_season ? 'In Season' : 'Out of Season'}
                  </span>
                </li>
              )
            })}
          </ul>
        )}

        <div style={{
          display: 'flex', gap: '0.75rem', justifyContent: 'center', alignItems: 'center',
          marginTop: '1.8rem',
        }}>
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            style={{
              padding: '0.5rem 1.4rem', fontSize: '0.9rem', fontWeight: 600,
              borderRadius: 10, border: 'none', cursor: page === 1 ? 'not-allowed' : 'pointer',
              background: page === 1 ? '#e0e0e0' : 'linear-gradient(135deg, #ff8a65, #f4511e)',
              color: page === 1 ? '#999' : '#fff',
              boxShadow: page === 1 ? 'none' : '0 3px 12px rgba(244,81,30,0.3)',
              transition: 'all 0.2s',
            }}
          >
            Prev
          </button>
          <span style={{ color: '#5d4037', fontSize: '0.9rem', fontWeight: 600 }}>
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => p + 1)}
            style={{
              padding: '0.5rem 1.4rem', fontSize: '0.9rem', fontWeight: 600,
              borderRadius: 10, border: 'none', cursor: page >= totalPages ? 'not-allowed' : 'pointer',
              background: page >= totalPages ? '#e0e0e0' : 'linear-gradient(135deg, #66bb6a, #43a047)',
              color: page >= totalPages ? '#999' : '#fff',
              boxShadow: page >= totalPages ? 'none' : '0 3px 12px rgba(67,160,71,0.3)',
              transition: 'all 0.2s',
            }}
          >
            Next
          </button>
        </div>

      </div>
    </div>
  )
}

export default App
