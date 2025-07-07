// Validador de CPF
export class CPFValidator {
    static CPF_LENGTH = 11;
    static BASE_LENGTH = 9;
    static REGEX_NON_DIGITS = /[^\d]/g;
    static REGEX_ALL_REPEATING = /^(\d)\1{10}$/;
    static WEIGHTS_DV1 = [10, 9, 8, 7, 6, 5, 4, 3, 2];
    static WEIGHTS_DV2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2];

    static isValid(cpf) {
        if (!cpf || typeof cpf !== 'string') return false;
        const cleanedCpf = this._clean(cpf);

        if (cleanedCpf.length !== this.CPF_LENGTH) return false;
        if (this.REGEX_ALL_REPEATING.test(cleanedCpf)) return false;

        const base = cleanedCpf.substring(0, this.BASE_LENGTH);
        const providedDvs = cleanedCpf.substring(this.BASE_LENGTH, this.CPF_LENGTH);
        const calculatedDvs = this._calculateCheckDigits(base);

        return providedDvs === calculatedDvs;
    }

    static _clean(cpf) {
        return cpf.replace(this.REGEX_NON_DIGITS, "");
    }

    static _calculateCheckDigits(base) {
        const baseNumbers = base.split('').map(Number);
        const dv1 = this._calculateDigit(baseNumbers, this.WEIGHTS_DV1);
        const dv2 = this._calculateDigit([...baseNumbers, dv1], this.WEIGHTS_DV2);
        return `${dv1}${dv2}`;
    }

    static _calculateDigit(numbers, weights) {
        const sum = numbers.reduce((acc, number, index) => {
            return acc + (number * weights[index]);
        }, 0);
        const rest = sum % 11;
        return rest < 2 ? 0 : 11 - rest;
    }

    static format(cpf) {
        const cleaned = this._clean(cpf);
        if (cleaned.length !== this.CPF_LENGTH) return cpf;
        return cleaned.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
}

// Validador de CNPJ
export class CNPJValidator {
    static tamanhoCNPJSemDV = 12;
    static regexCNPJSemDV = /^([A-Z\d]){12}$/;
    static regexCNPJ = /^([A-Z\d]){12}(\d){2}$/;
    static regexCaracteresMascara = /[./-]/g;
    static regexCaracteresNaoPermitidos = /[^A-Z\d./-]/i;
    static valorBase = "0".charCodeAt(0);
    static pesosDV = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    static cnpjZerado = "00000000000000";

    static isValid(cnpj) {
        if (!this.regexCaracteresNaoPermitidos.test(cnpj)) {
            let cnpjSemMascara = this.removeMascaraCNPJ(cnpj);
            if (this.regexCNPJ.test(cnpjSemMascara) && cnpjSemMascara !== this.cnpjZerado) {
                const dvInformado = cnpjSemMascara.substring(this.tamanhoCNPJSemDV);
                const dvCalculado = this.calculaDV(cnpjSemMascara.substring(0, this.tamanhoCNPJSemDV));
                return dvInformado === dvCalculado;
            }
        }
        return false;
    }

    static calculaDV(cnpj) {
        if (!this.regexCaracteresNaoPermitidos.test(cnpj)) {
            let cnpjSemMascara = this.removeMascaraCNPJ(cnpj);
            if (this.regexCNPJSemDV.test(cnpjSemMascara) && cnpjSemMascara !== this.cnpjZerado.substring(0, this.tamanhoCNPJSemDV)) {
                let somatorioDV1 = 0;
                let somatorioDV2 = 0;
                for (let i = 0; i < this.tamanhoCNPJSemDV; i++) {
                    const asciiDigito = cnpjSemMascara.charCodeAt(i) - this.valorBase;
                    somatorioDV1 += asciiDigito * this.pesosDV[i + 1];
                    somatorioDV2 += asciiDigito * this.pesosDV[i];
                }
                const dv1 = somatorioDV1 % 11 < 2 ? 0 : 11 - (somatorioDV1 % 11);
                somatorioDV2 += dv1 * this.pesosDV[this.tamanhoCNPJSemDV];
                const dv2 = somatorioDV2 % 11 < 2 ? 0 : 11 - (somatorioDV2 % 11);
                return `${dv1}${dv2}`;
            }
        }
        throw new Error("Não é possível calcular o DV pois o CNPJ fornecido é inválido");
    }

    static removeMascaraCNPJ(cnpj) {
        return cnpj.replace(this.regexCaracteresMascara, '').toUpperCase();
    }

    static format(cnpj) {
        const cleaned = this.removeMascaraCNPJ(cnpj);
        if (cleaned.length !== 14) return cnpj;
        return cleaned.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
}

// Utilitários de formatação
export class FormatUtils {
    static formatCurrency(value) {
        if (!value) return 'N/A';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    static formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            let date;

            // Formato YYYYMMDD (sem separadores) - ex: "20230522"
            if (/^\d{8}$/.test(dateString)) {
                const year = dateString.substring(0, 4);
                const month = dateString.substring(4, 6);
                const day = dateString.substring(6, 8);
                date = new Date(year, month - 1, day);
            }
            // Formato ISO (YYYY-MM-DD) - ex: "1990-03-16"
            else if (/^\d{4}-\d{2}-\d{2}/.test(dateString)) {
                date = new Date(dateString);
            }
            // Formato DD/MM/YYYY
            else if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateString)) {
                const [day, month, year] = dateString.split('/');
                date = new Date(year, month - 1, day);
            }
            // Outros formatos
            else {
                date = new Date(dateString);
            }

            // Verifica se a data é válida
            if (isNaN(date.getTime())) {
                return dateString;
            }

            return date.toLocaleDateString('pt-BR');
        } catch (error) {
            return dateString;
        }
    }

    static truncateText(text, maxLength = 50) {
        if (!text) return 'N/A';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
}