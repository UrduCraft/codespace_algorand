/**
 * Silexa Frontend Configuration
 * Environment variables and app configuration
 */

export const config = {
  // API Configuration
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000',
  
  // Algorand Configuration
  ALGOD_SERVER: process.env.REACT_APP_ALGOD_SERVER || 'https://testnet-api.algonode.cloud',
  ALGOD_PORT: parseInt(process.env.REACT_APP_ALGOD_PORT || '443'),
  INDEXER_SERVER: process.env.REACT_APP_INDEXER_SERVER || 'https://testnet-idx.algonode.cloud',
  INDEXER_PORT: parseInt(process.env.REACT_APP_INDEXER_PORT || '443'),
  
  // App Configuration
  APP_NAME: process.env.REACT_APP_APP_NAME || 'Silexa',
  VERSION: process.env.REACT_APP_VERSION || '1.0.0',
  
  // Feature Flags
  ENABLE_NOTIFICATIONS: process.env.REACT_APP_ENABLE_NOTIFICATIONS === 'true',
  ENABLE_FILE_SHARING: process.env.REACT_APP_ENABLE_FILE_SHARING === 'true',
  
  // Development
  DEBUG: process.env.REACT_APP_DEBUG === 'true' || process.env.NODE_ENV === 'development',
  
  // UI Configuration
  MAX_MESSAGE_LENGTH: 1000,
  MESSAGES_PER_PAGE: 50,
  TYPING_TIMEOUT: 3000, // 3 seconds
  RECONNECT_INTERVAL: 5000, // 5 seconds
  
  // Storage Keys
  STORAGE_KEYS: {
    WALLET_INFO: 'silexa_wallet_info',
    USER_PROFILE: 'silexa_user_profile',
    ENCRYPTION_KEYS: 'silexa_encryption_keys',
    THEME: 'silexa_theme',
  },
  
  // Algorand Network
  NETWORK: 'testnet',
  
  // WebSocket Events
  WS_EVENTS: {
    NEW_MESSAGE: 'new_message',
    MESSAGE_READ: 'message_read',
    TYPING: 'typing',
    USER_STATUS: 'user_status',
    PING: 'ping',
    PONG: 'pong',
  },
};

export default config;