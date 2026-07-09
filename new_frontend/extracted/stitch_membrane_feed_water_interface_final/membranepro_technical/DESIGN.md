---
name: MembranePro Technical
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e5'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f2ff'
  surface-container: '#ededf9'
  surface-container-high: '#e7e7f4'
  surface-container-highest: '#e2e1ee'
  on-surface: '#191b24'
  on-surface-variant: '#424655'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fc'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0054d8'
  primary: '#0051d3'
  on-primary: '#ffffff'
  primary-container: '#2e6bf2'
  on-primary-container: '#fefcff'
  inverse-primary: '#b3c5ff'
  secondary: '#495c94'
  on-secondary: '#ffffff'
  secondary-container: '#acbffe'
  on-secondary-container: '#394c84'
  tertiary: '#a13f00'
  on-tertiary: '#ffffff'
  tertiary-container: '#c85209'
  on-tertiary-container: '#0e0200'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#00174a'
  on-primary-fixed-variant: '#003ea6'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b3c5ff'
  on-secondary-fixed: '#00174a'
  on-secondary-fixed-variant: '#31447b'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2e00'
  background: '#faf8ff'
  on-background: '#191b24'
  surface-variant: '#e2e1ee'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.25'
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.0'
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  margin-desktop: 32px
  margin-mobile: 16px
  gutter: 16px
---

## Brand & Style
MembranePro is a high-precision industrial utility designed for engineers and process operators. The brand personality is **Technical, Methodical, and Precise**. It avoids unnecessary ornamentation in favor of data density and functional clarity.

The visual style is **Corporate Modern with a Technical Edge**. It utilizes a clean, systematic approach similar to modern SaaS platforms but maintains a rigorous, grid-based structure suitable for complex data entry and calculation-heavy workflows. The interface prioritizes legibility and logical grouping over "delight," fostering a sense of reliability and institutional trust.

## Colors
The palette is rooted in a refined technical spectrum designed for clarity and professional depth. 
- **Primary Electric Blue (#326ef5)**: Used for high-emphasis actions, active states, and branding. It provides a vibrant, high-contrast signal for primary progress.
- **Secondary Slate-Blue (#6275af)**: A more muted, professional tone reserved for supporting technical information and secondary navigation elements.
- **Tertiary Burnt Orange (#bf4c00)**: Used sparingly for warnings or cautionary data points that require engineer attention without reaching "error" status.
- **Neutrals**: A balanced neutral palette (using `#757681` as a foundation) keeps the interface feeling grounded and surgical. Surface containers use pure white to pop against cool-toned backgrounds.

## Typography
The system uses a dual-font approach:
1. **Inter**: The workhorse for the UI. It provides high legibility for labels, body text, and headlines. Its neutral character doesn't distract from technical data.
2. **JetBrains Mono**: Used for specific "technical" labels and data values. The monospaced nature helps engineers compare numerical strings and see tabular data clearly.

**Hierarchy Rules:**
- **Headlines**: Semi-bold weight with tight tracking for a professional look.
- **Labels**: Use JetBrains Mono for metadata, units, or status indicators to distinguish them from descriptive text.
- **Body**: Standardized 14px size for the majority of data-heavy views to maintain high information density.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. While the outer margins are fixed at 32px on desktop, internal modules use a fluid grid to maximize the visibility of technical tables.

- **Rhythm**: An 8px base grid drives all spacing. 
- **Density**: Use `sm` (8px) for related input groups and `md` (16px) for major component gaps. 
- **Desktop Strategy**: A 12-column grid is standard. Main content areas typically span 8-9 columns, with a 3-4 column sidebar for secondary parameters.
- **Mobile Strategy**: Margins shrink to 16px, and all multi-column layouts stack vertically. Navigation moves to a condensed header or hamburger menu.

## Elevation & Depth
The system uses **Tonal Layering and Low-Contrast Outlines** rather than heavy shadows.

- **Level 0 (Background)**: Uses a very subtle neutral-grey canvas to provide contrast for active surfaces.
- **Level 1 (Cards/Modules)**: White surfaces with a 1px border (`outline-variant`) and a very subtle `shadow-sm` (light neutral).
- **Sticky Elements**: The top navigation uses a `backdrop-blur-md` with 95% opacity to maintain context while scrolling.
- **Interactions**: On focus, elements (inputs/buttons) use a primary-colored glow/outline (#326ef5) to provide clear visual feedback without disrupting the flat aesthetic.

## Shapes
The shape language is **Soft yet Structured**. 
- **Standard Radius**: 4px (`0.25rem`) for most buttons and inputs to maintain a crisp, professional feel.
- **Container Radius**: 8px (`0.5rem`) for cards and modules.
- **High-Emphasis**: 12px (`0.75rem`) for large action buttons or floating elements.
- **Pills**: Only used for tags or status indicators where maximum visual distinction from rectangular data fields is required.

## Components
- **Buttons**: Primary buttons are solid Electric Blue (#326ef5) with white text. Ghost buttons use `on-surface-variant` text and no background until hover.
- **Input Fields**: Must have a 1px border. Focus state is critical; border color changes to Primary with a soft glow. Use `label-sm` for units (e.g., "mg/L") placed inside the trailing edge of the input.
- **Technical Cards**: A white container with a 1px `border-muted` bottom header rule. The header should contain the title in `headline-sm` and any contextual actions.
- **Data Tables**: Use condensed row heights. Header cells use `label-sm` with a background fill of `surface-container-low`.
- **Navigation**: The TopNavBar is 64px high, using a thin `outline-variant` bottom border for separation. Active links are marked with a 2px primary-colored bottom border.
- **Custom Scrollbar**: Keep scrollbars unobtrusive using a light neutral thumb and a 4px radius to match the technical aesthetic.