/**
 * Silexa Encryption Utilities
 * Provides end-to-end encryption using libsodium (tweetnacl)
 */

import * as nacl from 'tweetnacl';
import * as naclUtil from 'tweetnacl-util';
import { EncryptionKeys, EncryptedContent } from '../types';

export class EncryptionService {
  /**
   * Generate a new encryption key pair
   */
  static generateKeyPair(): EncryptionKeys {
    const keyPair = nacl.box.keyPair();
    
    return {
      privateKey: naclUtil.encodeBase64(keyPair.secretKey),
      publicKey: naclUtil.encodeBase64(keyPair.publicKey),
    };
  }

  /**
   * Encrypt a message for a recipient
   */
  static encryptMessage(
    content: string,
    recipientPublicKey: string,
    senderPrivateKey: string
  ): EncryptedContent {
    try {
      const recipientPublicKeyBytes = naclUtil.decodeBase64(recipientPublicKey);
      const senderPrivateKeyBytes = naclUtil.decodeBase64(senderPrivateKey);
      const messageBytes = naclUtil.decodeUTF8(content);
      
      const encrypted = nacl.box(
        messageBytes,
        nacl.randomBytes(24), // nonce
        recipientPublicKeyBytes,
        senderPrivateKeyBytes
      );
      
      const nonce = encrypted.slice(0, 24);
      const ciphertext = encrypted.slice(24);
      
      return {
        encrypted_content: naclUtil.encodeBase64(ciphertext),
        nonce: naclUtil.encodeBase64(nonce),
      };
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Failed to encrypt message');
    }
  }

  /**
   * Decrypt a message from a sender
   */
  static decryptMessage(
    encryptedContent: string,
    nonce: string,
    senderPublicKey: string,
    recipientPrivateKey: string
  ): string {
    try {
      const encryptedBytes = naclUtil.decodeBase64(encryptedContent);
      const nonceBytes = naclUtil.decodeBase64(nonce);
      const senderPublicKeyBytes = naclUtil.decodeBase64(senderPublicKey);
      const recipientPrivateKeyBytes = naclUtil.decodeBase64(recipientPrivateKey);
      
      const decrypted = nacl.box.open(
        encryptedBytes,
        nonceBytes,
        senderPublicKeyBytes,
        recipientPrivateKeyBytes
      );
      
      if (!decrypted) {
        throw new Error('Failed to decrypt message - invalid keys or corrupted data');
      }
      
      return naclUtil.encodeUTF8(decrypted);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt message');
    }
  }

  /**
   * Verify if a public key is valid
   */
  static verifyPublicKey(publicKey: string): boolean {
    try {
      const keyBytes = naclUtil.decodeBase64(publicKey);
      return keyBytes.length === 32; // X25519 public key should be 32 bytes
    } catch {
      return false;
    }
  }

  /**
   * Generate a random nonce for encryption
   */
  static generateNonce(): string {
    return naclUtil.encodeBase64(nacl.randomBytes(24));
  }

  /**
   * Hash a message for signing (utility function)
   */
  static hashMessage(message: string): string {
    const messageBytes = naclUtil.decodeUTF8(message);
    const hash = nacl.hash(messageBytes);
    return naclUtil.encodeBase64(hash);
  }
}

export default EncryptionService;