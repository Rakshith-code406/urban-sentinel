# shadcn / Tailwind / TypeScript Setup Notes

This frontend currently uses:

- Vite
- React
- JavaScript / JSX
- Custom CSS

It does not yet have:

- Tailwind CSS
- full TypeScript project setup
- shadcn/ui initialization

## Current default paths

- Components: `src/components`
- UI components: `src/components/ui`
- Global styles: `src/styles/base.css`
- Vite root stylesheet still exists at `src/index.css`, but the app currently imports `src/styles/base.css` from `src/main.jsx`

Creating `src/components/ui` is important because shadcn-style components are meant to live in a consistent shared UI folder. That makes imports predictable, keeps generated UI separate from page components, and avoids scattered one-off component files.

## Install Tailwind CSS in this Vite app

Run:

```bash
npm install -D tailwindcss @tailwindcss/vite
```

Then update `vite.config.js` to add the Tailwind plugin and import Tailwind in your main stylesheet using the Tailwind v4 approach.

If you want the classic config-based setup instead, use:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## Add TypeScript support

Install:

```bash
npm install -D typescript @types/node
```

Then create:

- `tsconfig.json`
- `tsconfig.app.json`

After that, rename files gradually:

- `src/main.jsx` -> `src/main.tsx`
- `src/App.jsx` -> `src/App.tsx`

You do not need to migrate every file at once. Vite can handle mixed JS and TS during migration.

## Initialize shadcn/ui

After Tailwind and TypeScript are ready, run:

```bash
npx shadcn@latest init
```

Recommended answers for this project:

- Framework: `Vite`
- Language: `TypeScript`
- Components path: `src/components`
- UI path: `src/components/ui`
- Utils path: `src/lib/utils`

## New component files added

- `src/components/ui/container-scroll-animation.tsx`
- `src/components/demo.tsx`

## Dependency added

Installed:

```bash
npm install framer-motion
```

## Important note

The new scroll component uses Tailwind utility classes, so it will not look correct until Tailwind is installed and configured.
