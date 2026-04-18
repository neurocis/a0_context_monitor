import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";

const TOKEN_EL_ID = "token-count-label";

const model = {
  system_tokens: 0,
  context_tokens: 0,
  prompt_tokens: 0,
  response_tokens: 0,
  total_tokens: 0,
  _fetchTimer: null,
  _mounted: false,
  _tokenEl: null,

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

  mountTokenDisplay() {
    // Inject a token count span inside #progress-bar-right, before stop-speech
    const rightBar = document.getElementById("progress-bar-right");
    if (!rightBar) return;

    let el = document.getElementById(TOKEN_EL_ID);
    if (!el) {
      el = document.createElement("span");
      el.id = TOKEN_EL_ID;
      el.className = "token-count-label";
      el.style.cssText =
        "font-size:8pt;opacity:0.6;font-family:monospace;white-space:nowrap;user-select:none;margin-right:8px;";
      const stopSpeech = document.getElementById("progress-bar-stop-speech");
      if (stopSpeech) {
        rightBar.insertBefore(el, stopSpeech);
      } else {
        rightBar.prepend(el);
      }
    }
    this._tokenEl = el;
    this._updateDisplay();
  },

  unmountTokenDisplay() {
    const el = document.getElementById(TOKEN_EL_ID);
    if (el) el.remove();
    this._tokenEl = null;
  },

  _updateDisplay() {
    const el = this._tokenEl || document.getElementById(TOKEN_EL_ID);
    if (!el) return;
    if (this.total_tokens <= 0) {
      el.textContent = "";
      el.style.display = "none";
      return;
    }
    el.style.display = "";
    el.textContent =
      `SYS: ${this.formatTokenCount(this.system_tokens)} | CTX: ${this.formatTokenCount(this.context_tokens)} | PRM: ${this.formatTokenCount(this.prompt_tokens)} | RES: ${this.formatTokenCount(this.response_tokens)}`;
  },

  async fetchTokenData() {
    try {
      const activeContextId = chatsStore.selected;
      const response = await callJsonApi(
        "/api/plugins/a0_context_monitor/context_monitor_api",
        { action: "token_counts", context_id: activeContextId || "" }
      );
      if (response && !response.error) {
        if (response.context_id) {
          this.system_tokens = response.system_tokens || 0;
          this.context_tokens = response.context_tokens || 0;
          this.prompt_tokens = response.prompt_tokens || 0;
          this.response_tokens = response.response_tokens || 0;
          this.total_tokens = response.total_tokens || 0;
        } else if (response.contexts && activeContextId && response.contexts[activeContextId]) {
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
    this._updateDisplay();
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
