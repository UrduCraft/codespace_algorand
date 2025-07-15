# Silexa - Decentralized End-to-End Encrypted Messaging

Silexa is a decentralized messaging application that provides end-to-end encryption and stores messages on IPFS with metadata on the Algorand blockchain.

## Features

- 🔐 End-to-end encryption using libsodium
- 🌐 Decentralized storage via IPFS
- 💰 Algorand wallet integration (MyAlgo/Pera)
- 💬 Real-time messaging
- 📱 Modern React UI with TailwindCSS

## Project Structure

```
silexa/
├── backend/           # Python FastAPI backend
│   ├── app/          # Main application code
│   └── config/       # Configuration files
├── frontend/         # React frontend
│   └── src/
│       ├── components/  # Reusable components
│       ├── pages/      # Page components
│       ├── hooks/      # Custom hooks
│       ├── utils/      # Utility functions
│       └── types/      # TypeScript type definitions
└── docs/             # Documentation
```

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- IPFS node (or Infura IPFS)
- Algorand wallet (MyAlgo/Pera)

## Environment Variables

Create `.env` files in both backend and frontend directories with the required configuration (see `.env.example` files).