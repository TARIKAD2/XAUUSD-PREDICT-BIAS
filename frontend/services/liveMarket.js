// Live market WebSocket client for the dashboard.
// Connects strictly to the FastAPI backend (/ws/market), NEVER to Twelve Data directly.
// Never exposes or handles external API keys.
// Reconnect backoff: 1 → 2 → 4 → 8 → 16 → 30 seconds.

class LiveMarketClient {
  constructor() {
    this.ws = null;
    this.backoffSteps = [1000, 2000, 4000, 8000, 16000, 30000];
    this.currentBackoff = 0;
    this.subscribers = new Set();
    this.status = 'DISCONNECTED';
    this.lastTick = null;
    this.reconnectTimer = null;

    if (typeof window !== 'undefined') {
      const baseUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}`.replace(/\/$/, '');
      this.url = baseUrl.replace(/^http/, 'ws') + '/ws/market';
      this.connect();
    }
  }

  notifyStatus(status) {
    this.status = status;
    this.subscribers.forEach((cb) => {
      try {
        cb(null, status);
      } catch (e) {
        console.error('LiveMarket: subscriber error on status', e);
      }
    });
  }

  connect() {
    if (typeof window === 'undefined') return;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.notifyStatus('CONNECTING');

    try {
      this.ws = new WebSocket(this.url);
    } catch (e) {
      console.warn('LiveMarket: WebSocket instantiation error', e);
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      console.info('LiveMarket: WebSocket connected to', this.url);
      this.currentBackoff = 0;
      this.notifyStatus('CONNECTED');
    };

    this.ws.onmessage = (event) => {
      try {
        const rawData = JSON.parse(event.data);
        const browserNow = Date.now();

        // Calculate fine-grained latency metrics
        const tick = {
          ...rawData,
          browser_received_at: new Date(browserNow).toISOString(),
        };

        if (rawData.received_at) {
          const backendTime = new Date(rawData.received_at).getTime();
          if (!isNaN(backendTime)) {
            tick.browser_latency_ms = Math.max(0, browserNow - backendTime);
          }
        }

        if (rawData.provider_timestamp) {
          const provTime =
            typeof rawData.provider_timestamp === 'number'
              ? rawData.provider_timestamp > 1e11
                ? rawData.provider_timestamp
                : rawData.provider_timestamp * 1000
              : new Date(rawData.provider_timestamp).getTime();

          if (!isNaN(provTime)) {
            tick.total_latency_ms = Math.max(0, browserNow - provTime);
          }
        }

        this.lastTick = tick;

        // Broadcast to all local subscribers immediately without throttle/debounce
        this.subscribers.forEach((cb) => {
          try {
            cb(tick, this.status);
          } catch (e) {
            console.error('LiveMarket: subscriber error on tick', e);
          }
        });
      } catch (e) {
        console.warn('LiveMarket: received non-JSON message', event.data);
      }
    };

    this.ws.onclose = (event) => {
      console.warn('LiveMarket: WebSocket closed', event?.reason || '');
      this.notifyStatus('DISCONNECTED');
      this.scheduleReconnect();
    };

    this.ws.onerror = (event) => {
      console.error('LiveMarket: WebSocket error', event);
      if (this.ws) {
        try {
          this.ws.close();
        } catch (_) {}
      }
    };
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;
    const delay = this.backoffSteps[this.currentBackoff] || this.backoffSteps[this.backoffSteps.length - 1];
    this.notifyStatus('RECONNECTING');
    console.info(`LiveMarket: reconnecting in ${delay / 1000}s`);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.currentBackoff = Math.min(this.currentBackoff + 1, this.backoffSteps.length - 1);
      this.connect();
    }, delay);
  }

  // Subscribe to live ticks and connection status changes
  subscribe(callback) {
    if (typeof callback !== 'function') return () => {};
    this.subscribers.add(callback);

    // Provide initial state if already connected or cached
    if (this.lastTick || this.status) {
      try {
        callback(this.lastTick, this.status);
      } catch (_) {}
    }

    // Ensure connection is active if in browser
    if (typeof window !== 'undefined' && (!this.ws || this.ws.readyState === WebSocket.CLOSED)) {
      this.connect();
    }

    return () => {
      this.subscribers.delete(callback);
    };
  }
}

export const liveMarket = new LiveMarketClient();
