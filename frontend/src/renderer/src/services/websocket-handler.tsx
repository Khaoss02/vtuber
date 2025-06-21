import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { wsService, MessageEvent } from '@/services/websocket-service';
import { WebSocketContext, defaultWsUrl, defaultBaseUrl } from '@/context/websocket-context';
// Importa solo lo que uses realmente en tu proyecto

function WebSocketHandler({ children }: { children: React.ReactNode }) {
  const [wsState, setWsState] = useState<'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'>('CLOSED');
  const [wsUrl, setWsUrl] = React.useState<string>(defaultWsUrl);
  const [baseUrl, setBaseUrl] = React.useState<string>(defaultBaseUrl);

  // Función que maneja los mensajes entrantes del websocket
  const handleWebSocketMessage = useCallback((message: MessageEvent) => {
    console.log('Mensaje recibido:', message);

    switch (message.type) {
      case 'control':
        if (message.text === 'start-mic') {
          console.log('Iniciar micrófono');
          // startMic();
        } else if (message.text === 'stop-mic') {
          console.log('Detener micrófono');
          // stopMic();
        }
        break;
      // Añade el resto de casos que uses
      default:
        console.warn('Tipo de mensaje desconocido:', message.type);
    }
  }, []);

  useEffect(() => {
    wsService.connect(wsUrl);
  }, [wsUrl]);

  useEffect(() => {
    const stateSub = wsService.onStateChange(setWsState);
    const messageSub = wsService.onMessage(handleWebSocketMessage);

    return () => {
      stateSub.unsubscribe();
      messageSub.unsubscribe();
    };
  }, [handleWebSocketMessage]);

  const contextValue = useMemo(() => ({
    sendMessage: wsService.sendMessage.bind(wsService),
    wsState,
    reconnect: () => wsService.connect(wsUrl),
    wsUrl,
    setWsUrl,
    baseUrl,
    setBaseUrl,
  }), [wsState, wsUrl, baseUrl]);

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export default WebSocketHandler;
