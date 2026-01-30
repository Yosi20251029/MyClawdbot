import dynamic from 'next/dynamic'
import TodoApp from '../components/TodoApp'

export default function Dashboard(){
  return (
    <main className="min-h-screen p-6" style={{backgroundColor:'var(--page)'}}>
      <div className="max-w-7xl mx-auto grid gap-6 grid-cols-1 md:grid-cols-3">
        <section className="md:col-span-1">
          <h2 className="text-xl font-semibold mb-4">任務</h2>
          <TodoApp />
        </section>
        <section className="md:col-span-2">
          <h2 className="text-xl font-semibold mb-4">看板 / 日曆 / 地圖（開發中）</h2>
          <div className="p-4 card card-border rounded">正在建立中—下一步會加入 Kanban、Calendar 與 Map 模組。</div>
        </section>
      </div>
    </main>
  )
}
