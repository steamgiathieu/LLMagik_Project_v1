# Frontend Setup & Development Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start dev server
npm run dev
```

Dev server akan chạy tại **http://localhost:5173**

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # API client (axios-like fetch wrapper)
│   ├── components/
│   │   ├── UploadModal.tsx      # Upload text/URL/file modal
│   │   ├── AnalysisPanel.tsx    # Display analysis results
│   │   ├── ChatBox.tsx          # Chat interface with AI
│   │   ├── RewritePanel.tsx     # Text rewriting interface
│   │   ├── Navbar.tsx           # Navigation bar
│   │   └── Reader/              # Text reader component
│   ├── hooks/
│   │   ├── useApi.ts            # API call hook
│   │   ├── usePagination.ts     # Pagination hook
│   │   └── index.ts
│   ├── pages/
│   │   ├── Login.tsx            # Login/Register page
│   │   ├── Home.tsx             # Documents list
│   │   ├── Reader.tsx           # Main reader interface
│   │   ├── Profile.tsx          # User profile
│   │   └── History.tsx          # Activity history
│   ├── store/
│   │   ├── authStore.ts         # Authentication state (Zustand)
│   │   ├── documentStore.ts     # Documents management
│   │   ├── analysisStore.ts     # Analysis results
│   │   ├── chatStore.ts         # Chat state
│   │   └── historyStore.ts      # History state
│   ├── styles/
│   │   └── global.css           # Global styles
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # Entry point
│   └── index.tsx                # ReactDOM mount
├── .env.example
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 🔧 Environment Variables

Create `.env` file:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000

# App Configuration
VITE_APP_NAME=TextAnalyzer
VITE_APP_VERSION=1.0.0
VITE_DEBUG=false
```

---

## 📦 Available Scripts

```bash
# Development mode with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🎯 Key Features Implemented

### Stores (State Management with Zustand)
- ✅ **authStore** - User authentication, login, register, profile
- ✅ **documentStore** - Document list, upload, delete
- ✅ **analysisStore** - Text analysis (reader/writer modes)
- ✅ **chatStore** - Chat sessions and messages
- ✅ **historyStore** - Activity history

### Components
- ✅ **UploadModal** - Upload text, URL, or file (PDF/DOCX)
- ✅ **AnalysisPanel** - Display analysis results with formatting
- ✅ **ChatBox** - Chat interface with real-time messages
- ✅ **RewritePanel** - Text rewriting with goals
- ✅ **Navbar** - Navigation and user menu
- ✅ **ReaderView** - Text display with paragraph selection

### Pages
- ✅ **Login** - User authentication
- ✅ **Home** - Document list and management
- ✅ **Reader** - Main analysis interface with sidebar controls
- ✅ **Profile** - User settings
- ✅ **History** - Activity history with filters

### Hooks & Utils
- ✅ **useApi** - Simplified API call wrapper
- ✅ **usePagination** - Pagination logic
- ✅ **Global CSS** - Base styles, utilities, animations

---

## 🔗 API Integration

API client is centralized in `src/api/client.ts`:

```typescript
// Authentication
authApi.login(username, password)
authApi.register(userData)
authApi.me()
authApi.updateProfile(data)

// Documents
textsApi.uploadText({ text })
textsApi.uploadUrl({ url })
textsApi.uploadFile(file)
textsApi.list()
textsApi.get(docId)
textsApi.delete(docId)

// Analysis
analysisApi.analyze({ document_id, mode, paragraphs })
analysisApi.history()

// Chat
chatApi.chat({ document_id, user_question, session_id })

// Rewrite
rewriteApi.rewrite({ paragraph_id, original_text, goal, document_id })

// History
historyApi.all()
historyApi.analyses()
historyApi.stats()
```

### Error Handling
- API errors automatically logged out expired sessions
- All errors caught and displayed to user
- HTTP status codes handled appropriately

---

## 🎨 Styling

- **CSS Files**: One CSS file per component + global styles
- **Color Scheme**: 
  - Primary: #3b82f6 (Blue)
  - Success: #10b981 (Green)
  - Warning: #f59e0b (Amber)
  - Error: #ef4444 (Red)
  - Background: #f5f5f5 (Light gray)

---

## 🧪 Testing

Run tests (when test files are added):
```bash
npm run test
```

---

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints: 480px, 600px, 768px
- Touch-friendly button sizes (44px minimum)
- Responsive layouts using flexbox/grid

---

## 🚨 Common Issues

### Issue: "Cannot find module '@/...'"
**Solution**: Check path in `tsconfig.json` - should have:
```json
{
  "paths": {
    "@/*": ["./src/*"]
  }
}
```

### Issue: "Unauthorized" errors
**Solution**: Make sure backend is running and `.env` `VITE_API_URL` is correct

### Issue: CSS not loading
**Solution**: Check that CSS files are imported in components:
```tsx
import "./ComponentName.css"
```

### Issue: Hot reload not working
**Solution**: Save file again or restart dev server

---

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

This creates `dist/` folder ready for deployment.

### Deploy to Netlify/Vercel
```bash
# Netlify
netlify deploy --prod --dir=dist

# Vercel
vercel --prod
```

### Environment Variables for Production
Set in hosting platform:
- `VITE_API_URL` - Production backend URL
- `VITE_APP_NAME` - App name
- `VITE_DEBUG` - false

---

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Vite Documentation](https://vitejs.dev)

---

## ✅ Checklist Before Going Live

- [ ] Backend is running (`npm run dev` in backend folder)
- [ ] `.env` file is created with correct `VITE_API_URL`
- [ ] `npm install` completed
- [ ] `npm run dev` starts without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Can login/register successfully
- [ ] Can upload documents
- [ ] Can run analysis
- [ ] Can chat with AI
- [ ] CSS styles look correct
- [ ] No console errors
- [ ] Built successfully (`npm run build`)

---

Generated: 2025-02-21
