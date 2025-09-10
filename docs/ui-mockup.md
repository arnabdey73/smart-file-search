# Smart File Search - UI Mockup Design

## 🎨 Visual Layout Design

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                            🔍 Smart File Search                                        ║
║                    Search across Windows network folders with AI                       ║
║                        Web-hosted application • No installation required               ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                       ║
║  ┌─── Setup Panel ──────────────────────────────────────────────────────────────┐     ║
║  │ 📁 Add Network Folders                                              [+ Add]  │     ║
║  │ \\network\shared\documents                                         [✓ Indexed] │     ║
║  │ \\server\projects\2024                                             [⏳ Indexing]│     ║
║  │ C:\Users\Shared\Reports                                            [✓ Indexed] │     ║
║  └───────────────────────────────────────────────────────────────────────────────┘     ║
║                                                                                       ║
║  ┌─── Search Interface ───────────────────────────────────────────────────────────┐     ║
║  │                                                                               │     ║
║  │  🔍 [Search for documents, content, or ask a question...        ] [Search]  │     ║
║  │                                                                               │     ║
║  │  Filters:  [ ] PDF  [ ] Word  [✓] Excel  [ ] PowerPoint  [✓] Text           │     ║
║  │           Max Results: [50 ▼]    [✓] Enable AI Enhancement                  │     ║
║  │                                                                               │     ║
║  └───────────────────────────────────────────────────────────────────────────────┘     ║
║                                                                                       ║
║  ┌─── Token Usage Dashboard ──────────────────────────────────────────────────────┐     ║
║  │ 💰 Today's Usage: ████████░░ 1,247 / 5,000 tokens (24.9%)                   │     ║
║  │ 💵 Cost: $0.19 USD  |  🔋 Remaining: 3,753 tokens                           │     ║
║  │ [📊 View Details]                                     [⚙️ Adjust Limits]       │     ║
║  └───────────────────────────────────────────────────────────────────────────────┘     ║
║                                                                                       ║
║  ┌─── Search Results ─────────────────────────────────────────────────────────────┐     ║
║  │ 📊 Found 47 files in 234ms (Standard FTS5 + AI Enhancement)                 │     ║
║  │                                                                               │     ║
║  │ 📄 Budget_Report_Q3_2024.xlsx                                     Score: 98% │     ║
║  │    \\server\finance\reports\Budget_Report_Q3_2024.xlsx                        │     ║
║  │    "quarterly budget analysis for departments... revenue projections..."      │     ║
║  │    📅 Modified: 2024-09-08  📏 Size: 2.3 MB                [📖 Open] [📋 Copy] │     ║
║  │                                                                               │     ║
║  │ 📄 Financial_Summary_September.pdf                               Score: 94%  │     ║
║  │    \\network\shared\documents\Financial_Summary_September.pdf                  │     ║
║  │    "executive summary of financial performance... budget variance..."         │     ║
║  │    📅 Modified: 2024-09-05  📏 Size: 1.8 MB                [📖 Open] [📋 Copy] │     ║
║  │                                                                               │     ║
║  │ 📄 Project_Budget_Template.docx                                  Score: 89%  │     ║
║  │    \\server\projects\templates\Project_Budget_Template.docx                   │     ║
║  │    "standardized template for project budget planning..."                     │     ║
║  │    📅 Modified: 2024-08-28  📏 Size: 456 KB             [📖 Open] [📋 Copy]  │     ║
║  │                                                                               │     ║
║  │ [Load More Results...]                                                        │     ║
║  └───────────────────────────────────────────────────────────────────────────────┘     ║
║                                                                                       ║
║  ┌─── AI Insights Panel ──────────────────────────────────────────────────────────┐     ║
║  │ 🤖 AI Summary (Tokens used: 89)                                              │     ║
║  │ Found 47 budget-related documents across 3 network locations. Most files     │     ║
║  │ contain Q3 2024 financial data including revenue projections, department      │     ║
║  │ budgets, and variance reports. Key themes: quarterly analysis, project       │     ║
║  │ planning, financial summaries.                                                │     ║
║  │                                                                               │     ║
║  │ 💡 Related Searches:                                                          │     ║
║  │ • "Q4 budget projections"     • "department budget allocation"               │     ║
║  │ • "financial variance reports"  • "revenue forecasting 2024"                 │     ║
║  └───────────────────────────────────────────────────────────────────────────────┘     ║
║                                                                                       ║
║  ┌─── Status Bar ────────────────────────────────────────────────────────────────┐     ║
║  │ 🟢 Connected to API  |  📂 3 folders indexed (47,392 files)  |  🔄 Last sync: 2m ago │     ║
║  └───────────────────────────────────────────────────────────────────────────────┘     ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

## 🎯 Key UI Components

### 1. **Header Section**
- **Gradient background**: Purple to blue gradient (#667eea → #764ba2)
- **Title**: "🔍 Smart File Search" with shadow effects
- **Subtitle**: Clear description and deployment status
- **Responsive design**: Adapts to mobile/tablet/desktop

### 2. **Network Folders Panel**
- **Visual indicators**: ✓ Indexed, ⏳ Indexing, ❌ Error
- **Path display**: Full network paths with status
- **Add button**: Easy folder addition with browse dialog
- **Progress bars**: For indexing operations

### 3. **Search Interface**
- **Large search input**: Prominent, auto-focus on load
- **Filter toggles**: Visual checkboxes for file types
- **AI toggle**: Clear indication when AI is enabled
- **Search button**: Disabled state when no query

### 4. **Token Usage Dashboard** ⭐ NEW FEATURE
- **Progress bar**: Visual representation of daily usage
- **Real-time metrics**: Tokens used, cost, remaining
- **Color coding**: Green → Yellow → Red as limit approached
- **Admin controls**: Adjust limits (if authorized)

### 5. **Search Results**
- **Performance metrics**: Search time, method used, count
- **File cards**: Clean layout with icons, paths, snippets
- **Relevance scores**: Visual percentage indicators
- **Action buttons**: Open file, copy path, share
- **Pagination**: Load more results on demand

### 6. **AI Insights Panel** 🤖
- **Token usage indicator**: Shows cost for transparency
- **Smart summary**: Contextual overview of results
- **Related suggestions**: Clickable query recommendations
- **Expandable**: Can be collapsed to save space

### 7. **Status Bar**
- **Connection status**: Real-time API connectivity
- **Index statistics**: Files indexed, last sync time
- **System health**: Performance indicators

## 🎨 Color Scheme & Styling

### Primary Colors
- **Header Gradient**: #667eea → #764ba2
- **Background**: #f5f7fa (light gray)
- **Text**: #2c3e50 (dark blue-gray)
- **Accent**: #3498db (blue)
- **Success**: #27ae60 (green)
- **Warning**: #f39c12 (orange)
- **Error**: #e74c3c (red)

### Typography
- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI'
- **Headers**: 2.5rem, 700 weight, text-shadow
- **Body**: 1rem, 400 weight, 1.6 line-height
- **Code**: 'Courier New', Monaco, Consolas

### Interactive Elements
- **Buttons**: Rounded corners, hover effects, disabled states
- **Cards**: Subtle shadows, border radius, hover lift
- **Inputs**: Focus rings, validation states
- **Toggles**: Smooth animations, clear on/off states

## 📱 Responsive Behavior

### Desktop (1200px+)
- **3-column layout**: Folders | Search+Results | AI Insights
- **Full feature visibility**: All panels expanded
- **Large search input**: Prominent, easy to use

### Tablet (768px - 1199px)
- **2-column layout**: Main content | Collapsible sidebar
- **Stacked panels**: Folders above search interface
- **Touch-friendly**: Larger buttons and touch targets

### Mobile (< 768px)
- **Single column**: Stacked vertically
- **Collapsible sections**: Expandable panels
- **Thumb navigation**: Bottom-aligned actions
- **Simplified AI**: Essential features only

## 🚀 Interactive Features

### Real-time Updates
- **Live search**: Results update as you type (debounced)
- **Token meter**: Updates with each AI request
- **Status indicators**: Connection, indexing progress

### Smart Interactions
- **Auto-complete**: Query suggestions based on indexed content
- **Quick filters**: One-click common search types
- **Keyboard shortcuts**: Ctrl+K for search focus, Escape to clear

### Accessibility
- **ARIA labels**: Screen reader compatibility
- **Keyboard navigation**: Full keyboard support
- **High contrast**: Option for accessibility
- **Focus indicators**: Clear visual focus rings

## 💡 Advanced Features

### Context Menus
- **Right-click file results**: Open, copy, share options
- **Bulk operations**: Select multiple files
- **Export results**: Save search results to CSV/JSON

### Customization
- **Theme toggle**: Light/dark mode
- **Layout preferences**: Panel sizes, positions
- **Search defaults**: Preferred file types, result counts

### Performance Indicators
- **Search method badges**: "FTS5", "AI Enhanced", "Cached"
- **Response time**: Millisecond precision
- **Index health**: File count, last update, errors

This mockup represents a professional, user-friendly interface that balances powerful search capabilities with cost-conscious AI usage, making it perfect for enterprise deployment! 🎯✨
