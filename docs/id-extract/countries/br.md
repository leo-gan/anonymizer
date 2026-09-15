# Brazil (`BR`)

National-ID patterns loaded when you pass `countries=["BR"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `CPF_BR` — CPF (Cadastro de Pessoas Físicas)

The federal tax identifier for a natural person in Brazil. Receita Federal issues it.

| | |
|---|---|
| **Package type** | `CPF_BR` |
| **Shape this package looks for** | 11 digits, often 000.000.000-00 |
| **Checksum** | two mod-11 check digits |
| **Example (synthetic)** | `529.982.247-25` |

**Official sources**

- [Receita Federal — CPF](https://www.gov.br/receitafederal/pt-br/assuntos/meu-cpf)

## `CNPJ_BR` — CNPJ (Cadastro Nacional da Pessoa Jurídica)

The federal tax identifier for a legal person.

| | |
|---|---|
| **Package type** | `CNPJ_BR` |
| **Shape this package looks for** | 14 digits, often 00.000.000/0001-00 |
| **Checksum** | none in this package |
| **Example (synthetic)** | `11.222.333/0001-81` |

**Official sources**

- [Receita Federal — CNPJ](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj)

## `RG_BR` — RG (Registro Geral)

A state civil-identity number. Formats vary by state. This pattern is structural.

| | |
|---|---|
| **Package type** | `RG_BR` |
| **Shape this package looks for** | 8 digits plus a check character, optional dots |
| **Checksum** | none |
| **Example (synthetic)** | `12.345.678-9` |

**Official sources**

- [Gov.br — documentos de identificação](https://www.gov.br/pt-br/servicos/obter-a-carteira-de-identidade)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
