/**
 * ui.js - Enhanced UI interactions for the online exam proctoring system
 */

document.addEventListener('DOMContentLoaded', function() {
  // Auto-hide flash messages after 5 seconds
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach(message => {
    setTimeout(() => {
      message.style.opacity = '0';
      setTimeout(() => {
        message.style.display = 'none';
      }, 500);
    }, 5000);
  });

  // Add loading state to all form submissions
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function() {
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
        
        // Store original text for restoration if needed
        submitBtn.dataset.originalText = originalText;
      }
    });
  });

  // Enhance question navigation in exam interface
  setupQuestionNavigation();
  
  // Setup collapsible sections
  setupCollapsibleSections();
  
  // Initialize tooltips
  initTooltips();
  
  // Add confirmation for important actions
  setupActionConfirmations();

  // Initialize real-time stats polling for dashboards
  initRealtimeStats();
  // Enable keyboard navigation for exam questions
  initKeyboardNavigation();
  // Initialize results page functionality
  initResultsPage();
});

/**
 * Sets up enhanced question navigation in the exam interface
 */
function setupQuestionNavigation() {
  const questionNav = document.querySelector('.question-nav');
  if (!questionNav) return;
  
  const questionItems = document.querySelectorAll('.question');
  const navContainer = document.createElement('div');
  navContainer.className = 'question-nav-container';
  
  // Create navigation buttons
  questionItems.forEach((question, index) => {
    const button = document.createElement('button');
    button.className = 'question-nav-btn';
    button.textContent = index + 1;
    button.setAttribute('data-question', index + 1);
    button.setAttribute('aria-pressed', 'false');
    
    // Check if question has been answered
    const input = question.querySelector('input[type="radio"]:checked');
    if (input) {
      button.classList.add('answered');
    }
    
    button.addEventListener('click', () => {
      // Hide all questions
      questionItems.forEach(q => q.style.display = 'none');

      // Show selected question
      question.style.display = 'block';
      try { question.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch(_) {}

      // Update active/aria state
      document.querySelectorAll('.question-nav-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
      });
      button.classList.add('active');
      button.setAttribute('aria-pressed', 'true');
    });
    
    navContainer.appendChild(button);
  });
  
  // Add navigation controls to the page
  const navControls = document.createElement('div');
  navControls.className = 'question-nav-controls';
  
  const prevBtn = document.createElement('button');
  prevBtn.className = 'btn secondary small';
  prevBtn.innerHTML = '&larr; Previous';
  prevBtn.addEventListener('click', navigateToPrevQuestion);
  
  const nextBtn = document.createElement('button');
  nextBtn.className = 'btn secondary small';
  nextBtn.innerHTML = 'Next &rarr;';
  nextBtn.addEventListener('click', navigateToNextQuestion);
  
  navControls.appendChild(prevBtn);
  navControls.appendChild(nextBtn);
  
  questionNav.appendChild(navContainer);
  questionNav.appendChild(navControls);
  
  // Show first question by default
  if (questionItems.length > 0) {
    questionItems.forEach(q => q.style.display = 'none');
    questionItems[0].style.display = 'block';
    const firstNavBtn = document.querySelector('.question-nav-btn');
    if (firstNavBtn) { firstNavBtn.classList.add('active'); firstNavBtn.setAttribute('aria-pressed','true'); }
  }
  
  // Update navigation button state when an answer is selected
  document.querySelectorAll('input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', function() {
      const questionNum = this.name.replace('q', '');
      const navBtn = document.querySelector(`.question-nav-btn[data-question="${questionNum}"]`);
      if (navBtn) navBtn.classList.add('answered');
    });
  });
}

/**
 * Navigate to the previous question
 */
function navigateToPrevQuestion() {
  const activeBtn = document.querySelector('.question-nav-btn.active');
  if (!activeBtn) return;
  
  const prevBtn = activeBtn.previousElementSibling;
  if (prevBtn) prevBtn.click();
}

/**
 * Navigate to the next question
 */
function navigateToNextQuestion() {
  const activeBtn = document.querySelector('.question-nav-btn.active');
  if (!activeBtn) return;
  
  const nextBtn = activeBtn.nextElementSibling;
  if (nextBtn) nextBtn.click();
}

/**
 * Sets up collapsible sections throughout the application
 */
function setupCollapsibleSections() {
  const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
  
  collapsibleHeaders.forEach(header => {
    header.addEventListener('click', function() {
      const content = this.nextElementSibling;
      
      if (content.style.maxHeight) {
        content.style.maxHeight = null;
        this.classList.remove('expanded');
      } else {
        content.style.maxHeight = content.scrollHeight + 'px';
        this.classList.add('expanded');
      }
    });
  });
}

/**
 * Initialize tooltips for elements with data-tooltip attribute
 */
function initTooltips() {
  const tooltipElements = document.querySelectorAll('[data-tooltip]');
  
  tooltipElements.forEach(element => {
    const tooltipText = element.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    
    element.appendChild(tooltip);
    
    element.addEventListener('mouseenter', () => {
      tooltip.style.visibility = 'visible';
      tooltip.style.opacity = '1';
    });
    
    element.addEventListener('mouseleave', () => {
      tooltip.style.visibility = 'hidden';
      tooltip.style.opacity = '0';
    });
  });
}

/**
 * Setup confirmation dialogs for important actions
 */
function setupActionConfirmations() {
  const confirmButtons = document.querySelectorAll('[data-confirm]');
  
  confirmButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      const message = this.getAttribute('data-confirm');
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
}

/**
 * Real-time stats polling for dashboards
 */
function initRealtimeStats() {
  const adminStats = document.getElementById('admin-stats');
  const studentStats = document.getElementById('student-stats');

  const setText = (el, value) => { if (el) el.textContent = value; };

  function fetchAdminStats() {
    if (!adminStats) return;
    fetch('/api/admin/stats')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        setText(document.getElementById('stat-total-exams'), data.exams ?? '-');
        setText(document.getElementById('stat-total-attempts'), data.attempts ?? '-');
        setText(document.getElementById('stat-active-attempts'), data.active_attempts ?? '-');
        const avg = data.avg_score;
        setText(document.getElementById('stat-avg-score'), avg != null ? `${avg}%` : '-');
      })
      .catch(() => {
        setText(document.getElementById('stat-total-exams'), '-');
        setText(document.getElementById('stat-total-attempts'), '-');
        setText(document.getElementById('stat-active-attempts'), '-');
        setText(document.getElementById('stat-avg-score'), '-');
      });
  }

  function fetchStudentStats() {
    if (!studentStats) return;
    fetch('/api/student/stats')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        setText(document.getElementById('student-total-exams'), data.total_exams ?? '-');
        setText(document.getElementById('student-my-attempts'), data.attempts ?? '-');
        setText(document.getElementById('student-pending'), data.pending ?? '-');
        const avg = data.avg_score;
        setText(document.getElementById('student-avg-score'), avg != null ? `${avg}%` : '-');
      })
      .catch(() => {
        setText(document.getElementById('student-total-exams'), '-');
        setText(document.getElementById('student-my-attempts'), '-');
        setText(document.getElementById('student-pending'), '-');
        setText(document.getElementById('student-avg-score'), '-');
      });
  }

  fetchAdminStats();
  fetchStudentStats();
  setInterval(() => { fetchAdminStats(); fetchStudentStats(); }, 5000);
}

/**
 * Keyboard navigation for exam questions
 */
function initKeyboardNavigation() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
      navigateToPrevQuestion();
    } else if (e.key === 'ArrowRight') {
      navigateToNextQuestion();
    }
  });
}

// Results page filtering and view toggle
function initResultsPage() {
  const searchInput = document.getElementById('search-attempts');
  const statusFilter = document.getElementById('filter-status');
  const scoreFilter = document.getElementById('filter-score');
  const cardViewBtn = document.getElementById('card-view');
  const tableViewBtn = document.getElementById('table-view');
  const attemptsCards = document.getElementById('attempts-cards');
  const attemptsTable = document.getElementById('attempts-table');

  if (!searchInput || !statusFilter || !scoreFilter) return;

  // View toggle functionality
  if (cardViewBtn && tableViewBtn && attemptsCards && attemptsTable) {
    cardViewBtn.addEventListener('click', function() {
      attemptsCards.style.display = 'grid';
      attemptsTable.style.display = 'none';
      cardViewBtn.classList.add('active');
      tableViewBtn.classList.remove('active');
    });

    tableViewBtn.addEventListener('click', function() {
      attemptsCards.style.display = 'none';
      attemptsTable.style.display = 'block';
      cardViewBtn.classList.remove('active');
      tableViewBtn.classList.add('active');
    });
  }

  // Filter functionality
  function filterAttempts() {
    const searchTerm = searchInput.value.toLowerCase();
    const statusValue = statusFilter.value;
    const scoreValue = scoreFilter.value;

    // Filter cards
    const cards = document.querySelectorAll('.attempt-card');
    cards.forEach(card => {
      const student = card.dataset.student || '';
      const exam = card.dataset.exam || '';
      const status = card.dataset.status || '';
      const score = card.dataset.score || '';

      const matchesSearch = student.includes(searchTerm) || exam.includes(searchTerm);
      const matchesStatus = !statusValue || status === statusValue;
      const matchesScore = !scoreValue || score === scoreValue;

      if (matchesSearch && matchesStatus && matchesScore) {
        card.style.display = 'block';
      } else {
        card.style.display = 'none';
      }
    });

    // Filter table rows
    const rows = document.querySelectorAll('.table-row');
    rows.forEach(row => {
      const student = row.dataset.student || '';
      const exam = row.dataset.exam || '';
      const status = row.dataset.status || '';
      const score = row.dataset.score || '';

      const matchesSearch = student.includes(searchTerm) || exam.includes(searchTerm);
      const matchesStatus = !statusValue || status === statusValue;
      const matchesScore = !scoreValue || score === scoreValue;

      if (matchesSearch && matchesStatus && matchesScore) {
        row.style.display = 'table-row';
      } else {
        row.style.display = 'none';
      }
    });
  }

  // Add event listeners
  searchInput.addEventListener('input', filterAttempts);
  statusFilter.addEventListener('change', filterAttempts);
  scoreFilter.addEventListener('change', filterAttempts);
}