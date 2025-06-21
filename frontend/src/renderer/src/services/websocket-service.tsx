import { Subject } from 'rxjs';
import { toaster } from '../components/ui/toaster';

export interface MessageEvent {
  type: string;
  [key: string]: any;
}

class WebSocketService {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private messageSubject = new Subject<MessageEvent>();
  private stateSubject = new Subject<'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'>();
  private currentState: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED' = 'CLOSED';

  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(url: string) {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      this.disconnect();
    }
    try {
      this.ws = new WebSocket(url);
      this.currentState = 'CONNECTING';
      this.stateSubject.next('CONNECTING');

      this.ws.onopen = () => {
        this.currentState = 'OPEN';
        this.stateSubject.next('OPEN');
        // Puedes enviar mensajes iniciales si quieres
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.messageSubject.next(message);
        } catch (error) {
          console.error('Error parsing WS message:', error);
          toaster.create({
            title: `Failed to parse WebSocket message: ${error}`,
            type: 'error',
            duration: 2000,
          });
        }
      };

      this.ws.onclose = () => {
        this.currentState = 'CLOSED';
        this.stateSubject.next('CLOSED');
      };

      this.ws.onerror = () => {
        this.currentState = 'CLOSED';
        this.stateSubject.next('CLOSED');
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.currentState = 'CLOSED';
      this.stateSubject.next('CLOSED');
    }
  }

  sendMessage(message: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not open. Unable to send message:', message);
      toaster.create({
        title: 'WebSocket is not open.',
        type: 'error',
        duration: 2000,
      });
    }
  }

  onMessage(callback: (message: MessageEvent) => void) {
    return this.messageSubject.subscribe(callback);
  }

  onStateChange(callback: (state: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED') => void) {
    return this.stateSubject.subscribe(callback);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }

  getCurrentState() {
    return this.currentState;
  }
}

export const wsService = WebSocketService.getInstance();
