import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { wsService, MessageEvent } from '../services/websocket-service';

type WsState = 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED';

interface WebSocketContextProps {
  sendMessage: (msg: object) => void;
  wsState: WsState;
  reconnect: () => void;
  wsUrl: string;
  setWsUrl: React.Dispatch<React.SetStateAction<string>>;
  baseUrl: string;
  setBaseUrl: React.Dispatch<React.SetStateAction<string>>;
}

const defaultWsUrl = 'ws://localhost:8000/ws';
const defaultBaseUrl = 'http://localhost:8000';

export const WebSocketContext = createContext<WebSocketContextProps | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [wsState, setWsState] = useState<WsState>('CLOSED');
  const [wsUrl, setWsUrl] = useState<string>(defaultWsUrl);
  const [baseUrl, setBaseUrl] = useState<string>(defaultBaseUrl);

  useEffect(() => {
    wsService.connect(wsUrl);

    const stateSub = wsService.onStateChange(setWsState);
    const msgSub = wsService.onMessage((msg: MessageEvent) => {
      // Aquí puedes manejar mensajes globales si quieres
      // O pasar a otros contextos o eventos
      console.log('WS Global Message:', msg);
    });

    return () => {
      stateSub.unsubscribe();
      msgSub.unsubscribe();
      wsService.disconnect();
    };
  }, [wsUrl]);

  const sendMessage = useCallback((msg: object) => {
    wsService.sendMessage(msg);
  }, []);

  const reconnect = useCallback(() => {
    wsService.connect(wsUrl);
  }, [wsUrl]);

  return (
    <WebSocketContext.Provider value={{
      sendMessage,
      wsState,
      reconnect,
      wsUrl,
      setWsUrl,
      baseUrl,
      setBaseUrl,
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextProps => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export { defaultWsUrl, defaultBaseUrl };
