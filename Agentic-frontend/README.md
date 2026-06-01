# Agentic Frontend Service

Modern React/TypeScript frontend application with 3D visualizations, interactive UI components, and real-time communication.

## Features

- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Full type safety and enhanced developer experience
- **3D Visualizations**: Three.js integration with interactive globe and elements
- **Material-UI**: Comprehensive component library with theming
- **Real-time Chat**: WebSocket-based communication with backend services
- **Authentication**: JWT-based user authentication and protected routes
- **Responsive Design**: Mobile-first responsive design with Tailwind CSS
- **Hot Reload**: Fast development with Vite build tool

## Quick Setup

This service uses npm for dependency management and Vite for development.

### Individual Service Setup
```bash
cd Agentic-frontend
python setup.py        # Install Node.js dependencies
python run.py          # Start development server
```

### Using Master Orchestrator
```bash
# From project root
python run_all_services.py setup    # Setup all services
python run_all_services.py start    # Start all services
```

## Service Details

- **Port**: 3000
- **Build Tool**: Vite
- **Package Manager**: npm
- **Development Server**: http://localhost:3000
- **Hot Reload**: Enabled by default

## Technology Stack

- **React 18**: Component framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Three.js**: 3D graphics and visualizations
- **Material-UI**: Component library
- **Tailwind CSS**: Utility-first styling
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

## Main Documentation

For complete setup instructions, architecture details, and usage examples, see the [main README](../README.md).

## Configuration

Key configuration files:
- `vite.config.ts`: Vite build configuration
- `tailwind.config.js`: Tailwind CSS configuration
- `tsconfig.json`: TypeScript configuration
- `package.json`: Dependencies and scripts

Environment variables:
- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_WS_URL`: WebSocket connection URL 