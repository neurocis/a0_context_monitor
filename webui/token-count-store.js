import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";

const model = {
  system_tokens: 0,
  context_tokens: 0,
  prompt_tokens: 0,
  response_tokens: 0,
  total_tokens: 0,
  _fetchTimer: null,
  _mounted: false,

  onOpen() {
    this._mounted = true;
    this.fetchTokenData();
    this._fetchTimer = setInterval(() => {
      this.fetchTokenData();
    }, 10000);
  },

  cleanup() {
    this._mounted = false;
    if (this._fetchTimer) {
      clearInterval(this._fetchTimer);
      this._fetchTimer = null;
    }
  },

  async fetchTokenData() {
    try {
      const activeContextId = chatsStore.selected;
      const response = await callJsonApi(
        "/api/plugins/a0_context_monitor/context_monitor_api",
        { action: "token_counts", context_id: activeContextId || "" }
      );
      if (response && !response.error) {
        // If specific context, data is at root level
        if (response.context_id) {
          this.system_tokens = response.system_tokens || 0;
          this.context_tokens = response.context_tokens || 0;
          this.prompt_tokens = response.prompt_tokens || 0;
          this.response_tokens = response.response_tokens || 0;
          this.total_tokens = response.total_tokens || 0;
        } else if (response.contexts && activeContextId && response.contexts[activeContextId]) {
          // If all contexts returned, pick the active one
          const data = response.contexts[activeContextId];
          this.system_tokens = data.system_tokens || 0;
          this.context_tokens = data.context_tokens || 0;
          this.prompt_tokens = data.prompt_tokens || 0;
          this.response_tokens = data.response_tokens || 0;
          this.total_tokens = data.total_tokens || 0;
        } else {
          this.system_tokens = 0;
          this.context_tokens = 0;
          this.prompt_tokens = 0;
          this.response_tokens = 0;
          this.total_tokens = 0;
        }
      }
    } catch (e) {
      console.error("[TokenCount] Error fetching token data:", e);
    }
  },

  formatTokenCount(count) {
    if (typeof count !== "number" || count <= 0) return "0";
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return String(count);
  },

  get hasData() {
    return this.total_tokens > 0;
  },
};

export const store = createStore("tokenCount", model);
