/**
 * Personal Expense Tracker — Frontend Application Logic
 *
 * Pure Vanilla JavaScript (no jQuery). Uses async/await with fetch()
 * for all API calls. Handles CRUD operations, chart rendering,
 * filtering, sorting, toasts, and all DOM manipulation.
 */

/* ============================================================
   CONSTANTS & STATE
   ============================================================ */

/** Base URL for API endpoints */
const API_BASE = '/api/expenses';

/** Category badge color mapping */
const CATEGORY_COLORS = {
    Food:          { bg: '#198754', label: 'bg-success' },
    Transport:     { bg: '#0d6efd', label: 'bg-primary' },
    Health:        { bg: '#dc3545', label: 'bg-danger' },
    Entertainment: { bg: '#6f42c1', label: 'bg-purple' },
    Shopping:      { bg: '#fd7e14', label: 'bg-warning' },
    Utilities:     { bg: '#0dcaf0', label: 'bg-info' },
    Other:         { bg: '#6c757d', label: 'bg-secondary' },
};

/** Chart.js chart instances (mutable for destroy/recreate) */
let categoryChart = null;
let trendChart = null;

/** Current sort state */
let currentSort = { column: 'date', direction: 'desc' };

/** ID of the expense pending deletion */
let pendingDeleteId = null;

/* ============================================================
   UTILITY FUNCTIONS
   ============================================================ */

/**
 * Create a debounced version of a function.
 * @param {Function} fn - The function to debounce.
 * @param {number} delay - Debounce delay in milliseconds.
 * @returns {Function} Debounced function.
 */
const debounce = (fn, delay) => {
    let timer = null;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
};

/**
 * Format a number as USD currency string.
 * @param {number} value - The numeric value.
 * @returns {string} Formatted string like "1,234.56".
 */
const formatCurrency = (value) => {
    return parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
};

/**
 * Get today's date in YYYY-MM-DD format.
 * @returns {string} Today's date string.
 */
const todayStr = () => {
    const d = new Date();
    return d.toISOString().split('T')[0];
};

/**
 * Get a CSS class for a category badge.
 * @param {string} category - The category name.
 * @returns {string} Bootstrap badge class.
 */
const categoryBadgeClass = (category) => {
    const mapping = {
        Food: 'bg-success',
        Transport: 'bg-primary',
        Health: 'bg-danger',
        Entertainment: 'bg-purple',
        Shopping: 'bg-orange',
        Utilities: 'bg-info',
        Other: 'bg-secondary',
    };
    return mapping[category] || 'bg-secondary';
};

/* ============================================================
   TOAST NOTIFICATIONS
   ============================================================ */

/**
 * Display a Bootstrap toast notification.
 * @param {string} message - Text to display.
 * @param {string} type - One of 'success', 'info', 'danger', 'warning'.
 */
const showToast = (message, type = 'success') => {
    const container = document.getElementById('toastContainer');
    const colorMap = {
        success: 'bg-success',
        info:    'bg-primary',
        danger:  'bg-danger',
        warning: 'bg-warning text-dark',
    };
    const bgClass = colorMap[type] || 'bg-success';

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white ${bgClass} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-semibold">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    container.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    /* Remove from DOM after hidden */
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
};

/* ============================================================
   API FUNCTIONS
   ============================================================ */

/**
 * Fetch all expenses with optional query parameters.
 * @param {Object} params - Query parameter object.
 * @returns {Promise<Array>} Array of expense objects.
 */
const fetchExpenses = async (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
        if (val !== null && val !== undefined && val !== '') {
            query.append(key, val);
        }
    });
    const url = `${API_BASE}/?${query.toString()}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch expenses');
    return response.json();
};

/**
 * Fetch a single expense by ID.
 * @param {number} id - Expense ID.
 * @returns {Promise<Object>} Expense object.
 */
const fetchExpenseById = async (id) => {
    const response = await fetch(`${API_BASE}/${id}`);
    if (!response.ok) throw new Error('Expense not found');
    return response.json();
};

/**
 * Fetch aggregated stats for the dashboard.
 * @returns {Promise<Object>} Stats object.
 */
const fetchStats = async () => {
    const response = await fetch(`${API_BASE}/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
};

/**
 * Create a new expense via POST.
 * @param {Object} data - Expense data matching ExpenseCreate schema.
 * @returns {Promise<Object>} Created expense object.
 */
const createExpense = async (data) => {
    const response = await fetch(`${API_BASE}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || JSON.stringify(err));
    }
    return response.json();
};

/**
 * Update an existing expense via PUT.
 * @param {number} id - Expense ID.
 * @param {Object} data - Fields to update.
 * @returns {Promise<Object>} Updated expense object.
 */
const updateExpense = async (id, data) => {
    const response = await fetch(`${API_BASE}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || JSON.stringify(err));
    }
    return response.json();
};

/**
 * Delete an expense via DELETE.
 * @param {number} id - Expense ID.
 * @returns {Promise<void>}
 */
const deleteExpense = async (id) => {
    const response = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to delete');
    }
};

/* ============================================================
   ANIMATED COUNT-UP
   ============================================================ */

/**
 * Animate a number counting up from 0 to target.
 * @param {HTMLElement} el - The element whose text to animate.
 * @param {number} target - Target number.
 * @param {boolean} isInteger - If true, render without decimals.
 */
const animateCountUp = (el, target, isInteger = false) => {
    const duration = 1000;
    const startTime = performance.now();
    const start = 0;

    const step = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        /* Ease-out cubic */
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + (target - start) * eased;

        el.textContent = isInteger
            ? Math.floor(current).toLocaleString()
            : formatCurrency(current);

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    };
    requestAnimationFrame(step);
};

/* ============================================================
   DASHBOARD STATS & CHARTS
   ============================================================ */

/**
 * Fetch stats and update all dashboard elements.
 */
const updateStats = async () => {
    try {
        const stats = await fetchStats();

        /* Animated count-ups */
        animateCountUp(document.getElementById('statTotalSpent'), stats.total_all_time);
        animateCountUp(document.getElementById('statThisMonth'), stats.total_this_month);
        animateCountUp(document.getElementById('statTransactions'), stats.transaction_count, true);

        /* Highest expense (static) */
        const highestEl = document.getElementById('statHighest');
        const highestBadge = document.getElementById('statHighestBadge');
        if (stats.highest_expense) {
            highestEl.textContent = formatCurrency(stats.highest_expense.amount);
            highestBadge.textContent = stats.highest_expense.category;
            highestBadge.className = `badge ${categoryBadgeClass(stats.highest_expense.category)} mt-1`;
            highestBadge.classList.remove('d-none');
        } else {
            highestEl.textContent = '0.00';
            highestBadge.classList.add('d-none');
        }

        /* Render charts */
        renderCharts(stats);
    } catch (err) {
        console.error('Error updating stats:', err);
    }
};

/**
 * Render (or re-render) the category doughnut and trend line charts.
 * @param {Object} stats - Stats object from the API.
 */
const renderCharts = (stats) => {
    renderCategoryChart(stats.by_category);
    renderTrendChart(stats.monthly_trend);
};

/**
 * Render the category doughnut chart.
 * @param {Object} byCategory - { category: totalAmount } mapping.
 */
const renderCategoryChart = (byCategory) => {
    const canvas = document.getElementById('categoryChart');
    const emptyMsg = document.getElementById('categoryChartEmpty');
    const categories = Object.keys(byCategory);
    const amounts = Object.values(byCategory);

    if (categories.length === 0) {
        canvas.style.display = 'none';
        emptyMsg.classList.remove('d-none');
        if (categoryChart) { categoryChart.destroy(); categoryChart = null; }
        return;
    }

    canvas.style.display = 'block';
    emptyMsg.classList.add('d-none');

    const colors = categories.map(c => CATEGORY_COLORS[c]?.bg || '#6c757d');

    if (categoryChart) categoryChart.destroy();

    categoryChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff',
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: { animateRotate: true, animateScale: true },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, usePointStyle: true },
                    onClick: Chart.defaults.plugins.legend.onClick,
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.label}: $${formatCurrency(ctx.parsed)}`,
                    },
                },
            },
        },
    });
};

/**
 * Render the monthly trend line chart.
 * @param {Array} monthlyTrend - Array of { month, total } objects.
 */
const renderTrendChart = (monthlyTrend) => {
    const canvas = document.getElementById('trendChart');
    const labels = monthlyTrend.map(m => m.month);
    const data = monthlyTrend.map(m => m.total);

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Monthly Spending',
                data,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13,110,253,0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#0d6efd',
                pointRadius: 5,
                pointHoverRadius: 7,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: { duration: 1000 },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (val) => `$${val}`,
                    },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `$${formatCurrency(ctx.parsed.y)}`,
                    },
                },
            },
        },
    });
};

/* ============================================================
   TABLE RENDERING
   ============================================================ */

/**
 * Build an HTML table row string for an expense.
 * @param {Object} expense - Expense object.
 * @returns {string} HTML <tr> string.
 */
const buildRow = (expense) => {
    const badgeClass = categoryBadgeClass(expense.category);
    return `
        <tr id="expense-row-${expense.id}" class="expense-row">
            <td>${expense.date}</td>
            <td>${escapeHtml(expense.description)}</td>
            <td><span class="badge ${badgeClass}">${expense.category}</span></td>
            <td class="text-end fw-semibold">$${formatCurrency(expense.amount)}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary me-1 btn-edit"
                        data-id="${expense.id}" title="Edit">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-delete"
                        data-id="${expense.id}" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `;
};

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} text - Raw text.
 * @returns {string} Escaped text.
 */
const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

/**
 * Render the full expenses table from the API.
 */
const renderTable = async () => {
    try {
        const params = getFilterParams();
        params.sort_by = currentSort.column;
        params.sort_dir = currentSort.direction;
        const expenses = await fetchExpenses(params);

        const tbody = document.getElementById('expensesBody');
        const emptyState = document.getElementById('emptyState');
        const resultsCount = document.getElementById('resultsCount');

        if (expenses.length === 0) {
            tbody.innerHTML = '';
            /* Show empty state only if no filters are active */
            const hasFilters = params.category || params.start_date || params.end_date || params.keyword;
            if (hasFilters) {
                emptyState.classList.add('d-none');
                resultsCount.textContent = '0 results';
                resultsCount.classList.remove('d-none');
            } else {
                emptyState.classList.remove('d-none');
                resultsCount.classList.add('d-none');
            }
        } else {
            emptyState.classList.add('d-none');
            tbody.innerHTML = expenses.map(buildRow).join('');
            /* Show results count when filters active */
            const hasFilters = params.category || params.start_date || params.end_date || params.keyword;
            if (hasFilters) {
                resultsCount.textContent = `${expenses.length} result${expenses.length !== 1 ? 's' : ''}`;
                resultsCount.classList.remove('d-none');
            } else {
                resultsCount.classList.add('d-none');
            }
        }

        /* Attach row action listeners */
        attachRowListeners();
    } catch (err) {
        console.error('Error rendering table:', err);
    }
};

/**
 * Render the recent expenses mini-table (top 5).
 */
const renderRecentExpenses = async () => {
    try {
        const expenses = await fetchExpenses({ sort_by: 'date', sort_dir: 'desc' });
        const recent = expenses.slice(0, 5);
        const tbody = document.getElementById('recentExpensesBody');

        if (recent.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">No recent expenses</td></tr>`;
            return;
        }

        tbody.innerHTML = recent.map(e => `
            <tr>
                <td>${e.date}</td>
                <td>${escapeHtml(e.description)}</td>
                <td><span class="badge ${categoryBadgeClass(e.category)}">${e.category}</span></td>
                <td class="text-end fw-semibold">$${formatCurrency(e.amount)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error rendering recent expenses:', err);
    }
};

/* ============================================================
   FILTER / SEARCH
   ============================================================ */

/**
 * Collect current filter values from the filter bar.
 * @returns {Object} Filter params object.
 */
const getFilterParams = () => {
    return {
        category: document.getElementById('filterCategory').value || null,
        start_date: document.getElementById('filterStartDate').value || null,
        end_date: document.getElementById('filterEndDate').value || null,
        keyword: document.getElementById('filterKeyword').value || null,
    };
};

/**
 * Handle filter change (called on every input change).
 */
const onFilterChange = () => {
    renderTable();
};

/**
 * Clear all filter inputs and re-render.
 */
const clearFilters = () => {
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    document.getElementById('filterKeyword').value = '';
    document.getElementById('resultsCount').classList.add('d-none');
    renderTable();
};

/* ============================================================
   SORTING
   ============================================================ */

/**
 * Handle sort header click.
 * @param {string} column - The column name to sort by.
 */
const handleSort = (column) => {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    updateSortIcons();
    renderTable();
};

/**
 * Update sort arrow icons in table headers.
 */
const updateSortIcons = () => {
    document.querySelectorAll('#expensesTable .sortable').forEach(th => {
        const icon = th.querySelector('.sort-icon');
        const col = th.dataset.sort;
        if (col === currentSort.column) {
            icon.className = currentSort.direction === 'asc'
                ? 'bi bi-arrow-up sort-icon text-primary'
                : 'bi bi-arrow-down sort-icon text-primary';
        } else {
            icon.className = 'bi bi-arrow-down-up sort-icon text-muted';
        }
    });
};

/* ============================================================
   MODAL LOGIC
   ============================================================ */

/**
 * Open the add expense modal with empty fields.
 */
const openAddModal = () => {
    document.getElementById('expenseId').value = '';
    document.getElementById('expenseModalLabel').innerHTML =
        '<i class="bi bi-plus-circle me-2"></i>Add Expense';
    document.getElementById('expenseForm').reset();
    document.getElementById('expenseDate').value = todayStr();
    document.getElementById('charCount').textContent = '0';
    document.getElementById('modalError').classList.add('d-none');
    clearValidation();
};

/**
 * Open the edit modal pre-filled with an expense's data.
 * @param {number} id - Expense ID.
 */
const openEditModal = async (id) => {
    try {
        const expense = await fetchExpenseById(id);
        document.getElementById('expenseId').value = expense.id;
        document.getElementById('expenseModalLabel').innerHTML =
            '<i class="bi bi-pencil me-2"></i>Edit Expense';
        document.getElementById('expenseAmount').value = expense.amount;
        document.getElementById('expenseCategory').value = expense.category;
        document.getElementById('expenseDate').value = expense.date;
        document.getElementById('expenseDescription').value = expense.description;
        document.getElementById('charCount').textContent = expense.description.length;
        document.getElementById('modalError').classList.add('d-none');
        clearValidation();

        const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
        modal.show();
    } catch (err) {
        showToast('Failed to load expense details', 'danger');
    }
};

/**
 * Clear Bootstrap validation classes from the form.
 */
const clearValidation = () => {
    document.querySelectorAll('#expenseForm .is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    document.querySelectorAll('#expenseForm .is-valid').forEach(el => {
        el.classList.remove('is-valid');
    });
};

/**
 * Validate the expense form. Returns true if valid.
 * @returns {boolean} Whether the form is valid.
 */
const validateForm = () => {
    let isValid = true;
    clearValidation();

    const amount = document.getElementById('expenseAmount');
    const category = document.getElementById('expenseCategory');
    const dateField = document.getElementById('expenseDate');
    const description = document.getElementById('expenseDescription');

    if (!amount.value || parseFloat(amount.value) <= 0) {
        amount.classList.add('is-invalid');
        isValid = false;
    } else {
        amount.classList.add('is-valid');
    }

    if (!category.value) {
        category.classList.add('is-invalid');
        isValid = false;
    } else {
        category.classList.add('is-valid');
    }

    if (!dateField.value) {
        dateField.classList.add('is-invalid');
        isValid = false;
    } else {
        dateField.classList.add('is-valid');
    }

    if (description.value.length > 200) {
        description.classList.add('is-invalid');
        isValid = false;
    }

    return isValid;
};

/**
 * Handle saving an expense (create or update).
 */
const saveExpense = async () => {
    if (!validateForm()) return;

    const id = document.getElementById('expenseId').value;
    const data = {
        amount: parseFloat(document.getElementById('expenseAmount').value),
        category: document.getElementById('expenseCategory').value,
        date: document.getElementById('expenseDate').value,
        description: document.getElementById('expenseDescription').value,
    };

    try {
        if (id) {
            /* Update existing */
            await updateExpense(id, data);
            showToast('Expense updated', 'info');
        } else {
            /* Create new */
            await createExpense(data);
            showToast('Expense added successfully', 'success');
        }

        /* Close modal */
        const modalEl = document.getElementById('expenseModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        /* Refresh everything */
        await Promise.all([renderTable(), renderRecentExpenses(), updateStats()]);
    } catch (err) {
        document.getElementById('modalError').textContent = err.message;
        document.getElementById('modalError').classList.remove('d-none');
    }
};

/* ============================================================
   DELETE LOGIC
   ============================================================ */

/**
 * Confirm and execute expense deletion.
 */
const confirmDelete = async () => {
    if (!pendingDeleteId) return;

    try {
        await deleteExpense(pendingDeleteId);

        /* Fade out the row */
        const row = document.getElementById(`expense-row-${pendingDeleteId}`);
        if (row) {
            row.classList.add('fade-out');
            setTimeout(() => row.remove(), 400);
        }

        showToast('Expense deleted', 'danger');

        /* Close modal */
        const modalEl = document.getElementById('deleteModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        pendingDeleteId = null;

        /* Refresh stats and recent */
        setTimeout(async () => {
            await Promise.all([renderTable(), renderRecentExpenses(), updateStats()]);
        }, 450);
    } catch (err) {
        showToast('Failed to delete expense', 'danger');
    }
};

/* ============================================================
   EVENT LISTENERS
   ============================================================ */

/**
 * Attach click listeners to edit/delete buttons in table rows.
 */
const attachRowListeners = () => {
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const id = e.currentTarget.dataset.id;
            openEditModal(id);
        });
    });

    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            pendingDeleteId = e.currentTarget.dataset.id;
            const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
            modal.show();
        });
    });
};

/**
 * Initialize all event listeners on page load.
 */
const initEventListeners = () => {
    /* Save button */
    document.getElementById('btnSaveExpense').addEventListener('click', saveExpense);

    /* Delete confirm button */
    document.getElementById('btnConfirmDelete').addEventListener('click', confirmDelete);

    /* Add modal opens via nav button — reset form */
    document.getElementById('btnAddExpenseNav').addEventListener('click', openAddModal);

    /* Add first expense button in empty state */
    const btnFirst = document.getElementById('btnAddFirstExpense');
    if (btnFirst) {
        btnFirst.addEventListener('click', openAddModal);
    }

    /* Character counter for description */
    document.getElementById('expenseDescription').addEventListener('input', (e) => {
        document.getElementById('charCount').textContent = e.target.value.length;
    });

    /* Filter listeners */
    document.getElementById('filterCategory').addEventListener('change', onFilterChange);
    document.getElementById('filterStartDate').addEventListener('change', onFilterChange);
    document.getElementById('filterEndDate').addEventListener('change', onFilterChange);
    document.getElementById('filterKeyword').addEventListener('input', debounce(onFilterChange, 300));
    document.getElementById('btnClearFilters').addEventListener('click', clearFilters);

    /* Sort headers */
    document.querySelectorAll('#expensesTable .sortable').forEach(th => {
        th.addEventListener('click', () => handleSort(th.dataset.sort));
        th.style.cursor = 'pointer';
    });

    /* Sidebar navigation smooth scroll */
    document.querySelectorAll('#sidebar .nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            /* Remove active from all links */
            document.querySelectorAll('#sidebar .nav-link').forEach(l => l.classList.remove('active'));
            e.currentTarget.classList.add('active');

            const targetId = e.currentTarget.getAttribute('href');
            if (targetId && targetId.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });

    /* Allow Enter key in modal form */
    document.getElementById('expenseForm').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveExpense();
        }
    });
};

/* ============================================================
   INITIALIZATION
   ============================================================ */

/**
 * Main initialization — runs when DOM is ready.
 */
document.addEventListener('DOMContentLoaded', async () => {
    initEventListeners();
    /* Set default date */
    document.getElementById('expenseDate').value = todayStr();
    /* Load all data */
    await Promise.all([renderTable(), renderRecentExpenses(), updateStats()]);
});
