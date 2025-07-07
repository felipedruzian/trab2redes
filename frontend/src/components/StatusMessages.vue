<template>
  <div v-if="hasMessages" class="status-container">
    <div v-if="loading" class="status-message status-loading">
      <div class="loading-spinner"></div>
      <span>Carregando dados...</span>
    </div>
    <div v-if="error" class="status-message status-error">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>
    <div v-if="success" class="status-message status-success">
      <i class="fas fa-check-circle"></i>
      <span>{{ success }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatusMessages',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    },
    success: {
      type: String,
      default: null
    }
  },
  computed: {
    hasMessages() {
      return this.loading || this.error || this.success;
    }
  }
};
</script>

