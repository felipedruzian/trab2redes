<template>
  <div class="search-results">
    <!-- Lista de Pessoas -->
    <div v-if="results.type === 'people_list'" class="card">
      <div class="card-header">
        <i class="fas fa-users"></i>
        <h3>Pessoas Encontradas ({{ results.people.length }})</h3>
      </div>
      <div class="card-content">
        <p class="results-instruction">
          <i class="fas fa-info-circle"></i>
          Clique em uma pessoa para ver suas empresas associadas:
        </p>
        <div class="people-grid grid-base">
          <div
            v-for="person in results.people"
            :key="person.cpf"
            class="person-card card-item-base"
            @click="selectPerson(person.cpf)"
          >
            <div class="person-name item-name ">
              <i class="fas fa-user"></i>
              {{ person.nome }}
            </div>
            <div class="person-cpf">
              <strong>CPF:</strong> {{ formatCPF(person.cpf) }}
            </div>
            <div v-if="person.sexo" class="person-detail">
              <strong>Sexo:</strong> {{ person.sexo }}
            </div>
            <div v-if="person.nasc" class="person-detail">
              <strong>Nascimento:</strong> {{ formatDate(person.nasc) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dados da Pessoa Selecionada -->
    <div v-if="selectedPerson && results.type === 'selected_person'" class="company-results">
      <div class="card company-info">
        <div class="company-name">
          <i class="fas fa-user"></i>
          {{ selectedPerson.nome }}
        </div>
        <div class="company-details">
          <div><strong>CPF:</strong> {{ formatCPF(selectedPerson.cpf) }}</div>
          <div v-if="selectedPerson.sexo"><strong>Sexo:</strong> {{ selectedPerson.sexo }}</div>
          <div v-if="selectedPerson.nasc"><strong>Nascimento:</strong> {{ formatDate(selectedPerson.nasc) }}</div>
        </div>
      </div>
    </div>

    <!-- Dados da Empresa -->
    <div v-if="results.type === 'company_data'" class="company-results">
      <div class="card company-info">
        <div class="company-name">
          <i class="fas fa-building"></i>
          {{ results.data.company.razao_social }}
        </div>
        <div class="company-details">
          <div><strong>CNPJ:</strong> {{ formatCNPJ(results.data.company.cnpj) }}</div>
          <div><strong>Nome Fantasia:</strong> {{ results.data.company.nome_fantasia || 'N/A' }}</div>
          <div><strong>Situação:</strong> {{ results.data.company.situacao_cadastral || 'N/A' }}</div>
          <div><strong>Porte:</strong> {{ results.data.company.porte_empresa || 'N/A' }}</div>
          <div><strong>Capital Social:</strong> {{ formatCurrency(results.data.company.capital_social) }}</div>
          <div><strong>Início Atividades:</strong> {{ formatDate(results.data.company.data_inicio_atividades) }}</div>
        </div>
      </div>

      <!-- Endereço da Empresa -->
      <div v-if="hasAddress(results.data.company)" class="card">
        <div class="card-header">
          <i class="fas fa-map-marker-alt"></i>
          <h3>Endereço</h3>
        </div>
        <div class="card-content">
          <div class="address-info">
            {{ getFullAddress(results.data.company) }}
          </div>
        </div>
      </div>

      <!-- Sócios -->
      <div class="card partners-section">
        <div class="card-header">
          <i class="fas fa-handshake"></i>
          <h3>Sócios ({{ results.data.partners.length }})</h3>
        </div>
        <div class="card-content">
          <div v-if="results.data.partners.length === 0" class="no-results">
            <i class="fas fa-info-circle"></i>
            Nenhum sócio encontrado para esta empresa.
          </div>
          <div v-else class="partners-grid grid-base">
            <div
              v-for="(partner, index) in results.data.partners"
              :key="index"
              class="partner-card card-item-base"
            >
              <div class="partner-name item-name ">
                <i class="fas fa-user-tie"></i>
                {{ partner.nome_socio || partner.nome_completo }}
              </div>
              <div class="partner-details item-details">
                <div v-if="partner.cpf">
                  <strong>CPF:</strong> {{ formatCPF(partner.cpf) }}
                </div>
                <div v-if="partner.qualificacao_socio">
                  <strong>Qualificação:</strong> {{ partner.qualificacao_socio }}
                </div>
                <div v-if="partner.data_entrada_sociedade">
                  <strong>Entrada na Sociedade:</strong> {{ formatDate(partner.data_entrada_sociedade) }}
                </div>
                <div v-if="partner.faixa_etaria">
                  <strong>Faixa Etária:</strong> {{ partner.faixa_etaria }}
                </div>
                <div v-if="partner.sexo">
                  <strong>Sexo:</strong> {{ partner.sexo }}
                </div>
                <div v-if="partner.data_nascimento">
                  <strong>Nascimento:</strong> {{ formatDate(partner.data_nascimento) }}
                </div>
                <div v-if="partner.percentual_capital_social">
                  <strong>Participação:</strong> {{ partner.percentual_capital_social }}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empresas de uma Pessoa -->
    <div v-if="results.type === 'person_companies'" class="card">
      <div class="card-header">
        <i class="fas fa-briefcase"></i>
        <h3>Empresas Associadas ({{ results.data.length }})</h3>
      </div>
      <div class="card-content">
        <div v-if="results.data.length === 0" class="no-results">
          <i class="fas fa-info-circle"></i>
          Nenhuma empresa encontrada para esta pessoa.
        </div>
        <div v-else class="companies-grid grid-base">
          <div
            v-for="(company, index) in results.data"
            :key="index"
            class="company-card card-item-base"
          >
            <div class="company-card-header">
              <div class="company-name">
                <i class="fas fa-building"></i>
                {{ company.razao_social }}
              </div>
              <div class="company-cnpj">
                {{ formatCNPJ(company.cnpj) }}
              </div>
            </div>
            <div class="company-card-details item-details">
              <div v-if="company.nome_fantasia">
                <strong>Nome Fantasia:</strong> {{ company.nome_fantasia }}
              </div>
              <div v-if="company.qualificacao_socio">
                <strong>Qualificação:</strong> {{ company.qualificacao_socio }}
              </div>
              <div v-if="company.situacao_cadastral">
                <strong>Situação:</strong> {{ company.situacao_cadastral }}
              </div>
              <div v-if="company.data_entrada_sociedade">
                <strong>Entrada na Sociedade:</strong> {{ formatDate(company.data_entrada_sociedade) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empresa não encontrada -->
    <div v-if="results.type === 'company_not_found'" class="card">
      <div class="card-header">
        <i class="fas fa-search"></i>
        <h3>Resultado da Busca</h3>
      </div>
      <div class="card-content">
        <div class="not-found">
          <i class="fas fa-exclamation-circle"></i>
          <h4>Empresa não encontrada</h4>
          <p>Nenhuma empresa foi encontrada com o CNPJ informado.</p>
          <p>Verifique se o CNPJ está correto ou tente novamente.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { CPFValidator, CNPJValidator, FormatUtils } from '../utils/validators';

export default {
  name: 'SearchResults',
  props: {
    results: {
      type: Object,
      required: true
    },
    selectedPerson: {
      type: Object,
      default: null
    }
  },
  methods: {
    selectPerson(cpf) {
      this.$emit('person-selected', cpf);
    },
    formatCPF(cpf) {
      return CPFValidator.format(cpf);
    },
    formatCNPJ(cnpj) {
      return CNPJValidator.format(cnpj);
    },
    formatCurrency(value) {
      return FormatUtils.formatCurrency(value);
    },
    formatDate(date) {
      return FormatUtils.formatDate(date);
    },
    hasAddress(company) {
      return company && (
        company.logradouro ||
        company.numero ||
        company.bairro ||
        company.municipio ||
        company.uf ||
        company.cep
      );
    },
    getFullAddress(company) {
      if (!company) return '';

      const addressParts = [];

      if (company.logradouro) {
        let street = company.logradouro;
        if (company.numero) {
          street += `, ${company.numero}`;
        }
        if (company.complemento) {
          street += `, ${company.complemento}`;
        }
        addressParts.push(street);
      }

      if (company.bairro) {
        addressParts.push(company.bairro);
      }

      if (company.municipio && company.uf) {
        addressParts.push(`${company.municipio} - ${company.uf}`);
      } else if (company.municipio) {
        addressParts.push(company.municipio);
      } else if (company.uf) {
        addressParts.push(company.uf);
      }

      if (company.cep) {
        addressParts.push(`CEP: ${company.cep}`);
      }

      return addressParts.join(' • ');
    }
  }
};
</script>