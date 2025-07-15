# Silexa - Decentralized Messaging App MVP

## Project Overview

Silexa is a decentralized, end-to-end encrypted messaging application built with React (frontend) and FastAPI (backend). It leverages Algorand blockchain for wallet authentication and metadata storage, IPFS for decentralized file storage, and libsodium for encryption.

## 🚀 Key Features

- **🔐 End-to-End Encryption**: Messages encrypted using libsodium (X25519 + XSalsa20Poly1305)
- **🌐 Decentralized Storage**: IPFS for message and file storage
- **💰 Blockchain Integration**: Algorand for wallet auth and metadata transactions
- **💬 Real-time Messaging**: WebSocket-based real-time communication
- **📱 Modern UI**: React with TailwindCSS and responsive design
- **🔑 Wallet Support**: MyAlgo and Pera wallet integration

## 📁 Project Structure

```
silexa/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── api/               # API route modules
│   │   │   ├── auth.py        # Authentication routes
│   │   │   ├── users.py       # User management routes
│   │   │   ├── messages.py    # Message handling routes
│   │   │   └── chat.py        # Chat room routes
│   │   ├── services/          # Core business logic
│   │   │   ├── encryption.py  # E2E encryption service
│   │   │   ├── ipfs_service.py # IPFS integration
│   │   │   ├── algorand_service.py # Blockchain operations
│   │   │   └── messaging_service.py # Message orchestration
│   │   ├── models.py          # Pydantic data models
│   │   ├── main.py            # FastAPI application
│   │   └── websocket_manager.py # Real-time messaging
│   └── config/
│       └── settings.py        # Environment configuration
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API and wallet services
│   │   ├── utils/            # Utility functions
│   │   └── types/            # TypeScript definitions
│   ├── package.json          # Node.js dependencies
│   └── tailwind.config.js    # TailwindCSS configuration
├── requirements.txt          # Python dependencies
├── main.py                   # Application entry point
└── README.md                 # Project documentation
```

## 🔧 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PyNaCl**: Libsodium encryption library
- **IPFS HTTP Client**: Decentralized storage
- **Algorand SDK**: Blockchain integration
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **Algorand Wallets**: MyAlgo and Pera integration
- **TweetNaCl**: Client-side encryption
- **Axios**: HTTP client for API communication

## 🛠 Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- IPFS node (optional, uses Infura by default)

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration

# Run the backend server
python main.py
# or
cd backend && uvicorn app.main:app --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Start the development server
npm start
```

## 🔐 Security Architecture

### End-to-End Encryption Flow
1. **Key Generation**: Each user generates X25519 key pairs
2. **Message Encryption**: Messages encrypted using sender's private key + recipient's public key
3. **Decentralized Storage**: Encrypted messages stored on IPFS
4. **Blockchain Metadata**: Message metadata recorded on Algorand
5. **Key Exchange**: Public keys shared during user registration

### Authentication Flow
1. **Wallet Connection**: User connects MyAlgo or Pera wallet
2. **Message Signing**: Wallet signs authentication message
3. **Backend Verification**: Server verifies signature against public key
4. **Session Management**: Secure session established

## 📡 API Endpoints

### Authentication
- `POST /api/auth/connect-wallet` - Connect wallet
- `POST /api/auth/register` - Register new user
- `GET /api/auth/profile/{address}` - Get user profile
- `POST /api/auth/logout/{address}` - Logout user

### Users
- `GET /api/users/search` - Search users
- `GET /api/users/online` - Get online users
- `PUT /api/users/profile/{address}` - Update profile

### Messages
- `POST /api/messages/send` - Send message
- `GET /api/messages/receive/{id}` - Receive/decrypt message
- `GET /api/messages/list/{address}` - List user messages
- `POST /api/messages/encrypt` - Encrypt content
- `POST /api/messages/decrypt` - Decrypt content

### Chat
- `GET /api/chat/rooms/{address}` - Get chat rooms
- `GET /api/chat/history/{user}/{other}` - Get chat history
- `POST /api/chat/typing` - Send typing indicator

### WebSocket Events
- `new_message` - New message notification
- `message_read` - Message read receipt
- `typing` - Typing indicators
- `user_status` - Online/offline status

## 🌐 Deployment Architecture

### Production Considerations
1. **IPFS**: Use dedicated IPFS node or Infura/Pinata
2. **Database**: Replace in-memory storage with PostgreSQL/MongoDB
3. **Caching**: Add Redis for session management
4. **Security**: Implement rate limiting and input validation
5. **Monitoring**: Add logging and error tracking
6. **Scaling**: Use load balancers and container orchestration

### Environment Configuration
- **Development**: Local IPFS + Algorand TestNet
- **Staging**: Infura IPFS + Algorand TestNet
- **Production**: Dedicated IPFS + Algorand MainNet

## 🔮 Future Enhancements

### Planned Features
- **File Sharing**: Encrypted file attachments
- **Group Chats**: Multi-participant encrypted conversations
- **Voice Messages**: Audio message support
- **Message History**: Blockchain-based message recovery
- **Mobile Apps**: React Native implementation
- **Push Notifications**: Real-time mobile notifications

### Technical Improvements
- **Database Persistence**: Full message history storage
- **Offline Support**: PWA with offline message queue
- **Advanced Encryption**: Support for multiple encryption algorithms
- **Federation**: Multi-server deployment support
- **Backup/Recovery**: Encrypted backup solutions

## 🐛 Known Limitations

1. **In-Memory Storage**: Messages not persisted between restarts
2. **Key Management**: Basic key storage (not hardware wallet integration)
3. **File Size Limits**: No chunking for large files
4. **Error Handling**: Basic error recovery mechanisms
5. **Performance**: Not optimized for high-throughput scenarios

## 🧪 Testing

### Backend Testing
```bash
# Run API tests
cd backend
python -m pytest tests/

# Test individual components
python -m pytest tests/test_encryption.py
```

### Frontend Testing
```bash
# Run React tests
cd frontend
npm test

# Run E2E tests
npm run test:e2e
```

## 📚 Documentation

- **API Documentation**: Available at `http://localhost:8000/docs` (Swagger)
- **Architecture Diagrams**: See `/docs/architecture/`
- **Security Analysis**: See `/docs/security/`
- **Deployment Guide**: See `/docs/deployment/`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `/docs/`
- Review the API documentation at `/docs` endpoint

---

**Silexa MVP** - Secure, Decentralized, Private Messaging 🔐