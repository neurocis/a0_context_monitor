import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";

const model = {
  contextMemoryMap: {},
  _sidebarMounted: false,
  _sidebarObserver: null,
  _syncScheduled: false,
  _fetchTimer: null,

  onOpen() {
    this.mountSidebarEnhancer();
  },

  cleanup() {
    if (this._sidebarObserver) {
      this._sidebarObserver.disconnect();
      this._sidebarObserver = null;
    }
    if (this._fetchTimer) {
      clearInterval(this._fetchTimer);
      this._fetchTimer = null;
    }
    this._sidebarMounted = false;
    this._syncScheduled = false;
  },

  // Format bytes to human-readable size with dynamic units
  _formatSize(bytes) {
    if (typeof bytes !== "number" || bytes <= 0) return "";
    const kb = bytes / 1024;
    const mb = kb / 1024;
    const gb = mb / 1024;
    if (gb >= 1) return `${gb.toFixed(1)}GB`;
    if (mb >= 1) return `${mb.toFixed(1)}MB`;
    return `${kb.toFixed(1)}KB`;
  },

  // Extract context ID from a sidebar row via Alpine's x-for scope.
  // Falls back to index-based lookup from chatsStore when Alpine data
  // is not yet available (e.g. during initial render).
  _getContextIdFromRow(row, fallbackIndex) {
    // Primary: walk up to <li> and read Alpine's _x_dataStack
    let el = row.closest("li") || row;
    while (el && el !== document.body) {
      if (el._x_dataStack) {
        for (const scope of el._x_dataStack) {
          try {
            if (scope.context && scope.context.id) {
              return scope.context.id;
            }
          } catch (_) { /* proxy access may fail during teardown */ }
        }
        break;
      }
      el = el.parentElement;
    }
    // Fallback: index-based lookup from chatsStore
    const contexts = Array.isArray(chatsStore.contexts)
      ? chatsStore.contexts
      : [];
    if (
      typeof fallbackIndex === "number" &&
      fallbackIndex >= 0 &&
      fallbackIndex < contexts.length
    ) {
      return contexts[fallbackIndex]?.id || null;
    }
    return null;
  },

  // Fetch memory data from API
  async fetchMemoryData() {
    try {
      const response = await callJsonApi(
        "/api/plugins/a0_context_monitor/context_monitor_api",
        { action: "contexts", detailed: true }
      );
      if (response && response.contexts && Array.isArray(response.contexts)) {
        this.contextMemoryMap = {};
        response.contexts.forEach((ctx) => {
          if (ctx.id && typeof ctx.estimated_size_bytes === "number") {
            this.contextMemoryMap[ctx.id] = ctx.estimated_size_bytes;
          } else if (ctx.id && typeof ctx.estimated_size_mb === "number") {
            this.contextMemoryMap[ctx.id] = ctx.estimated_size_mb * 1024 * 1024;
          }
        });
        this.scheduleSidebarSync();
      }
    } catch (e) {
      console.error("[ContextMonitor] Error fetching memory data:", e);
    }
  },

  // Mount MutationObserver to watch for sidebar changes
  mountSidebarEnhancer() {
    if (this._sidebarMounted) {
      this.scheduleSidebarSync();
      return;
    }

    this._sidebarMounted = true;

    // Observe DOM mutations for chat list changes.
    // When the chat list is available, observe it directly with attribute
    // tracking so collapse/expand (style/class toggles) trigger a re-sync.
    this._sidebarObserver = new MutationObserver(() => {
      this.scheduleSidebarSync();
    });
    const _chatList = document.querySelector(".chats-config-list");
    this._sidebarObserver.observe(_chatList || document.body, {
      childList: true,
      subtree: true,
      attributes: !!_chatList,
      attributeFilter: ["style", "class"],
    });

    // Initial fetch and sync
    this.fetchMemoryData();

    // Periodic refresh every 30 seconds
    this._fetchTimer = setInterval(() => {
      this.fetchMemoryData();
    }, 30000);

    this.scheduleSidebarSync();
  },

  // Schedule a sync on the next animation frame (debounced)
  scheduleSidebarSync() {
    if (this._syncScheduled) return;
    this._syncScheduled = true;
    globalThis.requestAnimationFrame(() => {
      this._syncScheduled = false;
      this.syncSidebarMemory();
    });
  },

  // Sync memory spans into sidebar chat rows.
  // Uses Alpine scope data to resolve context IDs so hierarchy,
  // grouping, and collapse/expand do not break the mapping.
  syncSidebarMemory() {
    const list = document.querySelector(".chats-config-list");
    if (!list) return;

    // Upgrade observer: if we started on document.body and the chat
    // list is now in the DOM, re-scope for better perf + attribute tracking.
    if (!list._ctxMonObserved && this._sidebarObserver) {
      this._sidebarObserver.disconnect();
      this._sidebarObserver.observe(list, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["style", "class"],
      });
      list._ctxMonObserved = true;
    }

    const rows = Array.from(list.querySelectorAll(".chat-container"));

    rows.forEach((row, index) => {
      const existing = row.querySelector(".ctx-memory-size");
      const contextId = this._getContextIdFromRow(row, index);

      if (!contextId) {
        if (existing) existing.remove();
        return;
      }

      const sizeBytes = this.contextMemoryMap[contextId];

      if (typeof sizeBytes !== "number" || sizeBytes <= 0) {
        if (existing) existing.remove();
        return;
      }

      const formatted = this._formatSize(sizeBytes);
      if (!formatted) {
        if (existing) existing.remove();
        return;
      }

      if (existing && existing.dataset.contextId === contextId) {
        // Update existing span text
        existing.textContent = `(${formatted})`;
        return;
      }

      // Remove old span if context changed
      if (existing) existing.remove();

      // Find the chat name element to insert memory span after it
      const nameEl = row.querySelector(".chat-name");
      if (!nameEl) return;

      const span = document.createElement("span");
      span.className = "ctx-memory-size";
      span.dataset.contextId = contextId;
      span.textContent = `(${formatted})`;
      nameEl.insertAdjacentElement("afterend", span);
    });
  },
};

export const store = createStore("contextMonitor", model);
