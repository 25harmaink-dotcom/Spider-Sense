# Spider-Sense — Frontend Development & Integration Brief

## Objective

I want you to integrate a visually impressive, functional frontend into my existing **Spider-Sense** project folder.

I am also providing:

1. My existing backend project folder.
2. My Markdown file: **“Spider-Sense Backend — Six-Hour Build-and-Learn Plan”**.
3. A visual mockup image showing the style I want.

## Design References

**Primary reference** — I especially like the opening/hero section and the cinematic feel of this website:

- Live website: https://luc-ribeiro.github.io/spiderman-js/
- Source code: https://github.com/luc-ribeiro/spiderman-js

**Secondary reference** — I like how this Spider-Man website is presented, including its animations and overall visual experience:

- Live website: https://rhuanlucass.github.io/spider-man/
- Source code: https://github.com/RhuanLucass/spider-man

## My Project

Spider-Sense is an incident-response application. Citizens report incidents, heroes can claim and respond to them, and an optional Command role provides oversight if it exists in my backend.

## What I Want You to Do

### 1. Inspect the Existing Project First

Inspect my existing project folder, the Markdown plan, the mockup, and the reference websites/source code. Tell me what backend features actually exist and which are planned but not yet implemented.

### 2. Build a Cinematic Landing Page

Build a cinematic landing page inspired by the opening of the primary reference and the overall presentation of the secondary reference. Use my mockup as the main guide for layout and visual direction:

- Dark city atmosphere with a Spider-Man-inspired red-and-black theme.
- Large **“SPIDER-SENSE”** branding and a dramatic headline.
- A superhero-inspired visual or silhouette.
- Clear **“Report an Incident”** and **“Hero Login”** buttons.
- Smooth, tasteful entrance animations and parallax effects.
- A **“How It Works”** section: **Report → Respond → Resolve**.
- Responsive layouts for desktop and mobile.

### 3. Create Functional Application Screens

Create clean, visually appealing application screens that match the landing page but are easier to use than a cinematic presentation:

- Citizen registration and login.
- Citizen dashboard to create incidents and view only the user's reports.
- Incident form using the fields my backend actually accepts.
- Incident details, current status, and status history.
- Hero login and dashboard to see available incidents, claim an incident, and update it through the backend's allowed status transitions.
- Filters and pagination if supported by my backend.
- Command dashboard only if that role is implemented in my backend.

### 4. Integrate With the Real FastAPI Backend

Inspect the real routes, schemas, authentication, and responses before writing the API integration. Do not invent endpoints or claim features work if they do not exist. Public registration must not allow users to select Hero or Command, and the backend must remain responsible for authorization.

### 5. Handle Real Application States

Handle loading, validation, empty states, login failures, expired sessions, permission errors, and conflicts such as an incident already being claimed. Use sensible accessibility practices and respect reduced-motion settings.

### 6. Preserve the Backend

Do not replace or break my existing backend. Explain any backend changes before making them. Preserve the project's existing structure where practical. If a required endpoint is missing, tell me and distinguish between implementing it and displaying an unavailable feature.

### 7. Respect Licensing and Attribution

You may adapt the reference source code only after checking its licence and permissions. Otherwise, create an original design inspired by the references. Do not assume copyrighted images or characters are free to reuse. Include a **“fan-made student project; not affiliated with Marvel”** notice.

### 8. Run Frontend and Backend Together Locally

Make the frontend and backend run together locally. Configure any necessary development proxy or CORS settings based on the actual setup. Give me exact macOS terminal commands for installation and running both services, along with the local URL to open.

### 9. Test Actual Flows

Test the real flows supported by the backend. Report what you actually tested, the results, and anything you could not verify. Do not use fake dashboard data while presenting it as real backend data.

## Important Working Style

I am a beginner and need to understand my project for an interview. Start by inspecting the files and explaining your proposed approach. Then work in manageable steps, explain important changes in plain language, and help me run the project. Do not silently rewrite the entire backend.

---

# Extra Spider-Man Experience

Make the website feel like a Spider-Man-inspired command center, not just a generic dashboard with red colours. Use the attached mockup and reference websites as visual inspiration.

## 1. Spider-Sense Activation

- On entering the website, show a brief cinematic **“SPIDER-SENSE ACTIVATED”** animation with a subtle pulse, web lines, and a city-themed background.
- Let users skip it, and avoid replaying it on every page or dashboard action.
- Provide a reduced-motion alternative.

## 2. Cinematic Landing Page

- Use a dark city skyline, Spider-Man-inspired silhouette, red and blue lighting, web patterns, and subtle parallax.
- Add a short loading or entrance animation resembling a web being drawn.
- Keep the main buttons visible and easy to use.

## 3. Spidey-Style Interactions

- Add subtle web effects on button hover and smooth card transitions.
- Use a pulse or ripple effect for important alerts.
- Give the Hero dashboard a **“patrol console”** feel.
- Use thematic labels where they remain clear, such as **“Patrol Dashboard”** and **“Incident Alert”**. Keep functional labels understandable.

## 4. Incident Experience

- Show incident status with a web-inspired progress timeline.
- Highlight severity with both text/icons and colour.
- When an incident is successfully claimed, show a brief confirmation such as **“MISSION ACCEPTED”**—only after the backend confirms the claim.
- When an incident is resolved, show a subtle success animation.

## 5. Optional Personality

- Add a small Spider-Sense status indicator or friendly assistant-style message, but do not make it look like a real AI assistant unless that functionality has actually been implemented.
- Optional sound effects must be off by default and user-controlled.

## Important Constraints

- Make all effects responsive, accessible, and smooth without slowing down important actions.
- Do not let animations block forms, navigation, or emergency-related actions.
- Respect reduced-motion preferences; avoid flashing and intense effects.
- Every claim, status, alert, and incident must reflect the real backend response. Do not present decorative effects or demo data as real features.
- Use properly licensed assets or original artwork. Clearly label the site as a fan-made student project, not an official Marvel product.
