<template>
  <div id="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="container">
        <h1><i class="fas fa-search"></i> Sistema de Consulta Integrada</h1>
        <p>Consulte informações de pessoas físicas e jurídicas de forma integrada</p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="container">
        <!-- Search Component -->
        <SearchForm
          @search="handleSearch"
          @person-selected="handlePersonSelected"
          :loading="loading"
        />

        <!-- Status Messages -->
        <StatusMessages
          :loading="loading"
          :error="error"
          :success="success"
        />

        <!-- Card da Pessoa Selecionada -->
        <SearchResults
          v-if="selectedPerson"
          :results="{ type: 'selected_person' }"
          :selected-person="selectedPerson"
        />

        <!-- Results Display -->
        <SearchResults
          v-if="results"
          :results="results"
          :selected-person="selectedPerson"
          @person-selected="handlePersonSelected"
        />

        <!-- Debug Section -->
        <DebugPanel
          v-if="debugData.jsonOutput || debugData.requestInfo"
          :debug-data="debugData"
          @clear-debug="clearDebugData"
        />
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import SearchForm from './components/SearchForm.vue';
import SearchResults from './components/SearchResults.vue';
import StatusMessages from './components/StatusMessages.vue';
import DebugPanel from './components/DebugPanel.vue';

export default {
  name: 'App',
  components: {
    SearchForm,
    SearchResults,
    StatusMessages,
    DebugPanel
  },
  data() {
    return {
      loading: false,
      error: null,
      success: null,
      results: null,
      selectedPerson: null,
      debugData: {
        jsonOutput: null,
        requestInfo: null,
        performanceInfo: null,
        errorDetails: null
      }
    };
  },
  methods: {
    clearMessages() {
      this.error = null;
      this.success = null;
    },
    clearDebugData() {
      this.debugData = {
        jsonOutput: null,
        requestInfo: null,
        performanceInfo: null,
        errorDetails: null
      };
    },
    async handleSearch(searchData) {
      this.loading = true;
      this.clearMessages();
      this.clearDebugData();
      this.results = null;
      // Limpar selectedPerson ao iniciar uma nova busca
      this.selectedPerson = null;

      try {
        let endpoint, requestData;

        if (searchData.type === 'person') {
          endpoint = '/api/search_person';
          requestData = { query: searchData.query };
        } else {
          endpoint = '/api/search_company';
          requestData = { cnpj: searchData.query };
        }

        const startTime = performance.now();
        const response = await axios.post(endpoint, requestData);
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        this.debugData.requestInfo = JSON.stringify({
          url: endpoint,
          method: 'POST',
          requestData: requestData,
          status: response.status,
          statusText: response.statusText,
          responseTime: `${duration}ms`,
          timestamp: new Date().toISOString()
        }, null, 2);

        this.debugData.jsonOutput = JSON.stringify(response.data, null, 2);
        this.results = response.data;
        this.setSuccessMessage(response.data);

      } catch (err) {
        this.error = err.response?.data?.error || `Erro ao buscar dados: ${err.message}`;
        this.debugData.errorDetails = JSON.stringify({
          message: err.message,
          status: err.response?.status || 'Network Error',
          responseData: err.response?.data || null,
        }, null, 2);
      } finally {
        this.loading = false;
      }
    },
    async handlePersonSelected(cpf) {
      // Encontrar a pessoa selecionada nos resultados atuais
      if (this.results && this.results.people) {
        this.selectedPerson = this.results.people.find(person => person.cpf === cpf);
      }

      this.loading = true;
      this.clearMessages();
      this.clearDebugData();

      try {
        const endpoint = '/api/person_companies';
        const requestData = { cpf: cpf };

        const startTime = performance.now();
        const response = await axios.post(endpoint, requestData);
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        this.debugData.requestInfo = JSON.stringify({
          url: endpoint,
          method: 'POST',
          requestData: requestData,
          status: response.status,
          responseTime: `${duration}ms`,
          timestamp: new Date().toISOString()
        }, null, 2);

        this.debugData.jsonOutput = JSON.stringify(response.data, null, 2);
        this.results = response.data;
        this.success = `Empresas da pessoa carregadas com sucesso! Encontradas ${response.data.data?.length || 0} empresa(s).`;

      } catch (err) {
        this.error = err.response?.data?.error || `Erro ao buscar empresas: ${err.message}`;
        this.debugData.errorDetails = JSON.stringify({
          message: err.message,
          status: err.response?.status || 'Network Error',
          responseData: err.response?.data || null,
        }, null, 2);
      } finally {
        this.loading = false;
      }
    },
    setSuccessMessage(data) {
      switch (data.type) {
        case 'people_list':
          this.success = `Busca realizada com sucesso! Encontradas ${data.people?.length || 0} pessoa(s).`;
          break;
        case 'company_data':
          this.success = `Empresa encontrada com sucesso! ${data.data?.partners?.length || 0} sócio(s) associado(s).`;
          break;
        case 'company_not_found':
          this.success = `Busca realizada com sucesso! ${data.message}`;
          break;
        case 'person_companies':
          this.success = `Empresas encontradas com sucesso! ${data.data?.length || 0} empresa(s) associada(s).`;
          break;
        default:
          this.success = `Dados carregados com sucesso!`;
      }
    }
  }
}
</script>

<style>
/* Você pode importar seu styles.css em main.js ou colocar os estilos aqui. */
/* Para estilos específicos deste componente, use <style scoped> */
</style>