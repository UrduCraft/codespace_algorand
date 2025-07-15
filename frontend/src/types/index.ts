/**
 * Silexa Frontend Type Definitions
 * Contains all TypeScript interfaces and types used in the frontend
 */

// ============= User Types =============
export interface User {
  id: string;
  username: string;
  algorand_address: string;
  public_key: string;
  created_at: string;
  last_seen?: string;
  is_online: boolean;
}

export interface UserCreate {
  username: string;
  public_key: string;
  algorand_address: string;
}

// ============= Message Types =============
export enum MessageType {
  TEXT = "text",
  FILE = "file",
  IMAGE = "image"
}

export enum MessageStatus {
  SENT = "sent",
  DELIVERED = "delivered",
  READ = "read",
  FAILED = "failed"
}

export interface Message {
  id: string;
  sender_address: string;
  recipient_address: string;
  message_type: MessageType;
  status: MessageStatus;
  created_at: string;
  delivered_at?: string;
  read_at?: string;
  ipfs_hash?: string;
  algorand_txn_id?: string;
  is_sent?: boolean; // Helper field for UI
}

export interface MessageCreate {
  recipient_address: string;
  content: string;
  message_type: MessageType;
  nonce: string;
  metadata?: Record<string, any>;
}

export interface DecryptedMessage extends Message {
  decrypted_content: string;
}

// ============= Chat Types =============
export interface ChatRoom {
  id: string;
  participants: string[];
  created_at: string;
  last_message_at?: string;
  last_message?: Message;
  other_user?: {
    address: string;
    username: string;
    is_online: boolean;
  };
}

export interface ChatHistory {
  chat_room_id: string;
  messages: Message[];
  total_count: number;
  has_more: boolean;
  other_user: {
    address: string;
    username: string;
    is_online: boolean;
  };
}

// ============= Wallet Types =============
export interface WalletInfo {
  address: string;
  publicKey: string;
  name: string;
  connected: boolean;
}

export interface WalletConnectRequest {
  address: string;
  public_key: string;
  signed_message: string;
  original_message: string;
}

// ============= API Types =============
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface ApiError {
  success: false;
  error: string;
  detail?: string;
  status_code?: number;
}

// ============= WebSocket Types =============
export interface WebSocketMessage {
  type: string;
  data: Record<string, any>;
  sender?: string;
  timestamp: string;
}

export interface TypingIndicator {
  user_address: string;
  chat_room_id: string;
  is_typing: boolean;
}

// ============= Encryption Types =============
export interface EncryptionKeys {
  privateKey: string;
  publicKey: string;
}

export interface EncryptedContent {
  encrypted_content: string;
  nonce: string;
}

// ============= App State Types =============
export interface AppState {
  user: User | null;
  wallet: WalletInfo | null;
  encryptionKeys: EncryptionKeys | null;
  isConnecting: boolean;
  error: string | null;
}

export interface ChatState {
  chatRooms: ChatRoom[];
  activeChat: ChatRoom | null;
  messages: Record<string, DecryptedMessage[]>; // chatRoomId -> messages
  typingUsers: Record<string, boolean>; // userAddress -> isTyping
  onlineUsers: Set<string>;
  loading: boolean;
  error: string | null;
}

// ============= Component Props Types =============
export interface ChatMessageProps {
  message: DecryptedMessage;
  isOwn: boolean;
  showAvatar?: boolean;
}

export interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export interface UserListProps {
  users: User[];
  onSelectUser: (user: User) => void;
  selectedUser?: User;
}

export interface WalletConnectProps {
  onConnect: (wallet: WalletInfo) => void;
  isConnecting: boolean;
}

// ============= Service Types =============
export interface EncryptionService {
  generateKeyPair(): Promise<EncryptionKeys>;
  encryptMessage(content: string, recipientPublicKey: string, senderPrivateKey: string): Promise<EncryptedContent>;
  decryptMessage(encryptedContent: string, nonce: string, senderPublicKey: string, recipientPrivateKey: string): Promise<string>;
}

export interface WalletService {
  connectMyAlgo(): Promise<WalletInfo>;
  connectPera(): Promise<WalletInfo>;
  disconnect(): Promise<void>;
  signMessage(message: string): Promise<string>;
}

export interface ApiService {
  post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>>;
  get<T>(endpoint: string, params?: any): Promise<ApiResponse<T>>;
  put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>>;
  delete<T>(endpoint: string): Promise<ApiResponse<T>>;
}

// ============= Hook Types =============
export interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (message: WebSocketMessage) => void;
  lastMessage: WebSocketMessage | null;
  error: string | null;
}

export interface UseEncryptionReturn {
  encryptMessage: (content: string, recipientAddress: string) => Promise<EncryptedContent>;
  decryptMessage: (encryptedContent: string, nonce: string, senderAddress: string) => Promise<string>;
  generateKeys: () => Promise<EncryptionKeys>;
  isReady: boolean;
}

export interface UseChatReturn extends ChatState {
  sendMessage: (recipientAddress: string, content: string) => Promise<void>;
  loadChatHistory: (otherUserAddress: string) => Promise<void>;
  markMessageAsRead: (messageId: string) => Promise<void>;
  startTyping: (chatRoomId: string) => void;
  stopTyping: (chatRoomId: string) => void;
}