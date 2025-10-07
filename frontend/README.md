# PharmGPT Frontend

Modern React frontend for the PharmGPT AI-powered pharmacology assistant focused on pharmacology education and research.

## Features

- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Authentication**: JWT-based authentication with automatic token refresh
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Chat**: Interactive chat interface with AI responses
- **Document Upload**: Support for PDF, DOCX, TXT, MD, and PPTX files
- **Admin Panel**: Administrative interface for user and system management
- **Support System**: Built-in contact and support request functionality

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Router** for navigation
- **React Query** for state management and API caching
- **React Hook Form** with Zod validation
- **Axios** for API communication
- **Framer Motion** for animations

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. **Clone and install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `VITE_APP_NAME` | Application name | `PharmGPT` |
| `VITE_APP_VERSION` | Application version | `2.0.0` |

## Project Structure

```
frontend/
├── public/                  # Static assets
├── src/
│   ├── components/         # Reusable components
│   │   ├── forms/         # Form components
│   │   ├── Layout.tsx     # Main layout
│   │   ├── Navbar.tsx     # Navigation
│   │   └── ...
│   ├── contexts/          # React contexts
│   │   └── AuthContext.tsx
│   ├── lib/               # Utilities and API
│   │   ├── api.ts         # API client
│   │   └── utils.ts       # Helper functions
│   ├── pages/             # Page components
│   │   ├── admin/         # Admin pages
│   │   ├── HomePage.tsx
│   │   ├── LoginPage.tsx
│   │   └── ...
│   ├── App.tsx            # Main app component
│   └── main.tsx           # Entry point
├── index.html             # HTML template
├── package.json           # Dependencies
├── tailwind.config.js     # Tailwind configuration
├── vite.config.ts         # Vite configuration
└── netlify.toml           # Netlify deployment config
```

## Key Components

### Authentication
- `AuthContext`: Global authentication state
- `LoginForm` & `RegisterForm`: Authentication forms
- `ProtectedRoute` & `AdminRoute`: Route protection

### Layout
- `Layout`: Main application layout
- `Navbar`: Responsive navigation with user menu
- `Footer`: Application footer

### Pages
- `HomePage`: Landing page with features
- `DashboardPage`: User dashboard
- `ChatPage`: Chat interface (placeholder)
- `SupportPage`: Support and contact
- Admin pages for system management

## Deployment

### Netlify (Recommended)

1. **Connect repository to Netlify**
2. **Configure build settings:**
   - Build command: `npm run build`
   - Publish directory: `dist`
3. **Set environment variables in Netlify dashboard**
4. **Deploy automatically on push**

### Manual Deployment

1. **Build the application**
   ```bash
   npm run build
   ```

2. **Deploy the `dist` folder** to your hosting provider

### Docker

```bash
# Build
docker build -t pharmgpt-frontend .

# Run
docker run -p 3000:80 pharmgpt-frontend
```

## Development

### Code Style

- ESLint for code linting
- Prettier for code formatting
- TypeScript for type safety

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Adding New Features

1. **Create components** in `src/components/`
2. **Add pages** in `src/pages/`
3. **Update routing** in `App.tsx`
4. **Add API calls** in `src/lib/api.ts`
5. **Style with Tailwind CSS**

## API Integration

The frontend communicates with the FastAPI backend through:

- **Authentication**: Login, register, token refresh
- **Chat**: Conversations, messages, AI responses
- **Documents**: Upload and management
- **Admin**: User management, system stats
- **Support**: Contact forms and tickets

## Responsive Design

The application is fully responsive with:
- Mobile-first design approach
- Responsive navigation with mobile menu
- Adaptive layouts for different screen sizes
- Touch-friendly interactions

## Performance

- **Code splitting** with React.lazy
- **Image optimization** with WebP support
- **Caching** with React Query
- **Bundle optimization** with Vite
- **CDN delivery** via Netlify

## Security

- **XSS protection** with Content Security Policy
- **Secure token storage** with automatic refresh
- **Input validation** with Zod schemas
- **HTTPS enforcement** in production

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

- **Build errors**: Check Node.js version (18+ required)
- **API errors**: Verify `VITE_API_URL` environment variable
- **Styling issues**: Ensure Tailwind CSS is properly configured
- **Routing issues**: Check React Router configuration

### Getting Help

- Check browser console for errors
- Verify environment variables
- Review network requests in DevTools
- Contact support team

## License

MIT License - see LICENSE file for details