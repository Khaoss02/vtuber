import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import { WebSocketProvider } from './context/websocket-context'; // ruta correcta a tu contexto WS

const originalConsoleWarn = console.warn;
console.warn = (...args) => {
  if (typeof args[0] === 'string' && args[0].includes('onnxruntime')) {
    return;
  }
  originalConsoleWarn.apply(console, args);
};

if (typeof window !== 'undefined') {
  createRoot(document.getElementById('root')!).render(
    <WebSocketProvider>
      <App />
    </WebSocketProvider>
  );
}
