"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, getToken, clearToken } from "@/lib/api";

type Task = {
  id: string;
  task_type: string;
  due_date: string | null;
  status: string;
};

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskType, setTaskType] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    apiFetch("/api/v1/tasks")
      .then((res) => setTasks(res.data.tasks || []))
      .finally(() => setLoading(false));
  }, [router]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!taskType.trim()) return;
    setAdding(true);
    try {
      const res = await apiFetch("/api/v1/tasks", {
        method: "POST",
        body: JSON.stringify({ task_type: taskType, due_date: dueDate || null }),
      });
      setTasks((prev) => [...prev, res.data]);
      setTaskType("");
      setDueDate("");
    } catch {}
    setAdding(false);
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5]">
      <header className="bg-[#1f3d1a] text-white px-6 py-4 flex items-center justify-between shadow-sm relative">
        <h1 className="font-heading text-xl font-bold flex items-center gap-2">🌾 Kisan Dost AI</h1>
        <nav className="hidden sm:flex items-center gap-5 text-sm">
          <Link href="/dashboard" className="opacity-90 hover:opacity-100 transition">Dashboard</Link>
          <Link href="/crops" className="opacity-90 hover:opacity-100 transition">Crops</Link>
          <Link href="/tasks" className="opacity-90 hover:opacity-100 transition">Tasks</Link>
          <Link href="/scan" className="opacity-90 hover:opacity-100 transition">New Scan</Link>
          <Link href="/chat" className="opacity-90 hover:opacity-100 transition">Assistant</Link>
          <button onClick={() => { clearToken(); router.push("/login"); }} className="opacity-90 hover:opacity-100 transition">Logout</button>
        </nav>
        <button onClick={() => setMenuOpen(!menuOpen)} className="sm:hidden text-2xl leading-none">
          {menuOpen ? "✕" : "☰"}
        </button>
        {menuOpen && (
          <div className="absolute top-full left-0 right-0 bg-[#1f3d1a] flex flex-col text-sm shadow-lg sm:hidden z-20">
            <Link href="/dashboard" className="px-6 py-3 border-t border-white/10" onClick={() => setMenuOpen(false)}>Dashboard</Link>
            <Link href="/crops" className="px-6 py-3 border-t border-white/10" onClick={() => setMenuOpen(false)}>Crops</Link>
            <Link href="/tasks" className="px-6 py-3 border-t border-white/10" onClick={() => setMenuOpen(false)}>Tasks</Link>
            <Link href="/scan" className="px-6 py-3 border-t border-white/10" onClick={() => setMenuOpen(false)}>New Scan</Link>
            <Link href="/chat" className="px-6 py-3 border-t border-white/10" onClick={() => setMenuOpen(false)}>Assistant</Link>
            <button onClick={() => { clearToken(); router.push("/login"); }} className="px-6 py-3 border-t border-white/10 text-left">Logout</button>
          </div>
        )}
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10">
        <h2 className="font-heading text-3xl font-extrabold text-[#1f3d1a] mb-6">Farming Tasks</h2>

        <form onSubmit={handleAdd} className="bg-white rounded-2xl p-5 border border-black/5 shadow-sm mb-8 flex flex-col sm:flex-row gap-2">
          <input
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            placeholder="e.g. Watering, Fertilizing, Spraying"
            className="w-full sm:flex-1 px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40"
          />
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="w-full sm:w-auto px-3 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40"
          />
          <button
            type="submit"
            disabled={adding}
            className="w-full sm:w-auto bg-[#1f3d1a] text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-[#2d5527] transition disabled:opacity-50"
          >
            Add
          </button>
        </form>

        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : tasks.length === 0 ? (
          <p className="text-gray-500 text-sm">No tasks yet — add one above.</p>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <div key={task.id} className="bg-white rounded-2xl p-4 border border-black/5 shadow-sm flex items-center justify-between">
                <div>
                  <p className="font-semibold text-[#1f3d1a] capitalize">{task.task_type}</p>
                  {task.due_date && <p className="text-sm text-gray-500">Due {task.due_date}</p>}
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-[#d97706] bg-orange-50 border border-orange-200 rounded-full px-3 py-1">
                  {task.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}