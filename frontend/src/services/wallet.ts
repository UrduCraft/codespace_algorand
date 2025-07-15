/**
 * Silexa Wallet Service
 * Handles Algorand wallet connections (MyAlgo and Pera)
 */

import { PeraWalletConnect } from '@perawallet/connect';
import MyAlgoConnect from '@myalgo/connect';
import algosdk from 'algosdk';
import { WalletInfo } from '../types';
import config from '../utils/config';
import { EncryptionService } from '../utils/encryption';

class WalletService {
  private peraWallet: PeraWalletConnect;
  private myAlgoWallet: MyAlgoConnect;
  private currentWallet: WalletInfo | null = null;

  constructor() {
    this.peraWallet = new PeraWalletConnect({
      deepLink: {
        deeplinkURL: 'pera-wallet://',
      },
      shouldShowSignTxnToast: true,
    });

    this.myAlgoWallet = new MyAlgoConnect();

    // Load saved wallet info
    this.loadSavedWallet();
  }

  /**
   * Connect to Pera Wallet
   */
  async connectPera(): Promise<WalletInfo> {
    try {
      const accounts = await this.peraWallet.connect();
      
      if (accounts.length === 0) {
        throw new Error('No accounts found in Pera Wallet');
      }

      const address = accounts[0];
      
      // Generate a message to sign for authentication
      const message = `Silexa Login: ${Date.now()}`;
      const messageBytes = new TextEncoder().encode(message);
      
      // Sign the message
      const signedMessage = await this.peraWallet.signData([
        {
          data: messageBytes,
          message: 'Please sign this message to authenticate with Silexa',
        },
      ], address);

      const walletInfo: WalletInfo = {
        address,
        publicKey: '', // Pera doesn't expose public key directly
        name: 'Pera Wallet',
        connected: true,
      };

      this.currentWallet = walletInfo;
      this.saveWallet(walletInfo);
      
      return walletInfo;
    } catch (error) {
      console.error('Pera Wallet connection failed:', error);
      throw new Error('Failed to connect to Pera Wallet');
    }
  }

  /**
   * Connect to MyAlgo Wallet
   */
  async connectMyAlgo(): Promise<WalletInfo> {
    try {
      const accounts = await this.myAlgoWallet.connect({
        shouldSelectOneAccount: true,
        openManager: false,
      });

      if (accounts.length === 0) {
        throw new Error('No accounts found in MyAlgo Wallet');
      }

      const account = accounts[0];
      
      const walletInfo: WalletInfo = {
        address: account.address,
        publicKey: '', // We'll get this from account info
        name: 'MyAlgo Wallet',
        connected: true,
      };

      this.currentWallet = walletInfo;
      this.saveWallet(walletInfo);
      
      return walletInfo;
    } catch (error) {
      console.error('MyAlgo Wallet connection failed:', error);
      throw new Error('Failed to connect to MyAlgo Wallet');
    }
  }

  /**
   * Sign a message with the connected wallet
   */
  async signMessage(message: string): Promise<string> {
    if (!this.currentWallet) {
      throw new Error('No wallet connected');
    }

    try {
      const messageBytes = new TextEncoder().encode(message);

      if (this.currentWallet.name === 'Pera Wallet') {
        const signedData = await this.peraWallet.signData([
          {
            data: messageBytes,
            message: 'Sign message for Silexa authentication',
          },
        ], this.currentWallet.address);

        return Buffer.from(signedData[0]).toString('base64');
      } else if (this.currentWallet.name === 'MyAlgo Wallet') {
        const signedData = await this.myAlgoWallet.signBytes(
          messageBytes,
          this.currentWallet.address
        );

        return Buffer.from(signedData.blob).toString('base64');
      }

      throw new Error('Unsupported wallet for message signing');
    } catch (error) {
      console.error('Message signing failed:', error);
      throw new Error('Failed to sign message');
    }
  }

  /**
   * Sign a transaction with the connected wallet
   */
  async signTransaction(txn: algosdk.Transaction): Promise<Uint8Array> {
    if (!this.currentWallet) {
      throw new Error('No wallet connected');
    }

    try {
      if (this.currentWallet.name === 'Pera Wallet') {
        const signedTxn = await this.peraWallet.signTransaction([
          { txn: algosdk.encodeUnsignedTransaction(txn) },
        ]);
        return signedTxn[0];
      } else if (this.currentWallet.name === 'MyAlgo Wallet') {
        const signedTxn = await this.myAlgoWallet.signTransaction(txn.toByte());
        return signedTxn.blob;
      }

      throw new Error('Unsupported wallet for transaction signing');
    } catch (error) {
      console.error('Transaction signing failed:', error);
      throw new Error('Failed to sign transaction');
    }
  }

  /**
   * Get account information from Algorand
   */
  async getAccountInfo(address: string): Promise<any> {
    try {
      const algodClient = new algosdk.Algodv2('', config.ALGOD_SERVER, config.ALGOD_PORT);
      const accountInfo = await algodClient.accountInformation(address).do();
      return accountInfo;
    } catch (error) {
      console.error('Failed to get account info:', error);
      throw new Error('Failed to get account information');
    }
  }

  /**
   * Disconnect the current wallet
   */
  async disconnect(): Promise<void> {
    try {
      if (this.currentWallet?.name === 'Pera Wallet') {
        await this.peraWallet.disconnect();
      }
      // MyAlgo doesn't have a disconnect method

      this.currentWallet = null;
      this.clearSavedWallet();
    } catch (error) {
      console.error('Wallet disconnection failed:', error);
      throw new Error('Failed to disconnect wallet');
    }
  }

  /**
   * Get the currently connected wallet
   */
  getCurrentWallet(): WalletInfo | null {
    return this.currentWallet;
  }

  /**
   * Check if a wallet is connected
   */
  isConnected(): boolean {
    return this.currentWallet !== null && this.currentWallet.connected;
  }

  /**
   * Generate encryption keys for the user
   */
  generateEncryptionKeys() {
    return EncryptionService.generateKeyPair();
  }

  /**
   * Save wallet info to localStorage
   */
  private saveWallet(walletInfo: WalletInfo): void {
    try {
      localStorage.setItem(config.STORAGE_KEYS.WALLET_INFO, JSON.stringify(walletInfo));
    } catch (error) {
      console.error('Failed to save wallet info:', error);
    }
  }

  /**
   * Load wallet info from localStorage
   */
  private loadSavedWallet(): void {
    try {
      const saved = localStorage.getItem(config.STORAGE_KEYS.WALLET_INFO);
      if (saved) {
        this.currentWallet = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load saved wallet:', error);
      this.clearSavedWallet();
    }
  }

  /**
   * Clear saved wallet info
   */
  private clearSavedWallet(): void {
    try {
      localStorage.removeItem(config.STORAGE_KEYS.WALLET_INFO);
    } catch (error) {
      console.error('Failed to clear saved wallet:', error);
    }
  }

  /**
   * Reconnect to the previously connected wallet
   */
  async reconnect(): Promise<WalletInfo | null> {
    if (!this.currentWallet) {
      return null;
    }

    try {
      if (this.currentWallet.name === 'Pera Wallet') {
        // Check if Pera is still connected
        const accounts = await this.peraWallet.reconnectSession();
        if (accounts.length > 0 && accounts.includes(this.currentWallet.address)) {
          return this.currentWallet;
        }
      } else if (this.currentWallet.name === 'MyAlgo Wallet') {
        // MyAlgo doesn't have a reconnect method, so we assume it's still connected
        // In a real app, you might want to verify the connection
        return this.currentWallet;
      }

      // If reconnection failed, clear the saved wallet
      this.currentWallet = null;
      this.clearSavedWallet();
      return null;
    } catch (error) {
      console.error('Wallet reconnection failed:', error);
      this.currentWallet = null;
      this.clearSavedWallet();
      return null;
    }
  }
}

export const walletService = new WalletService();
export default walletService;