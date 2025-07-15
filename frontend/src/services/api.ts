/**
 * Silexa API Service
 * Handles HTTP requests to the backend API
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ApiError } from '../types';
import config from '../utils/config';

class ApiService {
  private instance: AxiosInstance;

  constructor() {
    this.instance = axios.create({
      baseURL: config.API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        if (config.DEBUG) {
          console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
        }
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        if (config.DEBUG) {
          console.log('API Response:', response.status, response.data);
        }
        return response;
      },
      (error) => {
        console.error('API Response Error:', error);
        
        if (error.response?.data) {
          return Promise.reject(error.response.data as ApiError);
        }
        
        return Promise.reject({
          success: false,
          error: error.message || 'Network error',
          detail: error.code,
        } as ApiError);
      }
    );
  }

  async get<T>(endpoint: string, params?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.get<ApiResponse<T>>(endpoint, { params });
    return response.data;
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.post<ApiResponse<T>>(endpoint, data);
    return response.data;
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.put<ApiResponse<T>>(endpoint, data);
    return response.data;
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    const response = await this.instance.delete<ApiResponse<T>>(endpoint);
    return response.data;
  }

  // ============= Authentication API =============
  
  async connectWallet(walletRequest: any) {
    return this.post('/api/auth/connect-wallet', walletRequest);
  }

  async registerUser(userData: any) {
    return this.post('/api/auth/register', userData);
  }

  async getUserProfile(address: string) {
    return this.get(`/api/auth/profile/${address}`);
  }

  async verifyUserSession(address: string) {
    return this.get(`/api/auth/verify/${address}`);
  }

  async logoutUser(address: string) {
    return this.post(`/api/auth/logout/${address}`);
  }

  // ============= Users API =============

  async searchUsers(query: string, limit: number = 10) {
    return this.get('/api/users/search', { query, limit });
  }

  async getUserProfileDetailed(address: string) {
    return this.get(`/api/users/profile/${address}`);
  }

  async updateUserProfile(address: string, userData: any) {
    return this.put(`/api/users/profile/${address}`, userData);
  }

  async getOnlineUsers() {
    return this.get('/api/users/online');
  }

  async getUserStatus(address: string) {
    return this.get(`/api/users/status/${address}`);
  }

  async listAllUsers(limit: number = 50, offset: number = 0) {
    return this.get('/api/users/list', { limit, offset });
  }

  // ============= Messages API =============

  async sendMessage(messageData: any, senderAddress: string, senderPrivateKey: string) {
    return this.post('/api/messages/send', {
      ...messageData,
      sender_address: senderAddress,
      sender_private_key: senderPrivateKey,
    });
  }

  async receiveMessage(messageId: string, recipientAddress: string, recipientPrivateKey: string) {
    return this.get(`/api/messages/receive/${messageId}`, {
      recipient_address: recipientAddress,
      recipient_private_key: recipientPrivateKey,
    });
  }

  async listUserMessages(
    userAddress: string,
    limit: number = 50,
    offset: number = 0,
    messageType?: string,
    status?: string
  ) {
    return this.get(`/api/messages/list/${userAddress}`, {
      limit,
      offset,
      message_type: messageType,
      status,
    });
  }

  async getMessageInfo(messageId: string) {
    return this.get(`/api/messages/info/${messageId}`);
  }

  async encryptMessageContent(content: string, senderPrivateKey: string, recipientPublicKey: string) {
    return this.post('/api/messages/encrypt', {
      content,
      sender_private_key: senderPrivateKey,
      recipient_public_key: recipientPublicKey,
    });
  }

  async decryptMessageContent(
    encryptedContent: string,
    nonce: string,
    recipientPrivateKey: string,
    senderPublicKey: string
  ) {
    return this.post('/api/messages/decrypt', {
      encrypted_content: encryptedContent,
      nonce,
      recipient_private_key: recipientPrivateKey,
      sender_public_key: senderPublicKey,
    });
  }

  // ============= Chat API =============

  async getUserChatRooms(userAddress: string) {
    return this.get(`/api/chat/rooms/${userAddress}`);
  }

  async getChatHistory(
    userAddress: string,
    otherAddress: string,
    limit: number = 50,
    offset: number = 0
  ) {
    return this.get(`/api/chat/history/${userAddress}/${otherAddress}`, {
      limit,
      offset,
    });
  }

  async sendTypingIndicator(typingData: any) {
    return this.post('/api/chat/typing', typingData);
  }

  async getChatRoomInfo(chatRoomId: string) {
    return this.get(`/api/chat/room/${chatRoomId}`);
  }

  async getChatStats(userAddress: string) {
    return this.get(`/api/chat/stats/${userAddress}`);
  }

  // ============= System API =============

  async getServiceStatus() {
    return this.get('/api/status/services');
  }

  async healthCheck() {
    return this.get('/health');
  }
}

export const apiService = new ApiService();
export default apiService;