# CogniVox Landing Page

An isolated React + Vite landing page application for CogniVox, featuring beautiful animations, responsive design, and modern UI components.

## Features

- 🎨 **Beautiful UI**: Modern gradient designs with glassmorphism effects
- ✨ **Animations**: Smooth animations with Framer Motion
- 🌟 **Visual Effects**: Star field background, meteors, and magic cards
- 🎭 **Theme Support**: Dark and light theme toggle
- 📱 **Responsive**: Mobile-first responsive design
- 🔐 **Authentication**: Login and signup flows (mock implementation)
- ⚡ **Fast**: Built with Vite for lightning-fast development

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository and navigate to the landing page directory:
```bash
cd Cognivox-Landing
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and visit `http://localhost:3001`

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── magicui/         # Magic UI components (meteors, cards)
│   └── StarField.tsx    # Animated star field background
├── contexts/            # React contexts
│   ├── AuthContext.tsx  # Authentication context
│   └── ThemeContext.tsx # Theme management
├── pages/               # Page components
│   ├── LandingPage.tsx  # Main landing page
│   ├── Login.tsx        # Login page
│   └── Signup.tsx       # Signup page
├── themes/              # Theme configurations
├── lib/                 # Utility functions
└── App.tsx              # Main app component
```

## Technologies Used

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **React Router** - Navigation
- **React Hot Toast** - Notifications
- **React Icons** - Icon library

## Demo Features

- Interactive search interface with autocomplete
- Animated service cards
- Technology stack showcase
- Business metrics display
- Contact forms (UI only)
- Theme switching
- Mock authentication

## Customization

### Themes

Edit `src/themes/theme.ts` to customize colors and styling.

### Content

The landing page content can be customized by editing the data arrays in `src/pages/LandingPage.tsx`:

- `services` - Service offerings
- `businessBenefits` - Key metrics
- `techStack` - Technology stack

### Styling

This project uses Tailwind CSS. Edit `tailwind.config.js` to customize the design system.

## Deployment

Build the project for production:

```bash
npm run build
```

The built files will be in the `dist` directory, ready for deployment to any static hosting service.

## License

This project is part of the CogniVox ecosystem. 