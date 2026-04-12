# Animated Login Component Implementation Guide

## Overview
The animated characters login component provides an engaging, interactive login experience with cartoon characters that respond to user interactions and mouse movements.

## Component Architecture

### Main Component: `AnimatedLoginPage`
**File:** `src/components/ui/animated-characters-login-page.tsx`

This is the main login component that manages:
- Form state (email, password, remember me)
- Animation states (blinking, looking, peeking)
- Mouse tracking for character eyes
- Authentication and backend integration
- Error handling and loading states

### Sub-Components

#### 1. **EyeBall Component**
Renders an animated eye with tracking pupil.

**Props:**
```typescript
{
  size: number              // Eye diameter in pixels (default: 48)
  pupilSize: number        // Pupil diameter in pixels (default: 16)
  maxDistance: number      // Max pupil movement distance (default: 10)
  eyeColor: string         // CSS color for white of eye (default: "white")
  pupilColor: string       // CSS color for pupil (default: "black")
  isBlinking: boolean      // Active blink state
  forceLookX?: number      // Force look direction on X axis
  forceLookY?: number      // Force look direction on Y axis
}
```

**Features:**
- Tracks mouse position and moves pupil accordingly
- Can override mouse tracking with forced look direction
- Blink animation collapses eye to 2px height
- Smooth transitions on pupil movement

#### 2. **Pupil Component**
Renders a simple pupil dot (used for semi-circle characters).

**Props:**
```typescript
{
  size: number             // Pupil diameter in pixels (default: 12)
  maxDistance: number      // Max movement distance (default: 5)
  pupilColor: string       // CSS color (default: "black")
  forceLookX?: number      // Force look direction on X axis
  forceLookY?: number      // Force look direction on Y axis
}
```

## Character Design

### 1. Purple Character (Back)
- Shape: Tall rectangle with rounded top
- Dimensions: 180px width × 400px height
- Eyes: Full EyeBall components (size 18)
- Special behaviors:
  - Shows "surprised" expression when user types
  - Peeks when password is visible
  - Random blinking

### 2. Black Character (Middle)
- Shape: Tall rectangle with rounded top
- Dimensions: 120px width × 310px height
- Eyes: Full EyeBall components (size 16)
- Special behaviors:
  - Looks away when typing
  - Random blinking

### 3. Orange Character (Front Left)
- Shape: Semi-circle (rounded top)
- Dimensions: 240px width × 200px height
- Eyes: Just pupils (Pupil components)
- Special behaviors:
  - Looks away when password is visible
  - No blinking

### 4. Yellow Character (Front Right)
- Shape: Semi-circle (rounded top) with mouth
- Dimensions: 140px width × 230px height
- Features: Two pupils and a horizontal mouth line
- Special behaviors:
  - Looks away when password is visible
  - Mouth moves with user interactions
  - No blinking

## Animation States

### Mouse Tracking
- All characters follow the user's mouse cursor
- Face moves within limited range (±15px horizontal, ±10px vertical)
- Body leans toward cursor (skew effect up to ±6 degrees)

### Typing Animation
- Triggers when user focuses on input field
- Purple and black characters lean inward
- Characters look at each other for 800ms
- Eyes adjust position accordingly

### Password Visibility Toggle
- When password is revealed:
  - Orange and yellow look away (shame animation)
  - Purple leans over to peek (curious behavior)
  - Purple alternates between peeking and looking away
  - Other characters normalize their expressions

### Blinking
- Random interval: 3-7 seconds between blinks
- Blink duration: 150ms
- Purple character: Independent blinking
- Black character: Independent blinking
- Orange & Yellow: No blinking

### Peeking Behavior
- Triggers when password has content AND is visible
- Purple character peeks every 2-5 seconds
- Peek lasts 800ms
- Eyes look down-right (position: 4, 5)
- Alternates with looking away (position: -4, -4)

## State Management

### Form State
```typescript
email: string              // Email/phone identifier
password: string          // Password input
rememberMe: boolean       // Remember for 30 days
showPassword: boolean     // Toggle password visibility
isLoading: boolean        // Login in progress
error: string             // Error message display
```

### Animation State
```typescript
mouseX: number            // Current mouse X position
mouseY: number            // Current mouse Y position
isTyping: boolean         // User is typing
isPurpleBlinking: boolean // Purple character blink state
isBlackBlinking: boolean  // Black character blink state
isLookingAtEachOther: boolean // Looking animation state
isPurplePeeking: boolean  // Purple peeking animation state
```

## Backend Integration

### API Endpoint
**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "identifier": "user@email.com or +919876543210",
  "password": "user_password"
}
```

**Response (Success):**
```json
{
  "access_token": "jwt_token_here",
  "user": {
    "id": "user_id",
    "email": "user@email.com",
    "phone": "+919876543210",
    "name": "User Name",
    ...other fields
  }
}
```

### localStorage Usage
```javascript
localStorage.setItem("userToken", payload.access_token)
localStorage.setItem("userProfile", JSON.stringify(payload.user))
localStorage.setItem("rememberedIdentifier", email)
localStorage.setItem("urbanSentinelLocation", JSON.stringify({
  permission: "unknown",
  latitude: null,
  longitude: null,
  label: ""
}))
```

## Styling & Tailwind Classes

### Form Styling
- Input height: `h-12` (48px) for better touch target
- Border: `border-border/60` for subtlety
- Focus: `focus:border-primary` for clear indication
- Button: `h-12` with full width, rounded corners

### Character Styling
- Colors: Hardcoded CSS (not Tailwind) for specific shades
- Layout: Absolute positioning for layering
- Animations: CSS transitions (150-700ms duration)
- Z-index: 1-4 for proper layering

### Responsive Design
- Desktop (lg and up): Animated characters visible
- Mobile and tablet: Animated characters hidden, form centered
- Content width: `max-w-[420px]` for readability
- Padding: `p-8` for proper spacing on all devices

## Error Handling

### Login Errors
- Catches errors from auth API
- Displays user-friendly error messages
- Error messages shown in red box below form
- Error format: `p-3 text-red-400 bg-red-950/20 border border-red-900/30`

### Common Error Cases
1. **Invalid credentials** - Backend returns error message
2. **Network error** - Timeout or connection failure
3. **Validation error** - Missing email, invalid format, etc.

## Performance Considerations

### Mouse Event Listener
- Single listener on window for all characters
- Uses throttled state updates (React batching)
- Removed on component unmount

### Animation Timings
- Blink: 150ms (quick, natural feeling)
- Transitions: 200-700ms (smooth, not jarring)
- Random intervals: 3-7 seconds (natural variation)

### Optimizations
- useRef for direct DOM access to avoid unnecessary renders
- Conditional rendering to hide elements during blink
- Transform over opacity (GPU accelerated)
- CSS transitions instead of JS animations

## Testing Scenarios

### 1. Form Submission
```
✓ Valid email + password → Successful login
✓ Invalid email → Error message
✓ Invalid password → Error message
✓ Empty fields → Validation error
```

### 2. Character Animations
```
✓ Mouse move → Characters follow cursor
✓ Focus input → Characters look at each other
✓ Type in field → Body lean animation
✓ Toggle password → Characters look away
```

### 3. Features
```
✓ Remember me checkbox → Stores identifier
✓ Forgot password link → Navigates to /forgot-password
✓ Sign up link → Navigates to /register
✓ Show/hide password → Toggle input type
```

## Customization Guide

### Change Character Colors
Edit the hardcoded color values in the component:
```typescript
backgroundColor: '#6C3FF5',  // Purple
backgroundColor: '#2D2D2D',  // Black
backgroundColor: '#FF9B6B',  // Orange
backgroundColor: '#E8D754',  // Yellow
```

### Adjust Animation Speed
Modify transition durations:
```typescript
className="... transition-all duration-700 ..."  // 700ms
style={{transition: 'transform 0.1s ease-out'}}   // 100ms
```

### Change Character Size
Update the absolute `height` and `width` values:
```typescript
width: '180px',  // Change for Purple
height: '400px'
```

### Modify Blinking Frequency
Adjust the random interval in useEffect:
```typescript
const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;
// 3000-7000ms interval, change these numbers
```

## Known Limitations

1. **Mouse tracking only on desktop** - Touch devices show fixed characters
2. **Eyes only follow on screen** - Off-screen mouse position not tracked
3. **Single character layer** - Depth sorting fixed, can't reorder
4. **Animation complexity** - Heavy computations at high DPI
5. **Email only** - Phone number support would need backend changes

## Future Enhancement Ideas

1. Add phone number input with country code selector
2. Make character colors configurable via props
3. Add 2FA/OTP verification step
4. Add biometric authentication indicator
5. Add dark/light mode character themes
6. Add accessibility indicators for screen readers
7. Add keyboard navigation for form traversal
8. Add auto-blink on focus loss
9. Add celebration animation on successful login
10. Add sound effects (optional, toggleable)

