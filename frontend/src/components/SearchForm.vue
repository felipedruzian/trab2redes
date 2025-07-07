<template>
  <div class="card">
    <div class="card-header">
      <i class="fas fa-search"></i>
      <h3>Buscar Informações</h3>
    </div>
    <div class="card-content">
      <div class="search-tabs">
        <button
          class="tab-button"
          :class="{ active: searchType === 'person' }"
          @click="searchType = 'person'"
        >
          <i class="fas fa-user"></i> Pessoa Física
        </button>
        <button
          class="tab-button"
          :class="{ active: searchType === 'company' }"
          @click="searchType = 'company'"
        >
          <i class="fas fa-building"></i> Pessoa Jurídica
        </button>
      </div>

      <div class="search-form">
        <input
          v-model="searchQuery"
          :placeholder="getPlaceholder()"
          class="search-input"
          @keyup.enter="performSearch"
          @input="clearValidationError"
        />
        <button
          @click="performSearch"
          :disabled="loading || !searchQuery.trim()"
          class="search-button"
        >
          <span v-if="loading" class="loading-spinner"></span>
          <i v-else class="fas fa-search"></i>
          {{ loading ? 'Buscando...' : 'Buscar' }}
        </button>
      </div>

      <div v-if="validationError" class="status-message status-error">
        <i class="fas fa-exclamation-triangle"></i>
        {{ validationError }}
      </div>

      <div class="search-tips">
        <h4><i class="fas fa-lightbulb"></i> Dicas de Busca:</h4>
        <ul v-if="searchType === 'person'">
          <li><strong>CPF:</strong> Digite apenas números (ex: 12345678901)</li>
          <li><strong>Nome:</strong> Digite parte do nome ou nome completo</li>
        </ul>
        <ul v-else>
          <li><strong>CNPJ:</strong> Digite apenas números (ex: 12345678000195)</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { CPFValidator, CNPJValidator } from '../utils/validators';

export default {
  name: 'SearchForm',
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      searchType: 'person',
      searchQuery: '',
      validationError: null,
    };
  },
  methods: {
    getPlaceholder() {
      return this.searchType === 'person'
        ? 'Digite CPF ou Nome'
        : 'Digite CNPJ ';
    },
    clearValidationError() {
      this.validationError = null;
    },
    performSearch() {
      if (!this.searchQuery.trim()) return;

      const cleanQuery = this.searchQuery.replace(/\D/g, '');
      if (this.searchType === 'person' && cleanQuery.length === 11) {
        if (!CPFValidator.isValid(cleanQuery)) {
          this.validationError = 'CPF inválido. Verifique os dígitos.';
          return;
        }
      } else if (this.searchType === 'company') {
        if (!CNPJValidator.isValid(this.searchQuery)) {
          this.validationError = 'CNPJ inválido. Verifique os dígitos.';
          return;
        }
      }
      
      this.validationError = null;
      
      this.$emit('search', {
        type: this.searchType,
        query: this.searchQuery.trim()
      });
    }
  },
  watch: {
    searchType() {
      this.searchQuery = '';
      this.validationError = null;
    }
  }
};
</script>
