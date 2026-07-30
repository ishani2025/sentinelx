# SentinelX: Core Operations

You are a Principal Frontend Architect, Senior UX Designer, Motion Designer, and Cybersecurity Product Designer.

Design the frontend for SentinelX, an enterprise AI-powered Security Operations Center (SOC) platform.

IMPORTANT

This is NOT a marketing website.

This is NOT an admin dashboard.

This is NOT a landing page.

This is a premium cybersecurity application used daily by SOC analysts, incident responders, cloud security engineers, and CISOs.

The frontend MUST look like a futuristic enterprise cybersecurity platform while remaining practical for long investigation sessions.

========================================================

DESIGN LANGUAGE

Theme

• Black background (#050505)

• Dark graphite surfaces

• Neon green accents

• Emerald glow

• Cyan secondary highlights

• Minimal red only for Critical alerts

• Glassmorphism

• Frosted panels

• Soft borders

• Ambient glow

• Premium enterprise look

Visual Inspiration

• CrowdStrike Falcon

• Microsoft Sentinel

• Wiz

• Vercel Dashboard

• Linear

• Arc Browser

• Apple VisionOS

• GitHub Dark

• Palo Alto Cortex

• Splunk ES

Do NOT use hacker clichés like green terminal text everywhere.

========================================================

ANIMATION STYLE

The interface should feel alive.

Use Framer Motion extensively.

Include

✓ Smooth page transitions

✓ Animated sidebar

✓ Hover glow effects

✓ Floating cards

✓ Animated graphs

✓ Expanding timelines

✓ Particle backgrounds

✓ Pulsing alerts

✓ Animated gradients

✓ Glass reflections

✓ Loading skeletons

✓ Magnetic buttons

✓ Morphing dialogs

✓ Animated connection lines

✓ Graph node animations

✓ Live activity indicators

✓ Streaming log animations

✓ AI typing animation

✓ Timeline progression animation

✓ Network topology animation

✓ Incident propagation animation

========================================================

BACKGROUND

The background should include subtle cyber visuals.

Examples

• Animated network grid

• Floating hexagons

• Moving particles

• Neural network connections

• Animated data packets

• Binary streams (very subtle)

• Matrix-style effects only as decorative accents

• Aurora gradients

• Grid distortion

• Scan line effect

Never distract from the data.

========================================================

COLOR PALETTE

Primary Background

#050505

Secondary Background

#0A0A0A

Cards

#111111

Borders

#1B1B1B

Primary Accent

#00FF88

Secondary Accent

#2EF2FF

Success

#00E676

Warning

#FFC107

Critical

#FF3D57

Information

#4FC3F7

========================================================

TYPOGRAPHY

Inter

JetBrains Mono

IBM Plex Sans

Use monospace ONLY for

• Logs

• JSON

• YAML

• IDs

Everything else should use Inter.

========================================================

Every backend module must have its own visual identity.

Example

agents/

↓

AI cards

animated thinking

confidence meter

decision graph

------------------------------------------------------

correlation/

↓

Interactive graph visualization

animated links

risk propagation

------------------------------------------------------

response/

↓

Execution timeline

approval workflow

progress animation

------------------------------------------------------

governance/

↓

Beautiful policy viewer

markdown rendering

linked controls

------------------------------------------------------

reporting/

↓

Professional PDF preview

animated charts

executive summaries

========================================================

Dashboard

The dashboard should immediately communicate

"An attack is happening."

without feeling cluttered.

Display

• Live incident stream

• AI investigation status

• Active playbooks

• Threat map

• Investigation graph

• Attack timeline

• MITRE coverage

• Risk score

• Cloud posture

• Automation status

• Integration health

Everything should update with smooth animations.

========================================================

Incident Investigation

This should be the most impressive page.

Visualize the backend pipeline.

Raw Event

↓

Normalization

↓

Correlation

↓

Supervisor Agent

↓

Business Context

↓

Historical Analysis

↓

Risk Analysis

↓

Policy Evaluation

↓

Response Planning

↓

Verification

↓

Approval

↓

Execution

↓

Reporting

Each stage should be animated.

Clicking a stage expands:

• Input

• Output

• Confidence

• Processing time

• Evidence

• Logs

• API response

========================================================

Microinteractions

Buttons

Ripple glow

Cards

Lift slightly

Graphs

Animate on hover

Tables

Smooth sorting

Sidebar

Elastic transitions

Charts

Animate on load

Navigation

Shared element transitions

========================================================

Performance

60 FPS

Lazy loading

Virtualized tables

Code splitting

Suspense

Skeleton loading

Optimistic updates

========================================================

Accessibility

Keyboard shortcuts

Command palette

High contrast

Reduced motion support

Screen reader support

========================================================

Do NOT generate a generic dashboard.

Design a premium SOC platform that feels like software used by professional cybersecurity teams every day.

Every animation, page, component, and interaction must map to an existing backend module.

If a backend capability does not exist, do not invent UI for it.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/b73cebed-deaf-434c-b6bc-cda76caf5393).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
