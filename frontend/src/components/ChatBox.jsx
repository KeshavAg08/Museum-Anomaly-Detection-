import { useState } from 'react'
import { chat } from '../api'

export default function ChatBox() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    const text = input.trim()
    if (!text) return
    setInput('')
    const newMsgs = [...messages, { role: 'user', content: text }]
    setMessages(newMsgs)
    setLoading(true)
    try {
      const { reply } = await chat(text)
      setMessages([...newMsgs, { role: 'assistant', content: reply }])
    } catch (e) {
      setMessages([...newMsgs, { role: 'assistant', content: 'Error contacting AI service.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full border border-slate-600 rounded-lg overflow-hidden bg-slate-700/30 backdrop-blur-sm">
      <div className="flex-1 p-4 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
              </svg>
            </div>
            <p className="text-slate-400 text-sm">Ask me about anomalies, maintenance,</p>
            <p className="text-slate-400 text-sm">or artifact preservation advice.</p>
          </div>
        )}
        {messages.map((m, idx) => (
          <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-lg ${
              m.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-slate-600/50 text-slate-200 border border-slate-500'
            }`}>
              <div className={`text-xs mb-1 ${
                m.role === 'user' ? 'text-blue-200' : 'text-purple-400'
              }`}>
                {m.role === 'user' ? 'You' : 'AI Assistant'}
              </div>
              <div className="text-sm leading-relaxed">{m.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-600/50 border border-slate-500 p-3 rounded-lg">
              <div className="text-xs text-purple-400 mb-1">AI Assistant</div>
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}} />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}} />
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="p-4 bg-slate-800/50 border-t border-slate-600">
        <div className="flex gap-3">
          <input
            className="flex-1 bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && send()}
            placeholder="Ask about anomalies or maintenance..."
            disabled={loading}
          />
          <button 
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded-lg transition-colors duration-200 flex items-center space-x-2" 
            onClick={send} 
            disabled={loading || !input.trim()}
          >
            {loading ? (
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
            <span>{loading ? 'Sending' : 'Send'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}

