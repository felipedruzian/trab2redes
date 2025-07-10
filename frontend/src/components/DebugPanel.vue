<template>
  <div class="debug-panel">
    <button @click="isExpanded = !isExpanded" class="btn-base debug-toggle">
      <i class="fas fa-code"></i>
      Informações de Debug
    </button>
    <div v-if="isExpanded" class="debug-content">
      <div v-if="debugData.jsonOutput" class="debug-section">
        <div @click="toggleSection('json')" class="debug-section-header">
          <span><i class="fas fa-file-code"></i> JSON Response</span>
        </div>
        <div v-if="sectionsExpanded.json" class="debug-section-content">
          <pre>{{ debugData.jsonOutput }}</pre>
        </div>
      </div>
      <div v-if="debugData.requestInfo" class="debug-section">
        <div @click="toggleSection('request')" class="debug-section-header">
          <span><i class="fas fa-exchange-alt"></i> Informações da Requisição</span>
        </div>
        <div v-if="sectionsExpanded.request" class="debug-section-content">
          <pre>{{ debugData.requestInfo }}</pre>
        </div>
      </div>
      <div v-if="debugData.errorDetails" class="debug-section">
         <div @click="toggleSection('error')" class="debug-section-header">
          <span><i class="fas fa-exclamation-triangle"></i> Detalhes do Erro</span>
        </div>
        <div v-if="sectionsExpanded.error" class="debug-section-content">
          <pre>{{ debugData.errorDetails }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DebugPanel',
  props: {
    debugData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      isExpanded: false,
      sectionsExpanded: {
        json: true,
        request: true,
        error: true
      }
    };
  },
  methods: {
    toggleSection(section) {
      this.sectionsExpanded[section] = !this.sectionsExpanded[section];
    }
  },
  watch: {
    debugData: {
      handler(newData) {
        if (newData.jsonOutput || newData.requestInfo || newData.errorDetails) {
          this.isExpanded = true;
        }
      },
      deep: true
    }
  }
};
</script>
