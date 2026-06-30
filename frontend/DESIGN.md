# Design System Strategy: The Intelligent Stratum

## 1. Overview & Creative North Star: "The Digital Curator"
This design system moves away from the "chat bubble" cliché of consumer AI. Instead, it adopts the persona of **The Digital Curator**. This is a high-end, editorial approach to enterprise data, where the AI doesn't just "talk"—it synthesizes, organizes, and presents intelligence.

The visual language is rooted in **Architectural Depth**. We break the traditional flat-web template by using intentional asymmetry, overlapping "floating" containers, and an aggressive focus on tonal hierarchy over structural lines. By leveraging the contrast between the technical precision of `Inter` and the editorial authority of `Manrope`, we create a space that feels like a premium research laboratory rather than a generic support tool.

## 2. Colors: Tonal Architecture
The palette is a sophisticated "Deep Space" environment. It utilizes a base of `#030f1d` with calculated shifts in luminosity to define space.

*   **Primary (`#64b3ff`) & Secondary (`#b486ff`):** These are your "Intelligence Accents." Use them sparingly to highlight the AI's presence or active data processing.
*   **The "No-Line" Rule:** 1px solid borders are strictly prohibited for sectioning. Structural boundaries must be defined solely through background shifts. For instance, a `surface-container-low` side panel should sit directly against a `surface` background. The eye should perceive the edge through the change in value, not a drawn line.
*   **Surface Hierarchy & Nesting:** Treat the UI as a series of physical layers.
    *   **Level 0 (Base):** `surface` (#030f1d) – The canvas.
    *   **Level 1 (Sections):** `surface-container-low` (#061423) – For broad layout divisions.
    *   **Level 2 (Cards):** `surface-container` (#0b1a2b) – For primary content blocks.
    *   **Level 3 (Interactive):** `surface-container-high` (#102133) – For hovered states or active overlays.
*   **The "Glass & Gradient" Rule:** To provide "soul," the main AI input and primary CTA should utilize a linear gradient from `primary` to `primary-container`. For floating inspector panels, use a **Glassmorphism** effect: `surface-variant` at 60% opacity with a `24px` backdrop-blur.

## 3. Typography: The Editorial Scale
We use a dual-typeface system to balance technical reliability with high-level synthesis.

*   **Display & Headlines (Manrope):** This is our "Editorial" voice. It should feel authoritative. Use `display-md` for landing moments and `headline-sm` for document titles. The wider apertures of Manrope convey openness and modernity.
*   **Titles & Body (Inter):** This is our "Utility" voice. Inter’s high x-height and neutral tone are used for the chatbot’s output, document metadata, and system labels.
*   **Hierarchy as Identity:** Use a high contrast in weight—e.g., a `headline-lg` in Semi-Bold next to `body-sm` in Regular—to create a sense of organized complexity.

## 4. Elevation & Depth: Tonal Layering
In this system, light is the primary architect. We avoid harsh shadows in favor of ambient occlusion.

*   **The Layering Principle:** Depth is achieved by stacking. An "Inner Card" should be `surface-container-lowest` placed upon a `surface-container-low` background. This creates a "recessed" or "carved" look that feels more premium than a simple drop shadow.
*   **Ambient Shadows:** For floating elements (like a file preview), use a shadow with a blur of `40px` and a spread of `-10px`. The shadow color must be a tinted version of `on-surface` at 6% opacity, ensuring the shadow looks like light being absorbed rather than black ink.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility, use the `outline-variant` token at **15% opacity**. It should be felt, not seen.
*   **Signature Texture:** Apply a subtle noise texture (3% opacity) over the `surface` layer to break the digital flatness and give the dark theme a tactile, "fine paper" quality.

## 5. Components: Functional Primitives

### Input Fields & Search
Avoid the "input box" look. Use a `surface-container-highest` background with a `xl` (1.5rem) corner radius. The focus state should not be a stroke, but a subtle glow using `surface-tint` with a low-opacity outer spread.

### Cards & Document Previews
*   **Forbid Dividers:** Do not use lines to separate header from body. Use a `1.5rem` vertical padding gap.
*   **Anatomy:** Use `md` (0.75rem) or `lg` (1rem) roundedness. Content should be grouped by proximity and subtle shifts in background color (e.g., a `surface-container-low` header on a `surface-container` card).

### AI Interaction Chips
Instead of standard buttons, use **Action Chips** for RAG-specific tasks (e.g., "Summarize Source," "Find Discrepancies").
*   **Style:** `surface-container-highest` background, `full` (9999px) radius, with a `secondary` icon.

### Buttons
*   **Primary:** A gradient from `primary` to `primary-dim`. No border. White text (`on-primary`).
*   **Tertiary:** Transparent background with `primary` text. Hover state is a subtle `surface-bright` background shift.

### Source Citations (RAG-specific)
A "Smart Document Assistant" needs elegant citations. Use a small, `surface-container-high` card with a `sm` (0.25rem) radius and a `secondary` left-accent bar (2px width). This provides "Trust" through visual organization.

## 6. Do’s and Don’ts

| Do | Don’t |
| :--- | :--- |
| **Do** use `surface-container` tiers to create hierarchy. | **Don't** use 1px solid borders to separate sections. |
| **Do** use `Manrope` for large headings to feel "Editorial." | **Don't** use `Inter` for everything; it will look "Generic Tech." |
| **Do** use large, soft, tinted shadows for floating panels. | **Don't** use pure black or high-opacity drop shadows. |
| **Do** use glassmorphism and backdrop-blur for overlays. | **Don't** use opaque solid blocks for modals. |
| **Do** prioritize white space (negative space) as a separator. | **Don't** use divider lines to separate list items or card sections. |
| **Do** use the `secondary` purple for "AI Thinking" states. | **Don't** use "Traffic Light" colors (Red/Green) for AI status. |