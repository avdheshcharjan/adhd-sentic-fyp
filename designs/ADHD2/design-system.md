# ADHD2 — Design System: "The Cognitive Sanctuary"

**Project ID:** `2898718650865589337`
**Origin:** Google Stitch
**Device:** Desktop (1280x1024 base)
**Fonts:** Lexend (headline, body, label)
**Color Mode:** Dark
**Roundness:** ROUND_FULL

---

## Screens

| # | Screen | File | Dimensions |
|---|--------|------|------------|
| 1 | Ambient State | `01-ambient-state.html` | 2560x2048 |
| 2 | Expanded Panel State | `02-expanded-panel-state.html` | 2560x2048 |
| 3 | Sanctuary Dynamic Island Flow | `03-sanctuary-dynamic-island-flow.html` | 1280x1024 |
| 4 | Glanceable State | `04-glanceable-state.html` | 2560x2048 |
| 5 | Alert State | `05-alert-state.html` | 2944x2432 |
| 6 | Dormant State | `06-dormant-state.html` | 2560x2048 |

---

## Color Palette

### Primary
- `primary`: #99cdf0
- `primary_container`: #0a4c69
- `primary_dim`: #8bbfe2
- `primary_fixed`: #c6e7ff
- `primary_fixed_dim`: #a7dbfe
- `on_primary`: #004562
- `on_primary_container`: #a2d7fa

### Secondary
- `secondary`: #82a0c6
- `secondary_container`: #1d3d5e
- `secondary_dim`: #82a0c6
- `on_secondary`: #00213d
- `on_secondary_container`: #a3c2e9

### Tertiary
- `tertiary`: #e8fff0
- `tertiary_container`: #c3f7db
- `tertiary_dim`: #b5e8cd
- `on_tertiary`: #396853
- `on_tertiary_container`: #31604b

### Surfaces
- `surface`: #0e0e10
- `surface_bright`: #2b2c32
- `surface_container`: #19191d
- `surface_container_high`: #1f1f24
- `surface_container_highest`: #25252b
- `surface_container_low`: #131316
- `surface_container_lowest`: #000000
- `surface_tint`: #99cdf0
- `surface_variant`: #25252b

### Text
- `on_surface`: #e6e4ec
- `on_surface_variant`: #abaab1
- `on_background`: #e6e4ec
- `background`: #0e0e10

### Outline
- `outline`: #75757b
- `outline_variant`: #47474d

### Error
- `error`: #ee7d77
- `error_container`: #7f2927
- `error_dim`: #bb5551
- `on_error`: #490106
- `on_error_container`: #ff9993

### Inverse
- `inverse_on_surface`: #555557
- `inverse_primary`: #2d6483
- `inverse_surface`: #fcf8fb

### Override Colors
- Primary Override: #7FB3D5
- Secondary Override: #5C7A9E
- Tertiary Override: #B8EBD0
- Neutral Override: #1C1C1E

---

## Design Philosophy

### Creative North Star: "The Cognitive Sanctuary"
- Soft Minimalist Layering — intentional asymmetry, organic depth, "breathing" layout
- Dynamic Island metaphor — expand/contract with fluid, high-inertia motion
- Interface does not "shout" for attention; quiet, dynamic extension of macOS notch

### The "No-Line" Rule
No 1px solid borders. Boundaries defined through:
1. Tonal Shifts (surface-container-low on surface background)
2. Shadow Depth (diffused ambient occlusion)
3. Negative Space (spacing-6 and spacing-8)

### Glass & Gradient Rule
- primary-container at 80% opacity + 20px backdrop-blur
- Signature gradient: primary (#99cdf0) to primary-container (#0a4c69) at 15% opacity

### Dynamic Island States
- **Resting:** Solid black (#000000), 24px height, pill-shaped
- **Expanded:** surface-container with 2rem corner radius
- **Emotion Glows:** Outer glow using mood-specific color (#457B9D for "Focused"), 30px spread, 20% opacity

### Progress Meters (Non-Shaming)
- Horizontal bars only (no circular rings)
- Display as "% complete" or "Time invested" — never "Time remaining" in red

### Max Items Rule
- Never more than 4 items in any expanded view
- Use progressive disclosure ("See More")

### Motion
- **Entrance:** Spring physics (Stiffness: 120, Damping: 20)
- **Exit:** Ease-In (200ms)
- Elements have physical weight — lag behind cursor, snap with haptic pulse

### Typography
- Lexend throughout
- headline-lg: 2rem for focus states
- body-md: 0.875rem workhorse
- Monospaced for timers/progress percentages
- No "red dot" notification culture

### Do's
- spacing-4 (1.4rem) default inner padding
- Intentional asymmetry
- Warm Amber (#F0D3A4) for alerts instead of red

### Don'ts
- No dividers — use spacing + background shift
- No more than 4 items per expanded view
- No high-contrast white on black — use #E5E5E7 on #0e0e10
- No shaming language
