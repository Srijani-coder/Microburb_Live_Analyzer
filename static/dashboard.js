document.addEventListener("DOMContentLoaded", function () {
    function getJsonData(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.warn("Failed to parse JSON for", id, e);
            return null;
        }
    }

    // ===== Listings per Year =====
    const yearlySales = getJsonData("yearData");
    if (yearlySales && Object.keys(yearlySales).length > 0) {
        const labels = Object.keys(yearlySales).sort((a, b) => Number(a) - Number(b));
        const values = labels.map((y) => yearlySales[y]);

        const ctx = document.getElementById("yearChart").getContext("2d");
        new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    borderWidth: 2,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // ===== Median Price by Property Type =====
    const ptypeMedian = getJsonData("ptypeMedianData");
    if (ptypeMedian && Object.keys(ptypeMedian).length > 0) {
        const labels = Object.keys(ptypeMedian);
        const values = labels.map((k) => ptypeMedian[k]);

        const ctx = document.getElementById("ptypeChart").getContext("2d");
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // ===== Median Price by Bedrooms =====
    const bedMedian = getJsonData("bedMedianData");
    if (bedMedian && Object.keys(bedMedian).length > 0) {
        const labels = Object.keys(bedMedian);
        const values = labels.map((k) => bedMedian[k]);

        const ctx = document.getElementById("bedChart").getContext("2d");
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
});
