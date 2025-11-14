# Chat Interface Design Prompt for RAG System

Design a chat interface and UI for a RAG (Retrieval-Augmented Generation) system that matches the exact design system and color palette described below.

## Color Palette (Alpha Data Brand Colors)

Use these CSS custom properties throughout the design:

```css
:root {
  /* Primary Brand Colors */
  --alpha-green: #76B900;
  --alpha-green-dark: #5A8F00;
  --alpha-green-light: #8FD900;
  
  /* Neutral Colors */
  --alpha-black: #000000;
  --alpha-white: #FFFFFF;
  --alpha-gray-dark: #1a1a1a;
  --alpha-gray: #333333;
  --alpha-gray-light: #666666;
  --alpha-gray-lighter: #999999;
  
  /* Background Colors */
  --alpha-bg-dark: #0a0a0a;
  --alpha-bg: #1a1a1a;
  --alpha-bg-primary: #000000;
  --alpha-bg-secondary: #1a1a1a;
  
  /* Text Colors */
  --alpha-text-primary: #FFFFFF;
  --alpha-text-secondary: #999999;
  
  /* Border Colors */
  --alpha-border: #333333;
}
```

## Design Principles

1. **Dark Theme**: The interface uses a dark theme with black (#000000) as the primary background and dark grays (#1a1a1a) for secondary surfaces.

2. **Brand Green Accent**: The primary brand color (#76B900) is used for:
   - Primary buttons and CTAs
   - User message bubbles
   - Active states and highlights
   - Borders and accents
   - Hover states

3. **Typography**:
   - Font family: System fonts (-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', etc.)
   - Headers use uppercase text with letter-spacing (0.5px to 1px)
   - Font weights: 500-700 for emphasis
   - Font sizes: 11px-32px depending on hierarchy

4. **Spacing & Layout**:
   - Padding: 12px, 16px, 20px, 24px, 32px
   - Border radius: 6px, 8px, 12px
   - Gaps: 8px, 12px, 16px, 24px
   - Consistent use of flexbox for layouts

## Component Specifications

### 1. Main Chat Interface Layout

- **Container**: Full height flexbox layout with dark background (--alpha-bg)
- **Layout Structure**:
  - Left sidebar (300px width, collapsible) for chat history
  - Main chat area (flex: 1) with messages and input
  - Optional right panel (350-400px) for additional features
- **Background**: --alpha-bg-primary (#000000) for main area, --alpha-bg-secondary (#1a1a1a) for panels

### 2. Chat Messages

**User Messages**:
- Background: --alpha-green (#76B900)
- Text color: --alpha-black (#000000)
- Font weight: 500
- Alignment: Right side (flex-end)
- Max width: 85%
- Border radius: 12px
- Padding: 8px 12px
- Avatar: Circular (40px), green background with black text
- Animation: fadeIn (0.3s ease-in) with translateY effect

**Assistant Messages**:
- Background: --alpha-bg-secondary (#1a1a1a)
- Text color: --alpha-text-primary (#FFFFFF)
- Border: 1px solid --alpha-border (#333333)
- Alignment: Left side (flex-start)
- Max width: 85%
- Border radius: 12px
- Padding: 8px 12px
- Avatar: Circular (40px), dark gray background with green border and green text
- Box shadow: 0 2px 8px rgba(0, 0, 0, 0.2)

**Message Features**:
- Timestamp: 11px font, --alpha-text-secondary color
- Gap between messages: 24px
- Container padding: 32px

### 3. Input Area

- **Container**: 
  - Padding: 24px 32px
  - Background: --alpha-bg-primary
  - Border-top: 1px solid --alpha-border

- **Input Container**:
  - Background: --alpha-gray-dark (#1a1a1a)
  - Border: 2px solid --alpha-gray (#333333)
  - Border radius: 12px
  - Padding: 14px 18px
  - Display: flex with gap: 12px
  - Focus state: Border changes to --alpha-green with box-shadow: 0 0 0 3px rgba(118, 185, 0, 0.1)

- **Text Input**:
  - Background: transparent
  - Color: --alpha-text-primary
  - Font size: 15px
  - Max height: 150px (auto-resize)
  - Placeholder: --alpha-gray-lighter (#999999)

- **Send Button**:
  - Background: --alpha-green (#76B900)
  - Color: --alpha-black
  - Size: 44px × 44px
  - Border radius: 8px
  - Hover: --alpha-green-light with scale(1.05) and box-shadow: 0 4px 12px rgba(118, 185, 0, 0.4)
  - Disabled: opacity 0.4, --alpha-gray background

### 4. Buttons

**Primary Buttons**:
- Background: --alpha-green (#76B900)
- Color: --alpha-black
- Padding: 10px 16px or 12px 20px
- Border radius: 6px or 8px
- Font weight: 600-700
- Font size: 13px-14px
- Text transform: uppercase
- Letter spacing: 0.5px
- Box shadow: 0 2px 8px rgba(118, 185, 0, 0.3)
- Hover: --alpha-green-light with translateY(-1px to -2px) and enhanced shadow
- Active: translateY(0)

**Secondary Buttons**:
- Background: --alpha-gray-dark (#1a1a1a)
- Border: 1px solid --alpha-border
- Color: --alpha-text-primary
- Hover: Background --alpha-gray, border-color --alpha-green, color --alpha-green

### 5. Sidebar (Chat History)

- **Width**: 300px (collapsible to 0)
- **Background**: --alpha-bg (#1a1a1a)
- **Border**: Right border 1px solid --alpha-gray
- **Header**:
  - Background: --alpha-black
  - Padding: 20px
  - Border-bottom: 1px solid --alpha-gray
  - Min height: 70px

- **New Chat Button**:
  - Full width
  - Background: --alpha-green
  - Color: --alpha-black
  - Padding: 12px 20px
  - Border radius: 6px
  - Font weight: 600
  - Text transform: uppercase

- **History Items**:
  - Background: --alpha-gray-dark
  - Border: 1px solid --alpha-gray
  - Border radius: 8px
  - Padding: 14px
  - Margin bottom: 10px
  - Hover: Background --alpha-gray, border-color --alpha-green, transform translateX(2px)
  - Active state: Background --alpha-black, border-color --alpha-green, box-shadow with green glow

- **Scrollbar**:
  - Width: 8px
  - Track: --alpha-bg-dark
  - Thumb: --alpha-gray, border-radius: 4px
  - Thumb hover: --alpha-gray-light

### 6. Welcome Screen

- **Container**: Centered, padding: 80px 20px
- **Title**:
  - Font size: 32px
  - Font weight: 600
  - Color: --alpha-text-primary
  - Text transform: uppercase
  - Letter spacing: 1px
  - Margin bottom: 16px

- **Description**:
  - Font size: 16px
  - Color: --alpha-text-secondary
  - Margin bottom: 40px

- **Example Questions Box**:
  - Background: --alpha-bg-secondary
  - Border: 1px solid --alpha-border
  - Border radius: 12px
  - Padding: 32px
  - Max width: 600px
  - Box shadow: 0 4px 20px rgba(0, 0, 0, 0.1)

- **Example Questions List**:
  - List style: none
  - Items: Padding 12px 0, color --alpha-text-primary, font-size 14px
  - Border-bottom: 1px solid --alpha-border
  - Hover: Color --alpha-green, padding-left 16px, border-left 2px solid --alpha-green
  - Cursor: pointer

### 7. Loading/Typing Indicator

- **Container**: Flex with gap: 6px
- **Background**: --alpha-gray-dark
- **Border**: 1px solid --alpha-gray
- **Border radius**: 8px
- **Padding**: 16px 20px
- **Dots**:
  - Size: 8px × 8px
  - Background: --alpha-green
  - Border radius: 50%
  - Animation: typing (1.4s infinite) with translateY and opacity changes
  - Staggered delays: 0s, 0.2s, 0.4s

### 8. Panels (Right Side)

- **Panel Container**:
  - Width: 350px-400px
  - Background: --alpha-bg-secondary
  - Border-left: 3px solid --alpha-green
  - Box shadow: -4px 0 20px rgba(0, 0, 0, 0.3)
  - Display: flex column

- **Panel Header**:
  - Background: Linear gradient from --alpha-bg to --alpha-bg-secondary
  - Border-bottom: 2px solid --alpha-border
  - Padding: 18px 20px
  - Box shadow: 0 2px 8px rgba(0, 0, 0, 0.1)
  - Title: Font size 16px, weight 700, uppercase, letter-spacing 1px
  - Title has green accent bar (4px width, 18px height) on left

- **Panel Content**:
  - Flex: 1
  - Overflow-y: auto
  - Padding: 20px
  - Scrollbar: 10px width, styled with green hover

- **Panel Toggle Button**:
  - Position: Absolute, left: -20px, top: 50%
  - Size: 40px × 80px
  - Background: --alpha-green
  - Color: --alpha-black
  - Border radius: 8px 0 0 8px
  - Hover: --alpha-green-light with translateX(-5px)

### 9. Tables/Data Display

- **Table Container**:
  - Border: 1px solid --alpha-gray
  - Border radius: 8px
  - Background: --alpha-gray-dark
  - Overflow: auto
  - Max height: 400px

- **Table Header**:
  - Background: --alpha-black
  - Padding: 12px 16px
  - Border-bottom: 1px solid --alpha-gray

- **Table Headers (th)**:
  - Background: --alpha-black
  - Color: --alpha-green
  - Font weight: 600
  - Font size: 12px
  - Text transform: uppercase
  - Letter spacing: 0.5px
  - Border-bottom: 2px solid --alpha-green
  - Padding: 12px 16px
  - Sticky: top: 0

- **Table Cells (td)**:
  - Padding: 12px 16px
  - Color: --alpha-text-primary
  - Font size: 13px
  - Border-bottom: 1px solid --alpha-gray

- **Table Rows**:
  - Hover: Background --alpha-bg

### 10. Scrollbars

All scrollbars should be styled consistently:
- Width: 8px (or 10px for panels)
- Track: --alpha-bg-dark
- Thumb: --alpha-gray, border-radius: 4px-5px
- Thumb hover: --alpha-gray-light or --alpha-green (for panels)

### 11. Animations & Transitions

- **Fade In**: Messages fade in with translateY(10px to 0) over 0.3s
- **Hover Transitions**: All interactive elements use transition: all 0.2s
- **Button Hovers**: Transform effects (translateY, scale, translateX)
- **Panel Transitions**: Width and visibility transitions over 0.3s ease

### 12. Typography Hierarchy

- **H1/Page Title**: 24px-32px, weight 700, uppercase, letter-spacing 1px
- **H2/Section Title**: 16px-20px, weight 600-700, uppercase, letter-spacing 0.5px-1px
- **H3/Panel Title**: 16px, weight 700, uppercase, letter-spacing 1px
- **Body Text**: 13px-15px, weight 400-500
- **Small Text**: 11px-12px, weight 400
- **Labels**: 12px-14px, weight 600, uppercase, letter-spacing 0.5px

### 13. Interactive States

- **Hover**: Border color changes to --alpha-green, background lightens, slight transform
- **Active/Selected**: Background --alpha-black, border-color --alpha-green, box-shadow with green glow
- **Focus**: Border-color --alpha-green with box-shadow ring
- **Disabled**: Opacity 0.4-0.6, cursor not-allowed

### 14. Error States

- **Error Messages**:
  - Background: rgba(255, 0, 0, 0.1)
  - Border: 1px solid rgba(255, 0, 0, 0.3)
  - Color: #ff6666
  - Border radius: 8px
  - Padding: 16px

### 15. Success States

- **Success Messages**:
  - Background: rgba(118, 185, 0, 0.1)
  - Border: 1px solid --alpha-green
  - Color: --alpha-green
  - Border radius: 6px
  - Padding: 12px

## Implementation Requirements

1. **Use CSS Custom Properties**: All colors must use the CSS variables defined above
2. **Responsive Design**: Ensure the interface works on different screen sizes
3. **Accessibility**: Maintain proper contrast ratios and keyboard navigation
4. **Consistent Spacing**: Use the spacing scale consistently (8px, 12px, 16px, 20px, 24px, 32px)
5. **Smooth Animations**: All transitions should be smooth (0.2s-0.3s)
6. **Dark Theme Focus**: The design is primarily dark-themed with green accents

## Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│                    App Header                           │
│  (Black bg, green bottom border, title with green bar)  │
├──────────┬──────────────────────────────┬────────────────┤
│          │                              │                │
│ History  │     Chat Messages Area       │  Right Panel   │
│ Sidebar  │     (Scrollable)             │  (Optional)    │
│ (300px)  │                              │  (350-400px)   │
│          │                              │                │
│          ├──────────────────────────────┤                │
│          │     Input Area               │                │
│          │     (Text input + Send)      │                │
└──────────┴──────────────────────────────┴────────────────┘
```

## Key Visual Elements

1. **Green Accent Bars**: 4px wide vertical bars used in headers and titles
2. **Rounded Corners**: Consistent use of 6px, 8px, and 12px border-radius
3. **Box Shadows**: Subtle shadows (0 2px 8px rgba(0, 0, 0, 0.2)) for depth
4. **Green Glow Effects**: Box-shadow with rgba(118, 185, 0, 0.2-0.5) for active states
5. **Uppercase Text**: Headers, labels, and buttons use uppercase with letter-spacing
6. **Smooth Transitions**: All interactive elements have 0.2s-0.3s transitions

## Notes for RAG System

For the RAG system, adapt the following:
- Replace SQL query display with source citations/references
- Replace table data display with document snippets/chunks
- Replace "Select Table" panel with "Document Sources" or "Knowledge Base" panel
- Replace Excel upload with document upload (PDF, TXT, etc.)
- Welcome message should mention RAG/document querying capabilities
- Example questions should be about document content, not database queries

Maintain the exact same visual design, color palette, spacing, typography, and interaction patterns described above.

