import { useEffect } from 'react';
import { useWebSocketStore } from '../store/websocketStore';

export const useWebSocket = (investigationId: string) => {
  const { connect, disconnect } = useWebSocketStore();

  useEffect(() => {
    if (investigationId && investigationId.trim() !== '') {
      connect(investigationId);
    }

    return () => {
      disconnect();
    };
  }, [investigationId, connect, disconnect]);
};