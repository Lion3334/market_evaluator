document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const tableBody = document.getElementById('tableBody');

    // Mock Data (Single Card Analysis - Caleb Williams Cosmic Chrome)
    const cardData = [
        {
            grade: "PSA 10",
            title: "Gem Mint",
            pop: 79,
            totalGraded: 136, // Derived from total pop
            successRate: 58.1, // Gem Rate
            avgBin: 1450.00,
            avgAuction: 1250.75,
            activeVol: 4,
            trendData: [1100, 1150, 1300, 1280, 1450],
            isGem: true
        },
        {
            grade: "PSA 9",
            title: "Mint",
            pop: 37,
            totalGraded: 136,
            successRate: 27.2, // % of total graded
            avgBin: 425.50,
            avgAuction: 380.20,
            activeVol: 8,
            trendData: [450, 420, 390, 410, 425],
            isGem: false
        },
        {
            grade: "PSA 8",
            title: "NM-MT",
            pop: 12,
            totalGraded: 136,
            successRate: 8.8,
            avgBin: 180.00,
            avgAuction: 155.50,
            activeVol: 2,
            trendData: [200, 190, 180, 175, 180],
            isGem: false
        },
        {
            grade: "Raw",
            title: "Ungraded",
            pop: null, // N/A for raw
            totalGraded: null,
            successRate: null,
            avgBin: 380.10,
            avgAuction: 315.45,
            activeVol: 15,
            trendData: [320, 340, 310, 350, 380],
            isGem: false
        }
    ];

    // Initialize
    function init() {
        renderTable();
    }

    // Format Helpers
    const formatCurrency = (val) => {
        if (!val) return '-';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(val);
    };

    const formatNumber = (val) => {
        if (val === null) return '-';
        return new Intl.NumberFormat('en-US').format(val);
    };

    // Generate Sparkline HTML
    function generateSparkline(data) {
        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;

        return `
            <div class="sparkline">
                ${data.map(val => {
            const height = ((val - min) / range * 80) + 20; // Min 20% height
            let className = 'medium';
            if (val === max) className = 'max';
            else if (val > (max + min) / 2) className = 'high';
            else className = 'low';

            return `<div class="sparkline-bar ${className}" style="height: ${height}%"></div>`;
        }).join('')}
            </div>
        `;
    }

    // Determine Badge Class
    function getGradeBadgeClass(grade) {
        if (grade.includes('10')) return 'badge-gem';
        if (grade.includes('9')) return 'badge-mint';
        if (grade === 'Raw') return 'badge-raw';
        return 'badge-std';
    }

    // Render Table
    function renderTable() {
        tableBody.innerHTML = '';

        cardData.forEach(item => {
            const row = document.createElement('tr');

            // Format Success Rate / Pop Share
            let successHtml = '-';
            if (item.successRate !== null) {
                const isHigh = item.successRate > 50;
                successHtml = `<span class="success-rate ${isHigh ? 'high' : 'std'}">${item.successRate}%</span>`;
            }

            row.innerHTML = `
                <td>
                    <div class="condition-cell">
                        <span class="grade-badge ${getGradeBadgeClass(item.grade)}">${item.grade}</span>
                        <span class="grade-title">${item.title}</span>
                    </div>
                </td>
                <td class="text-center font-mono">${formatNumber(item.pop)}</td>
                <td class="text-center">${successHtml}</td>
                <td class="text-center font-bold bin-price">${formatCurrency(item.avgBin)}</td>
                <td class="text-center font-bold auction-price">${formatCurrency(item.avgAuction)}</td>
                <td class="text-center">${formatNumber(item.activeVol)}</td>
                <td class="col-trend">
                    ${generateSparkline(item.trendData)}
                </td>
            `;

            tableBody.appendChild(row);
        });
    }

    // Run
    init();
});
