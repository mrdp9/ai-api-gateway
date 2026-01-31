# Frontend Architecture Documentation

## Overview

The AI API Gateway dashboard has been refactored with separated concerns for better maintainability, testing, and scalability.

## File Structure

```
api/
├── templates/
│   └── index.html          # Jinja2 HTML template (clean, no inline CSS/JS)
├── static/
│   ├── style.css           # CSS stylesheet (with CSS variables, responsive design)
│   └── dashboard.js        # JavaScript module (all interactive functionality)
```

## File Descriptions

### `api/templates/index.html` (119 lines)
**Purpose:** Render the API Key Management Dashboard

**Responsibilities:**
- Define HTML structure and semantic markup
- Use Jinja2 templating for dynamic data (keys list)
- Reference external CSS and JavaScript files
- Provide form inputs and tables for key management

**Key Features:**
- `{% for key in keys %}` - Loop through API keys from server
- `{{ url_for() }}` - Generate URLs for static files using Flask/FastAPI
- Responsive HTML5 structure
- Accessible form controls and semantics

**Important Notes:**
- **NO inline CSS** - All styles moved to `style.css`
- **NO inline JavaScript** - All interactivity moved to `dashboard.js`
- Uses Jinja2 variables for server-side templating
- Clean separation of concerns makes template easy to read

### `api/static/style.css` (400+ lines)
**Purpose:** Define all visual styling and responsive design

**Structure:**
```css
:root { }           /* CSS Variables (colors, shadows, etc.) */
* { }               /* Reset styles */
body { }            /* Base styling with gradient background */
.container { }      /* Main container and layout */
h1, h2 { }          /* Headers */
.form-section { }   /* Form styling */
table { }           /* Table styling */
.btn { }            /* Button styling */
.status-badge { }   /* Status indicators */
@media (max-width: 768px)  { }   /* Tablet styles */
@media (max-width: 480px)  { }   /* Mobile styles */
```

**Key Features:**
- **CSS Variables:** Centralized color management via `:root`
- **Responsive Design:** Mobile-first approach with breakpoints at 768px and 480px
- **Color System:**
  - Primary: `#667eea` (Purple-blue)
  - Secondary: `#764ba2` (Deep purple)
  - Success: `#4caf50` (Green)
  - Danger: `#d32f2f` (Red)
  - Warning: `#ffc107` (Orange)

**Selectors by Category:**
- **Layout:** `.container`, `body`, `html`
- **Typography:** `h1`, `h2`, `p`, `code`
- **Forms:** `.form-section`, `.form-group`, `input`, `label`
- **Tables:** `table`, `thead`, `tbody`, `th`, `td`
- **Components:** `.btn`, `.status-badge`, `.notification`, `.info-box`
- **Responsive:** `@media (max-width: 768px)`, `@media (max-width: 480px)`

### `api/static/dashboard.js` (300+ lines)
**Purpose:** Handle all client-side interactions and API communication

**Module Structure:**
```javascript
// Utility Functions
- showNotification(message, type, duration)
- copyToClipboard(text, message)
- formatDate(dateString)
- formatBytes(bytes)
- maskKey(key)

// Tunnel URL Management
- fetchTunnelUrl()

// API Key Management
- createApiKey()
- deleteApiKey(keyId)
- copyKeyId(keyId)

// Helpers
- getStatusBadge(status)

// Initialization
document.addEventListener('DOMContentLoaded', ...)

// Module Export (for testing)
module.exports = { ... }
```

**Key Features:**
- **Pure JavaScript** - No external dependencies (vanilla JS)
- **Async/Await** - Modern promise-based API calls
- **Error Handling** - Try-catch blocks and user notifications
- **DOM Manipulation** - Updates UI without page reload
- **Module Pattern** - Exports functions for Node.js testing

**API Endpoints Called:**
- `GET /api/tunnel-url` - Fetch the CloudFlare tunnel URL
- `POST /api/create` - Create a new API key
- `DELETE /api/delete/{key}` - Revoke an API key

**User Notifications:**
- `showNotification()` creates toast-like messages
- Color-coded by type: success (green), error (red), warning (orange), info (blue)

## FastAPI Integration

### Static Files Configuration

**In `api/main.py`:**
```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

**What this does:**
- Mounts the `api/static/` directory to serve at `/static/` route
- Enables `{{ url_for('static', path='style.css') }}` in templates
- Serves CSS and JS files with proper MIME types

### Template Setup

**In `api/main.py`:**
```python
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(require_admin)):
    conn = get_db()
    keys = conn.execute("SELECT * FROM api_keys").fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "keys": keys})
```

**How it works:**
1. Jinja2 renders `index.html` with `keys` data
2. FastAPI serves static files via `/static/` route
3. HTML references external files using `url_for()`

## Development Workflow

### Adding New Styles

1. **Add CSS class to `style.css`:**
```css
.new-component {
    background: var(--primary-color);
    padding: 1em;
    border-radius: 4px;
    /* Mobile responsive override */
}

@media (max-width: 768px) {
    .new-component {
        /* Mobile adjustments */
    }
}
```

2. **Use in HTML:**
```html
<div class="new-component">Content</div>
```

### Adding New JavaScript Functions

1. **Add function to `dashboard.js`:**
```javascript
/**
 * New function description
 * @param {string} param - Parameter description
 * @returns {Promise<any>} Return value description
 */
async function newFunction(param) {
    try {
        // Implementation
    } catch (error) {
        showNotification('Error: ' + error.message, 'error', 3000);
    }
}
```

2. **Export for testing:**
```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        newFunction,
        // ... other exports
    };
}
```

3. **Use in HTML:**
```html
<button onclick="newFunction('value')">Click me</button>
```

## Testing

### Frontend Tests
Located in `tests/test_frontend.py`

**Test Coverage:**
- ✅ File existence checks (HTML, CSS, JS)
- ✅ HTML/CSS/JS separation verification
- ✅ Jinja2 template variable presence
- ✅ CSS responsive design media queries
- ✅ JavaScript function definitions
- ✅ FastAPI static file configuration
- ✅ Directory structure validation

**Running Tests:**
```bash
cd ai-api-gateway
python tests/test_frontend.py
```

**Expected Output:**
```
Ran 20 tests in 0.005s
OK

TEST SUMMARY
Tests run: 20
Successes: 20
Failures: 0
Errors: 0
```

### Manual Testing Checklist

**Browser Testing:**
- [ ] Dashboard loads without console errors
- [ ] Tunnel URL displays when available
- [ ] Create API key form works
- [ ] New key copied to clipboard
- [ ] Revoke button works and removes key
- [ ] Status badges show correct colors
- [ ] Responsive design works on mobile (768px breakpoint)
- [ ] All buttons have hover effects

**Network Testing (DevTools):**
- [ ] CSS file loads with 200 status
- [ ] JavaScript file loads with 200 status
- [ ] `/api/tunnel-url` GET request succeeds
- [ ] `/api/create` POST request succeeds
- [ ] `/api/delete/*` DELETE request succeeds

**Functionality Testing:**
```javascript
// In browser console:
showNotification('Test message', 'success', 2000);
maskKey('abcd1234efgh5678');
formatDate('2024-12-25T10:30:00');
```

## Performance Considerations

### CSS
- **One stylesheet:** Combined into single `style.css` for efficient loading
- **CSS Variables:** Enables theme switching without reloading styles
- **Minification:** Ready for minification in production

### JavaScript
- **No external libraries:** Vanilla JS reduces bundle size
- **Async API calls:** Non-blocking operations using async/await
- **Event delegation:** Efficient DOM event handling

### Caching
```python
# In production, configure in main.py:
@app.get("/static/{file_path:path}")
async def get_static(file_path: str):
    # Add cache headers
    return FileResponse(
        path=file_path,
        headers={"Cache-Control": "public, max-age=31536000"}
    )
```

## Browser Compatibility

### Modern Browsers (2020+)
- ✅ Chrome/Edge 88+
- ✅ Firefox 85+
- ✅ Safari 14+

### Features Used
- CSS Grid & Flexbox (all modern)
- CSS Variables (all modern)
- Fetch API (all modern)
- async/await (all modern)
- ES6+ syntax (arrow functions, template literals)

### Fallbacks
- Gradient background (works in all browsers)
- Responsive design (works without JS)

## Troubleshooting

### CSS Not Loading
```
Check:
1. Static files are mounted in main.py
2. url_for('static', path='style.css') generates correct path
3. Browser cache cleared (F12 > Network > Disable cache)
4. File path matches exactly: api/static/style.css
```

### JavaScript Not Executing
```
Check:
1. dashboard.js file exists at api/static/dashboard.js
2. Script tag in index.html uses correct url_for() path
3. No JavaScript errors in browser console (F12 > Console)
4. HTTP Basic Auth is passed (dashboard requires admin login)
```

### Responsive Design Not Working
```
Check:
1. Viewport meta tag exists in HTML: <meta name="viewport" ...>
2. Browser dev tools shows correct viewport size
3. CSS media queries are correctly formatted
4. No hardcoded pixel widths overriding responsive design
```

## Future Enhancements

### Proposed Improvements
1. **Component Framework:** Consider React/Vue for complex components
2. **Build Pipeline:** Add webpack/Vite for CSS/JS minification
3. **Dark Mode:** Add CSS variable based theme switching
4. **Accessibility:** Add ARIA labels and keyboard navigation
5. **Testing:** Add Playwright for E2E browser testing
6. **Documentation:** Add JSDoc comments for all functions

### Modular CSS Architecture
```css
/* Proposed structure */
api/static/
├── css/
│   ├── variables.css      /* CSS variables & theme */
│   ├── reset.css          /* Base reset styles */
│   ├── layout.css         /* Grid, flexbox layouts */
│   ├── components.css     /* Reusable component styles */
│   ├── forms.css          /* Form-specific styles */
│   └── responsive.css     /* Media queries */
└── js/
    ├── utils/
    │   ├── api.js         /* API communication */
    │   ├── notifications.js
    │   └── formatting.js
    ├── modules/
    │   ├── keys.js        /* Key management */
    │   ├── tunnel.js      /* Tunnel URL logic */
    │   └── ui.js          /* UI interactions */
    └── app.js             /* Main app initialization */
```

## Related Files

- **Backend API:** [api/main.py](../main.py)
- **Configuration:** [.env.example](../../.env.example)
- **Docker Setup:** [api/Dockerfile](../Dockerfile)
- **Tests:** [tests/test_frontend.py](../../tests/test_frontend.py)

## Quick Links

- CSS Reference: See [style.css comments](./style.css#L1)
- JS Reference: See [dashboard.js function comments](./dashboard.js#L1)
- API Endpoints: See [main.py endpoints](../main.py#L150)
