import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { useEffect, useState } from 'react'

export default function App({ Component, pageProps }: AppProps) {
  const [theme, setTheme] = useState<'light'|'dark'>(() => {
    try{
      const stored = localStorage.getItem('theme') as 'light'|'dark'|null
      if(stored) return stored
      // follow system preference
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      return prefersDark ? 'dark' : 'light'
    }catch{ return 'light' }
  })

  useEffect(()=>{
    const root = document.documentElement
    if(theme==='dark') root.classList.add('dark')
    else root.classList.remove('dark')
    try{ localStorage.setItem('theme', theme) }catch{}
  },[theme])

  useEffect(()=>{
    // listen to system preference changes and update only if user hasn't set pref
    try{
      const stored = localStorage.getItem('theme')
      if(!window.matchMedia) return
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      const handler = (e: MediaQueryListEvent) => {
        if(stored) return // user has explicit preference
        setTheme(e.matches ? 'dark' : 'light')
      }
      mq.addEventListener?.('change', handler)
      return ()=> mq.removeEventListener?.('change', handler)
    }catch{}
  },[])

  return (
    <div className="min-h-screen">
      <div className="fixed top-4 right-4 z-50">
        <button onClick={()=>{
            // toggle and mark explicit preference
            const next = theme==='dark' ? 'light' : 'dark'
            localStorage.setItem('theme', next)
            setTheme(next)
          }}
          className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-800 text-sm">
          {theme==='dark' ? '亮模式' : '暗模式'}
        </button>
      </div>
      <Component {...pageProps} />
    </div>
  )
}
