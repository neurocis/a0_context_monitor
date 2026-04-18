/**
 * Context Monitor Store - Alpine.js Store Gate Module
 * Manages state for the context monitoring dashboard.
 * Follows mandatory Store Gate pattern using createStore from AlpineStore.js
 */

import { createStore } from "/js/AlpineStore.js";
import { toastFrontendSuccess, toastFrontendError } from "/components/notifications/notification-store.js";

const BASE_API = "/api/context-monitor";
const REFRESH_INTERVAL = 30000; // 30 seconds

export const contextMonitorStore = createStore("contextMonitorStore", {
    // State
    loading: false,
    error: null,
    available: false,
    summary: null,
    contexts: [],
    refreshTimer: null,

    /**
     * Initialize store when dashboard opens
     */
    async onOpen() {
        this.loading = true;
        this.error = null;

        try {
            // Check if context monitoring is available
            await this.checkStatus();

            if (this.available) {
                // Load initial data
                await this.refresh();

                // Set up auto-refresh every 30 seconds
                this.startAutoRefresh();
            }
        } catch (err) {
            this.error = `Failed to initialize: ${err.message}`;
            toastFrontendError(
                `Context Monitor initialization failed: ${err.message}`,
                "Context Monitor"
            );
        } finally {
            this.loading = false;
        }
    },

    /**
     * Clean up store when dashboard closes
     */
    cleanup() {
        this.stopAutoRefresh();
    },

    /**
     * Check if context monitoring is available
     */
    async checkStatus() {
        try {
            const response = await fetch(`${BASE_API}/status`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.available = data.available === true;

            if (!this.available) {
                this.error = data.message || "Context monitoring not available";
            }
        } catch (err) {
            this.available = false;
            this.error = `Status check failed: ${err.message}`;
            throw err;
        }
    },

    /**
     * Refresh all data (summary and contexts)
     */
    async refresh() {
        if (this.loading || !this.available) return;

        this.loading = true;
        this.error = null;

        try {
            // Fetch summary
            const summaryResponse = await fetch(`${BASE_API}/summary`);
            if (!summaryResponse.ok) {
                throw new Error(`Failed to fetch summary: HTTP ${summaryResponse.status}`);
            }
            this.summary = await summaryResponse.json();

            // Check for errors in summary response
            if (this.summary.status === "error") {
                throw new Error(this.summary.message || "Failed to get summary");
            }

            // Fetch detailed contexts
            const contextsResponse = await fetch(`${BASE_API}/contexts?detailed=true`);
            if (!contextsResponse.ok) {
                throw new Error(
                    `Failed to fetch contexts: HTTP ${contextsResponse.status}`
                );
            }
            const contextsData = await contextsResponse.json();

            // Check for errors in contexts response
            if (contextsData.error) {
                throw new Error(contextsData.error);
            }

            this.contexts = contextsData.contexts || [];
        } catch (err) {
            this.error = err.message;
            this.summary = null;
            this.contexts = [];
            toastFrontendError(
                `Refresh failed: ${err.message}`,
                "Context Monitor"
            );
        } finally {
            this.loading = false;
        }
    },

    /**
     * Export context inventory to JSON file
     */
    async exportInventory() {
        if (this.loading || !this.available) return;

        this.loading = true;
        this.error = null;

        try {
            const response = await fetch(`${BASE_API}/export`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({}),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();

            if (result.status === "error") {
                throw new Error(result.message || "Export failed");
            }

            toastFrontendSuccess(
                `Context inventory exported to ${result.file_path}`,
                "Context Monitor"
            );

            // Refresh data after export
            await this.refresh();
        } catch (err) {
            this.error = err.message;
            toastFrontendError(`Export failed: ${err.message}`, "Context Monitor");
        } finally {
            this.loading = false;
        }
    },

    /**
     * Get summary table as formatted string
     */
    async getFormattedTable() {
        try {
            const response = await fetch(`${BASE_API}/table`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data.table || "";
        } catch (err) {
            console.error("Failed to fetch table:", err);
            return null;
        }
    },

    /**
     * Get context by ID
     */
    async getContextDetail(contextId) {
        try {
            const response = await fetch(`${BASE_API}/contexts/${contextId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            return data.context || null;
        } catch (err) {
            console.error(`Failed to fetch context detail for ${contextId}:`, err);
            return null;
        }
    },

    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (!this.loading && this.available) {
                this.refresh().catch((err) => {
                    console.error("Auto-refresh failed:", err);
                });
            }
        }, REFRESH_INTERVAL);
    },

    /**
     * Stop auto-refresh timer
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    },
});
