import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { useEffect, useState } from 'react'

export default function App({ Component, pageProps }: AppProps) {
  const [theme, setTheme] = useState<'light'|'dark'>(() => {
    try{
      return (localStorage.getItem('theme') as 'light'|'dark') || 'light'
    }catch{ return 'light' }
  })

  useEffect(()=>{
    const root = document.documentElement
    if(theme==='dark') root.classList.add('dark')
    else root.classList.remove('dark')
    try{ localStorage.setItem('theme', theme) }catch{}
  },[theme])

  return (
    <div className="min-h-screen">
      <div className="fixed top-4 right-4 z-50">
        <button onClick={()=>setTheme(t=> t==='dark' ? 'light' : 'dark')}
          className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-800 text-sm">
          {theme==='dark' ? '亮模式' : '暗模式'}
        </button>
      </div>
      <Component {...pageProps} />
    </div>
  )
}
