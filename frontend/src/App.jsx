import { useState } from 'react'
import IndexBuilder from './components/IndexBuilder'
import ChatInterface from './components/ChatInterface'

export default function App() {
  const [step, setStep] = useState('build') // 'build' | 'chat'

  return step === 'build'
    ? <IndexBuilder onComplete={() => setStep('chat')} />
    : <ChatInterface />
}
