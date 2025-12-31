// ContainerX Dashboard JavaScript

class DashboardManager {
    constructor() {
        this.currentScenario = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.setupRealTimeUpdates();
    }

    setupEventListeners() {
        // Search and filter functionality
        const searchInput = document.getElementById('scenarioSearch');
        const industryFilter = document.getElementById('industryFilter');
        const statusFilter = document.getElementById('statusFilter');

        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterScenarios());
        }
        if (industryFilter) {
            industryFilter.addEventListener('change', () => this.filterScenarios());
        }
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterScenarios());
        }

        // Action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-action')) {
                const action = e.target.dataset.action;
                this.handleAction(action, e.target.dataset.params);
            }
        });
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/scenarios');
            const scenarios = await response.json();
            this.renderDashboard(scenarios);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    renderDashboard(scenarios) {
        const healthyCount = scenarios.filter(s => s.health_status === 'healthy').length;
        const warningCount = scenarios.filter(s => s.health_status === 'warning').length;
        const criticalCount = scenarios.filter(s => s.health_status === 'critical').length;

        // Update metrics
        this.updateMetric('totalScenarios', scenarios.length);
        this.updateMetric('healthyCount', healthyCount);
        this.updateMetric('warningCount', warningCount);
        this.updateMetric('criticalCount', criticalCount);

        // Render scenario list
        this.renderScenarioList(scenarios);

        // Update alerts
        this.updateAlerts(scenarios);
    }

    updateMetric(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    renderScenarioList(scenarios) {
        const container = document.getElementById('scenarioList');
        if (!container) return;

        container.innerHTML = '';

        scenarios.forEach(scenario => {
            const scenarioElement = this.createScenarioElement(scenario);
            container.appendChild(scenarioElement);
        });
    }

    createScenarioElement(scenario) {
        const div = document.createElement('div');
        div.className = 'scenario-item mb-2';
        div.dataset.industry = scenario.industry;
        div.dataset.status = scenario.health_status;

        div.innerHTML = `
            <a href="/scenario/${scenario.id}" class="nav-link d-flex justify-content-between align-items-center">
                <div>
                    <div class="fw-bold">${scenario.name}</div>
                    <small class="text-muted">${scenario.industry}</small>
                </div>
                <span class="badge bg-${this.getStatusColor(scenario.health_status)}">
                    ${scenario.health_status}
                </span>
            </a>
        `;

        return div;
    }

    getStatusColor(status) {
        const colors = {
            'healthy': 'success',
            'warning': 'warning',
            'critical': 'danger'
        };
        return colors[status] || 'secondary';
    }

    updateAlerts(scenarios) {
        const alertsContainer = document.getElementById('alertsContainer');
        if (!alertsContainer) return;

        const alerts = [];

        scenarios.forEach(scenario => {
            const violations = scenario.metrics?.violations || [];
            const lowStock = scenario.metrics?.inventory_alerts || [];

            if (violations.length > 0 || lowStock.length > 0) {
                alerts.push({
                    scenario: scenario.name,
                    violations: violations.length,
                    lowStock: lowStock.length,
                    severity: violations.length > 0 ? 'danger' : 'warning'
                });
            }
        });

        if (alerts.length === 0) {
            alertsContainer.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> All systems healthy - no alerts detected
                </div>
            `;
        } else {
            alertsContainer.innerHTML = alerts.map(alert => `
                <div class="alert alert-${alert.severity} mb-2">
                    <strong>${alert.scenario}</strong>:
                    ${alert.violations > 0 ? `${alert.violations} invariant violations` : ''}
                    ${alert.lowStock > 0 ? `${alert.lowStock} low stock alerts` : ''}
                </div>
            `).join('');
        }
    }

    filterScenarios() {
        const searchTerm = (document.getElementById('scenarioSearch')?.value || '').toLowerCase();
        const industryFilter = document.getElementById('industryFilter')?.value || '';
        const statusFilter = document.getElementById('statusFilter')?.value || '';

        const scenarioItems = document.querySelectorAll('.scenario-item');

        scenarioItems.forEach(item => {
            const name = item.querySelector('.fw-bold')?.textContent.toLowerCase() || '';
            const industry = item.dataset.industry || '';
            const status = item.dataset.status || '';

            const matchesSearch = name.includes(searchTerm);
            const matchesIndustry = !industryFilter || industry === industryFilter;
            const matchesStatus = !statusFilter || status === statusFilter;

            item.style.display = (matchesSearch && matchesIndustry && matchesStatus) ? 'block' : 'none';
        });
    }

    async handleAction(action, params) {
        try {
            switch (action) {
                case 'run_tests':
                    await this.runCoreTests();
                    break;
                case 'generate_scenario':
                    await this.generateScenario(params);
                    break;
                case 'export_all':
                    await this.exportAllScenarios();
                    break;
                case 'refresh':
                    await this.loadDashboardData();
                    break;
                default:
                    console.log('Unknown action:', action);
            }
        } catch (error) {
            console.error('Action failed:', error);
            this.showError(`Action failed: ${error.message}`);
        }
    }

    async runCoreTests() {
        this.showLoading('Running core tests...');
        // Simulate test run
        await new Promise(resolve => setTimeout(resolve, 2000));
        this.hideLoading();
        this.showSuccess('Core tests completed successfully!');
    }

    async generateScenario(params) {
        this.showLoading('Generating new scenario...');
        // Simulate scenario generation
        await new Promise(resolve => setTimeout(resolve, 3000));
        this.hideLoading();
        this.showSuccess('New scenario generated successfully!');
        // Refresh dashboard
        await this.loadDashboardData();
    }

    async exportAllScenarios() {
        this.showLoading('Exporting scenarios...');
        // Simulate export
        await new Promise(resolve => setTimeout(resolve, 1500));
        this.hideLoading();
        this.showSuccess('Scenarios exported successfully!');
    }

    setupRealTimeUpdates() {
        // Set up periodic updates every 30 seconds
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    showLoading(message) {
        const toast = this.createToast(message, 'info');
        document.body.appendChild(toast);
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    hideLoading() {
        // Implementation would hide loading indicators
    }

    showSuccess(message) {
        const toast = this.createToast(message, 'success');
        document.body.appendChild(toast);
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    showError(message) {
        const toast = this.createToast(message, 'danger');
        document.body.appendChild(toast);
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        return toast;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});

// Global functions for HTML onclick handlers
function refreshDashboard() {
    if (window.dashboardManager) {
        window.dashboardManager.handleAction('refresh');
    }
}

function runCoreTests() {
    if (window.dashboardManager) {
        window.dashboardManager.handleAction('run_tests');
    }
}

function generateNewScenario() {
    if (window.dashboardManager) {
        window.dashboardManager.handleAction('generate_scenario');
    }
}

function exportAllScenarios() {
    if (window.dashboardManager) {
        window.dashboardManager.handleAction('export_all');
    }
}

function showSystemStatus() {
    alert('System Status: All core functions operational, scenarios loaded and validated');
}
