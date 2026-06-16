import api from './api'

export const tradingService = {
  placeOrder: async (orderData) => {
    const { data } = await api.post('/trading/order', orderData)
    return data
  },
  buyMarket: async (symbol, quantity) =>
    tradingService.placeOrder({ symbol, quantity, order_type: 'market', side: 'buy' }),
  sellMarket: async (symbol, quantity) =>
    tradingService.placeOrder({ symbol, quantity, order_type: 'market', side: 'sell' }),
  buyLimit: async (symbol, quantity, price) =>
    tradingService.placeOrder({ symbol, quantity, order_type: 'limit', side: 'buy', price }),
  sellLimit: async (symbol, quantity, price) =>
    tradingService.placeOrder({ symbol, quantity, order_type: 'limit', side: 'sell', price }),
  buyStopLoss: async (symbol, quantity, stop_price) =>
    tradingService.placeOrder({ symbol, quantity, order_type: 'stop_loss', side: 'buy', stop_price }),
  sellStopLoss: async (symbol, quantity, stop_price) =>
    tradingService.placeOrder({ symbol, quantity, order_type: 'stop_loss', side: 'sell', stop_price }),
  cancelOrder: async (orderId) => {
    const { data } = await api.delete(`/trading/orders/${orderId}`)
    return data
  },
  getOrders: async (params = {}) => {
    const { data } = await api.get('/trading/orders', { params })
    return data
  },
  getOrder: async (orderId) => {
    const { data } = await api.get(`/trading/orders/${orderId}`)
    return data
  },
  getTrades: async (params = {}) => {
    const { data } = await api.get('/trading/trades', { params })
    return data
  },
  getOrderBook: async (symbol, depth = 10) => {
    const { data } = await api.get(`/trading/orderbook/${symbol}`, { params: { depth } })
    return data
  },
}