import { io, Socket } from 'socket.io-client'
import type { WSMessage, Bag, Flight } from './types'

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000'

type EventCallback<T = any> = (data: T) => void

class WebSocketClient {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(namespace: string = '/'): Socket {
    if (this.socket?.connected) {
      return this.socket
    }

    this.socket = io(`${WS_BASE_URL}${namespace}`, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      this.reconnectAttempts = attemptNumber
      console.log(`Reconnection attempt ${attemptNumber}`)
    })

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed')
    })

    return this.socket
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  onBagUpdate(callback: EventCallback<Bag>) {
    if (!this.socket) return

    this.socket.on('bag_update', callback)
  }

  onFlightUpdate(callback: EventCallback<Flight>) {
    if (!this.socket) return

    this.socket.on('flight_update', callback)
  }

  onAlert(callback: EventCallback<WSMessage>) {
    if (!this.socket) return

    this.socket.on('alert', callback)
  }

  subscribeToBag(bagId: string) {
    if (!this.socket) return

    this.socket.emit('subscribe_bag', { bag_id: bagId })
  }

  unsubscribeFromBag(bagId: string) {
    if (!this.socket) return

    this.socket.emit('unsubscribe_bag', { bag_id: bagId })
  }

  subscribeToFlight(flightId: string) {
    if (!this.socket) return

    this.socket.emit('subscribe_flight', { flight_id: flightId })
  }

  unsubscribeFromFlight(flightId: string) {
    if (!this.socket) return

    this.socket.emit('unsubscribe_flight', { flight_id: flightId })
  }

  subscribeToAirport(airportCode: string) {
    if (!this.socket) return

    this.socket.emit('subscribe_airport', { airport_code: airportCode })
  }

  off(event: string, callback?: EventCallback) {
    if (!this.socket) return

    this.socket.off(event, callback)
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }
}

export const wsClient = new WebSocketClient()
export default wsClient
