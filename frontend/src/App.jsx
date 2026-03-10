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
    <div style={{ maxWidth: 700, margin: '2rem auto', fontFamily: 'sans-serif', padding: '0 1rem' }}>
      <h1 style={{ marginBottom: '1.5rem' }}>Fruit Explorer</h1>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search by name (e.g. app, aPp, aple)..."
          value={name}
          onChange={handleFilter(setName)}
          style={{ flex: 2, padding: '0.6rem 0.8rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: 6 }}
        />
        <input
          type="text"
          placeholder="Color (e.g. red)"
          value={color}
          onChange={handleFilter(setColor)}
          style={{ flex: 1, padding: '0.6rem 0.8rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: 6 }}
        />
        <select
          value={inSeason}
          onChange={handleFilter(setInSeason)}
          style={{ padding: '0.6rem 0.8rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: 6 }}
        >
          <option value="">All seasons</option>
          <option value="true">In season</option>
          <option value="false">Out of season</option>
        </select>
      </div>

      <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>
        {data.total} result{data.total !== 1 ? 's' : ''}
      </p>

      {data.items.length === 0 ? (
        <p style={{ color: '#999', textAlign: 'center', padding: '3rem 0' }}>No fruits found.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {data.items.map(f => (
            <li key={f.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '0.75rem 1rem', marginBottom: '0.5rem',
              border: '1px solid #e5e5e5', borderRadius: 8, background: '#fafafa'
            }}>
              <strong style={{ fontSize: '1.05rem', minWidth: 100 }}>{f.name}</strong>
              <span style={{ color: '#555', textTransform: 'capitalize' }}>{f.color}</span>
              <span style={{
                padding: '0.2rem 0.7rem', borderRadius: 20, fontSize: '0.82rem', fontWeight: 500,
                background: f.in_season ? '#d4edda' : '#f8d7da',
                color: f.in_season ? '#155724' : '#721c24'
              }}>
                {f.in_season ? 'In Season' : 'Out of Season'}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', alignItems: 'center', marginTop: '1.5rem' }}>
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
          style={{ padding: '0.4rem 1rem', cursor: page === 1 ? 'not-allowed' : 'pointer', borderRadius: 6, border: '1px solid #ccc' }}
        >
          Prev
        </button>
        <span style={{ color: '#555', fontSize: '0.9rem' }}>Page {page} of {totalPages}</span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage(p => p + 1)}
          style={{ padding: '0.4rem 1rem', cursor: page >= totalPages ? 'not-allowed' : 'pointer', borderRadius: 6, border: '1px solid #ccc' }}
        >
          Next
        </button>
      </div>
    </div>
  )
}

export default App
