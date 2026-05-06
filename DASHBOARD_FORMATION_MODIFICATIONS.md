# Dashboard.html Formation Integration — Modification Spec

## Overview
Wire the existing FY chat modal to handle Questions 1-3 of the formation process.
Formation meter in left panel tracks progress (0% → 33% → 66% → 100%).
FY's opening message IS formation beginning.

---

## Changes Required

### 1. Formation State (Add to useState block)
```javascript
const [formationProgress, setFormationProgress] = useState(0); // 0-3 (tracks Q1-Q3)
const [formationQ1, setFormationQ1] = useState(null);
const [formationQ2, setFormationQ2] = useState(null);
const [formationQ3, setFormationQ3] = useState(null);
const [isFormationActive, setIsFormationActive] = useState(true); // True until Q3 answered
```

### 2. The 3 Formation Questions (Q1-Q3)
```javascript
const FORMATION_QUESTIONS = [
  {
    id: 'q1',
    prompt: 'You're building something. What's the creative core?',
    key: 'formationQ1'
  },
  {
    id: 'q2',
    prompt: 'What's the biggest shift you want to make in the next year?',
    key: 'formationQ2'
  },
  {
    id: 'q3',
    prompt: 'What would make you actually USE StudioYou instead of just thinking about it?',
    key: 'formationQ3'
  }
];
```

### 3. Left Panel Formation Meter (Modify fy-panel section)
```javascript
<div className="fy-panel">
  <div className="fy-panel-hd">
    <span className="fy-icon">📋</span>
    <span className="fy-panel-name">Formation</span>
  </div>
  <div style={{ padding: '12px 0' }}>
    <div style={{
      height: '4px',
      background: 'rgba(0,200,255,0.1)',
      borderRadius: '2px',
      overflow: 'hidden',
      marginBottom: '8px'
    }}>
      <div style={{
        height: '100%',
        background: 'linear-gradient(90deg, #6495ff, #b366ff)',
        width: `${(formationProgress / 3) * 100}%`,
        transition: 'width 0.3s ease'
      }} />
    </div>
    <div style={{
      fontSize: '11px',
      color: '#888',
      textAlign: 'center'
    }}>
      {formationProgress} of 3 questions
    </div>
  </div>
</div>
```

### 4. Chat Logic Modification (sendText function)
When user sends a message during formation phase:
```javascript
async function sendText(txt) {
  if (!txt || loading) return;
  
  // Store formation response if in formation phase
  if (isFormationActive) {
    if (formationProgress === 0) {
      setFormationQ1(txt);
      setFormationProgress(1);
    } else if (formationProgress === 1) {
      setFormationQ2(txt);
      setFormationProgress(2);
    } else if (formationProgress === 2) {
      setFormationQ3(txt);
      setFormationProgress(3);
      setIsFormationActive(false);
      // Formation complete — save to localStorage
      localStorage.setItem('sy_formation_phase2', JSON.stringify({
        q1: txt,
        q2: formationQ2,
        q3: formationQ3,
        completedAt: new Date().toISOString()
      }));
    }
  }

  setInput('');
  setMsgs(prev=>[...prev,{role:'user',text:txt}]);
  setLoading(true);
  startProcessing('FutureYou is thinking...');
  
  try {
    const history = msgs.map(m=>({
      role: m.role==='fy'?'assistant':'user',
      content: m.text
    }));
    
    const res = await fetch(`${API_URL}/api/chat`, {
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':`Bearer ${sessionToken}`},
      body: JSON.stringify({
        model:'claude-sonnet-4-6',
        max_tokens:600,
        system: `[existing system prompt with formation context]`,
        messages: history
      })
    });
    
    const data = await res.json();
    const fyText = data.content?.[0]?.text || 'Got it. What else?';
    setMsgs(prev=>[...prev,{role:'fy',text:fyText}]);
    
    // If formation just completed, show next prompt
    if (formationProgress === 3 && isFormationActive === false) {
      setTimeout(() => {
        setMsgs(prev=>[...prev,{role:'fy',text: 'Formation complete. Let's get to work.'}]);
      }, 500);
    } else if (formationProgress < 3) {
      // Show next formation question
      const nextQ = FORMATION_QUESTIONS[formationProgress];
      setTimeout(() => {
        setMsgs(prev=>[...prev,{role:'fy',text: nextQ.prompt}]);
      }, 500);
    }
  } catch(err) {
    console.error('Chat error:', err);
    setMsgs(prev=>[...prev,{role:'fy',text: 'Something went wrong. Try again.'}]);
  } finally {
    setLoading(false);
  }
}
```

### 5. Initial FY Message (In generateOpener)
FutureYou's opening message is already context-aware. Keep it as is — it IS formation beginning.

After opener displays, **automatically show Q1**:
```javascript
setMsgs(prev=>[
  ...prev,
  {role:'fy', text: FORMATION_QUESTIONS[0].prompt}
]);
```

### 6. "3 Questions Ready" Box (Modify or Remove)
**Option A:** Transform it into formation progress display
```javascript
<div className="fy-p">
  <div className="fy-p-t">Formation Questions</div>
  <div style={{ fontSize: '11px', color: '#888', marginTop: '6px' }}>
    {formationProgress === 3 ? '✓ Complete' : `${formationProgress}/3 answered`}
  </div>
</div>
```

**Option B:** Keep as-is (users see it as reference that 3 questions remain)

---

## Flow Logic

```
Dashboard loads
  ↓
generateOpener() calls Claude (FY's first words, formation-aware)
  ↓
msgs shows: [FY opening message]
  ↓
Auto-show Q1: "You're building something. What's the creative core?"
  ↓
User types answer → stored in formationQ1 → meter: 0/3 → 1/3
  ↓
Auto-show Q2: "What's the biggest shift you want in the next year?"
  ↓
User types answer → stored in formationQ2 → meter: 1/3 → 2/3
  ↓
Auto-show Q3: "What would make you USE StudioYou instead of thinking about it?"
  ↓
User types answer → stored in formationQ3 → meter: 2/3 → 3/3 → COMPLETE
  ↓
Formation complete message
  ↓
User can now freely chat with FY
```

---

## localStorage Schema
```javascript
sy_lobby_responses // Array of 6 responses from lobby flow
sy_formation_phase2 // Object with q1, q2, q3 answers (dashboard formation)
sy_formation // Combined formation (if exists from previous flow)
```

---

## No Breaking Changes
- Existing FY chat modal unchanged
- Existing sendText() logic extended (not replaced)
- Existing left panel structure reused
- New state just adds to component

**This is wiring existing pieces together, not rebuilding.**

