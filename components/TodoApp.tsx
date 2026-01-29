import React, { useEffect, useState } from 'react'

export type Todo = {
  id: string
  text: string
  done: boolean
  priority?: 'low'|'medium'|'high'
  due?: string | null
}

export default function TodoApp(){
  const [todos, setTodos] = useState<Todo[]>([])
  const [text, setText] = useState('')
  const [filter, setFilter] = useState<'all'|'active'|'done'>('all')

  useEffect(()=>{
    try{
      const raw = localStorage.getItem('todos')
      if(raw) setTodos(JSON.parse(raw))
    }catch(e){}
  },[])

  useEffect(()=>{
    localStorage.setItem('todos', JSON.stringify(todos))
  },[todos])

  function add(){
    if(!text.trim()) return
    const t: Todo = { id: Date.now().toString(), text: text.trim(), done:false }
    setTodos(prev=>[t, ...prev])
    setText('')
  }

  function toggle(id:string){
    setTodos(prev=>prev.map(t=> t.id===id? {...t, done: !t.done} : t))
  }

  function remove(id:string){
    setTodos(prev=>prev.filter(t=>t.id!==id))
  }

  const visible = todos.filter(t=> filter==='all' ? true : filter==='active' ? !t.done : t.done)

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h1 className="text-2xl font-semibold mb-4">我的待辦清單</h1>
      <div className="flex gap-2 mb-4">
        <input className="flex-1 border rounded px-3 py-2" placeholder="新增待辦..." value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=> e.key==='Enter' && add()} />
        <button className="bg-primary-500 text-white px-4 py-2 rounded" onClick={add}>新增</button>
      </div>
      <div className="flex gap-2 mb-4">
        <button className={`px-3 py-1 rounded ${filter==='all'? 'bg-gray-200':''}`} onClick={()=>setFilter('all')}>全部</button>
        <button className={`px-3 py-1 rounded ${filter==='active'? 'bg-gray-200':''}`} onClick={()=>setFilter('active')}>未完成</button>
        <button className={`px-3 py-1 rounded ${filter==='done'? 'bg-gray-200':''}`} onClick={()=>setFilter('done')}>已完成</button>
      </div>

      <ul className="space-y-2">
        {visible.map(t=> (
          <li key={t.id} className="flex items-center justify-between border p-3 rounded">
            <div className="flex items-center gap-3">
              <input type="checkbox" checked={t.done} onChange={()=>toggle(t.id)} />
              <div className={`${t.done? 'line-through text-gray-400':''}`}>{t.text}</div>
            </div>
            <div className="flex items-center gap-2">
              <button className="text-sm text-red-500" onClick={()=>remove(t.id)}>刪除</button>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-4 text-sm text-gray-500">共 {todos.length} 項</div>
    </div>
  )
}
