import {
  createContext, useContext, useState, useMemo, useCallback,
} from 'react';
// import { Message } from '@/services/websocket-service'; // Ajusta la ruta según tu proyecto
// Define Message and HistoryInfo types here if not exported from './websocket-context'
export interface Message {
  id: string;
  content: string;
  role: 'human' | 'ai';
  timestamp: string;
  name?: string;
  avatar?: string;
}

export interface HistoryInfo {
  uid: string;
  latest_message: {
    content: string;
    role: 'human' | 'ai';
    timestamp: string;
  } | null;
  timestamp: string;
}

/**
 * Estado y funciones del contexto de historial de chat
 */
interface ChatHistoryState {
  messages: Message[];
  historyList: HistoryInfo[];
  currentHistoryUid: string | null;
  appendHumanMessage: (content: string) => void;
  appendAIMessage: (content: string, name?: string, avatar?: string) => void;
  setMessages: (messages: Message[]) => void;
  setHistoryList: (
    value: HistoryInfo[] | ((prev: HistoryInfo[]) => HistoryInfo[])
  ) => void;
  setCurrentHistoryUid: (uid: string | null) => void;
  updateHistoryList: (uid: string, latestMessage: Message | null) => void;
  fullResponse: string;
  setFullResponse: (text: string) => void;
  appendResponse: (text: string) => void;
  clearResponse: () => void;
  setForceNewMessage: (value: boolean) => void;
}

/**
 * Valores iniciales por defecto
 */
const DEFAULT_HISTORY = {
  messages: [] as Message[],
  historyList: [] as HistoryInfo[],
  currentHistoryUid: null as string | null,
  fullResponse: '',
};

/**
 * Contexto para el historial del chat
 */
export const ChatHistoryContext = createContext<ChatHistoryState | null>(null);

/**
 * Proveedor del contexto de historial de chat
 */
export function ChatHistoryProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<Message[]>(DEFAULT_HISTORY.messages);
  const [historyList, setHistoryList] = useState<HistoryInfo[]>(DEFAULT_HISTORY.historyList);
  const [currentHistoryUid, setCurrentHistoryUid] = useState<string | null>(DEFAULT_HISTORY.currentHistoryUid);
  const [fullResponse, setFullResponse] = useState(DEFAULT_HISTORY.fullResponse);
  const [forceNewMessage, setForceNewMessage] = useState<boolean>(false);

  const appendHumanMessage = useCallback((content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'human',
      timestamp: new Date().toISOString(),
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
  }, []);

  const appendAIMessage = useCallback((content: string, name?: string, avatar?: string) => {
    setMessages((prevMessages) => {
      const lastMessage = prevMessages[prevMessages.length - 1];

      if (forceNewMessage || !lastMessage || lastMessage.role !== 'ai') {
        setForceNewMessage(false);
        return [...prevMessages, {
          id: Date.now().toString(),
          content,
          role: 'ai',
          timestamp: new Date().toISOString(),
          name,
          avatar,
        }];
      }

      return [
        ...prevMessages.slice(0, -1),
        {
          ...lastMessage,
          content: lastMessage.content + content,
          timestamp: new Date().toISOString(),
        },
      ];
    });
  }, [forceNewMessage, setForceNewMessage]);

  const updateHistoryList = useCallback(
    (uid: string, latestMessage: Message | null) => {
      if (!uid) {
        console.error('updateHistoryList: uid is null');
      }
      if (!currentHistoryUid) {
        console.error('updateHistoryList: currentHistoryUid is null');
      }

      setHistoryList((prevList) => prevList.map((history) => {
        if (history.uid === uid) {
          return {
            ...history,
            latest_message: latestMessage
              ? {
                content: latestMessage.content,
                role: latestMessage.role,
                timestamp: latestMessage.timestamp,
              }
              : null,
            timestamp: latestMessage?.timestamp || history.timestamp,
          };
        }
        return history;
      }));
    },
    [currentHistoryUid],
  );

  const appendResponse = useCallback((text: string) => {
    setFullResponse((prev) => prev + (text || ''));
  }, []);

  const clearResponse = useCallback(() => {
    setFullResponse(DEFAULT_HISTORY.fullResponse);
  }, []);

  const contextValue = useMemo(
    () => ({
      messages,
      historyList,
      currentHistoryUid,
      appendHumanMessage,
      appendAIMessage,
      setMessages,
      setHistoryList,
      setCurrentHistoryUid,
      updateHistoryList,
      fullResponse,
      setFullResponse,
      appendResponse,
      clearResponse,
      setForceNewMessage,
    }),
    [
      messages,
      historyList,
      currentHistoryUid,
      appendHumanMessage,
      appendAIMessage,
      updateHistoryList,
      fullResponse,
      appendResponse,
      clearResponse,
      setForceNewMessage,
    ],
  );

  return (
    <ChatHistoryContext.Provider value={contextValue}>
      {children}
    </ChatHistoryContext.Provider>
  );
}

/**
 * Hook para usar el contexto de historial de chat
 */
export function useChatHistory() {
  const context = useContext(ChatHistoryContext);

  if (!context) {
    throw new Error('useChatHistory must be used within a ChatHistoryProvider');
  }

  return context;
}
