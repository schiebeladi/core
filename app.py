import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import tempfile
import os
from datetime import date, datetime

# --- CONFIGURAÇÃO DA API (SEGURA) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Usando o modelo 1.5-flash que é mais estável e rápido
    model = genai.GenerativeModel('gemini-3-flash-preview')
except Exception as e:
    st.error("Erro na chave da API. Verifique o arquivo secrets.toml.")

# --- CONFIGURAÇÕES FIXAS ---
CAMINHO_LOGO = "logo.png" 
ARQUIVO_HISTORICO = "historico_analises.txt"
ENDERECO_FIXO = "Atendimento On-line"
INSTA_FIXO = "@schiebeladriana"
ZAP_FIXO = "41 99687-9500"
NOME_TERAPEUTA_FIXO = "Adriana Alarcon Schiebel"

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(nome_paciente):
    data_hoje = date.today().strftime("%Y-%m-%d")
    linha = f"{data_hoje}|{nome_paciente}\n"
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(linha)

def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return []
    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        return [linha.strip().split("|") for linha in f.readlines()]

def contar_analises_mes():
    historico = carregar_historico()
    mes_atual = date.today().strftime("%Y-%m")
    total = sum(1 for item in historico if item[0].startswith(mes_atual))
    return total

def limpar_dados():
    st.session_state["nome_paciente"] = ""
    st.session_state["queixa"] = ""
    st.session_state["nascimento"] = date.today()
    st.session_state["sexo"] = "Feminino"
    st.session_state["file_key"] = st.session_state.get("file_key", 0) + 1
    if "analise_atual" in st.session_state:
        del st.session_state["analise_atual"]

# --- CLASSE DO PDF ---
class RelatorioPDF(FPDF):
    def __init__(self, info_rodape=None):
        super().__init__()
        self.info_rodape = info_rodape

    def header(self):
        if os.path.exists(CAMINHO_LOGO):
            self.image(CAMINHO_LOGO, x=85, y=10, w=40)
            self.ln(35)
        else:
            self.ln(10)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Analise Integrativa por Biorressonancia Quantica", ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", "I", 8)
        contato = f"{self.info_rodape['endereco']} | Instagram: {self.info_rodape['insta']} | Tel: {self.info_rodape['tel']}"
        self.cell(0, 5, contato.encode('latin-1', 'replace').decode('latin-1'), align='C', ln=True)
        self.cell(0, 10, f"Pagina {self.page_no()}", align='C')

def gerar_pdf(texto_analise, dados_usuario, nome_terapeuta, info_rodape):
    pdf = RelatorioPDF(info_rodape)
    pdf.add_page()
    data_formatada = dados_usuario['nascimento'].strftime('%d/%m/%Y')
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"Paciente: {dados_usuario['nome']}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Data de Nascimento: {data_formatada} ({dados_usuario['idade']} anos)", ln=True)
    pdf.cell(0, 6, f"Sexo: {dados_usuario['sexo']}", ln=True)
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Arial", "", 11)
    # Limpeza básica de Markdown para o PDF
    texto_limpo = texto_analise.replace("**", "").replace("#", "").replace("•", "-")
    pdf.multi_cell(0, 7, txt=texto_limpo.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf.ln(15)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, txt=nome_terapeuta, ln=True, align='R')
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 8, txt="Consultora DoTerra", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Gestão de Análises", layout="wide")

if "file_key" not in st.session_state:
    st.session_state["file_key"] = 0

# BARRA LATERAL
with st.sidebar:
    st.title("📊 Painel de Controle")
    st.metric("Análises este Mês", contar_analises_mes())
    
    st.divider()
    st.subheader("🔍 Histórico Recente")
    hist = carregar_historico()
    if hist:
        for data_item, nome_item in reversed(hist[-10:]): # Mostra as últimas 10
            try:
                data_format = datetime.strptime(data_item, "%Y-%m-%d").strftime("%d/%m/%y")
                st.text(f"📅 {data_format} - {nome_item}")
            except: continue
    else:
        st.info("Nenhuma análise registrada.")

    st.divider()
    st.title("⚙️ Dados Fixos")
    nome_terapeuta = st.text_input("Terapeuta", NOME_TERAPEUTA_FIXO)
    endereco = st.text_input("Endereço", ENDERECO_FIXO)
    insta = st.text_input("Instagram", INSTA_FIXO)
    tel = st.text_input("WhatsApp", ZAP_FIXO)

# ÁREA PRINCIPAL
st.title("🌿 Portal Consultora Adriana Alarcon Schiebel")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Dados do Cliente")
    nome_paciente = st.text_input("Nome do Cliente", key="nome_paciente")
    hoje = date.today()
    nascimento = st.date_input("Data de Nascimento", min_value=date(1900, 1, 1), max_value=hoje, format="DD/MM/YYYY", key="nascimento")
    sexo = st.selectbox("Sexo", ["Feminino", "Masculino", "Outro"], key="sexo")

with col2:
    st.subheader("📄 Relatório da Análise CoRe")
    upload_pdf = st.file_uploader("Arquivo Inergetix CoRe em pdf", type=['pdf'], key=f"pdf_{st.session_state['file_key']}")
    queixa = st.text_area("Queixa Principal", key="queixa")

st.divider()

c1, c2 = st.columns([1, 4])
with c1:
    st.button("🗑️ Limpar Campos", on_click=limpar_dados)
with c2:
    gerar = st.button("🪄 Gerar Relatório e Salvar no Histórico")

if gerar:
    if not upload_pdf or not nome_paciente:
        st.warning("Por favor, preencha o nome do paciente e anexe o arquivo PDF.")
    else:
        # CÁLCULO DA IDADE (CORREÇÃO DO ERRO)
        idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))

        with st.spinner("Analisando e Gerando o resultado..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(upload_pdf.getvalue())
                    path_pdf_tmp = tmp.name

                arquivo_gemini = genai.upload_file(path_pdf_tmp)
                
                prompt_final = f"""

                Você é uma Consultora doTERRA, com vasta experiência prática em:

                    - Saúde física, emocional, energética e espiritual
                    - Saúde preventiva
                    - Aromaterapia clínica
                    - Nutrição funcional e suplementação
                    - Biorressonância Quântica
                    - Especialista no Sistema Inergetix Core

                    Sua missão é elaborar um relatório integrativo personalizado com base na análise do PDF gerado pelo Inergetix Core para:

                    Paciente: {nome_paciente}  
                    Idade: {idade}  
                    Sexo: {sexo}  
                    Queixa principal: {queixa}

                    ⚠ IMPORTANTE:
                    - A análise NÃO é diagnóstico médico.
                    - Trabalhe com interpretação integrativa, emocional e energética.
                    - Utilize linguagem acolhedora, humanizada e profissional.
                    - Escreva como consultora experiente, com segurança técnica e sensibilidade.

                    -------------------------------------------------------

                    ESTRUTURA OBRIGATÓRIA DO RELATÓRIO:

                    # RELATÓRIO INTEGRATIVO PERSONALIZADO

                    ## 1) Análise Integrativa Simplificada
                    - Analise exclusivamente os óleos e frequências apresentados no PDF.
                    - Explique as possíveis interações energéticas.
                    - Relacione com a idade, sexo e queixa principal do paciente.
                    - Linguagem clara e acessível, sem termos excessivamente técnicos.

                    ## 2) Sua Rotina Diária
                    Elabore uma rotina prática personalizada com:
                    - Uso de óleos por ingestão (quando apropriado)
                    - Inalação
                    - Difusão ambiental
                    - Aplicação tópica

                    Organize em:
                    - Manhã
                    - Tarde
                    - Noite

                    Inclua para cada momento:
                    - Como usar
                    - Quantidade
                    - Forma de uso
                    - Objetivo terapêutico
                    - Uma afirmação positiva personalizada para aquele óleo e aquele momento.

                    ## 3) Seu Guia de Automassagem
                    Crie uma rotina simples e prática de automassagem terapêutica utilizando os óleos indicados.
                    Explique:
                    - Região de aplicação
                    - Movimentos
                    - Frequência
                    - Objetivo energético e emocional

                    ## 4) Rotina de Suplementação doTERRA(Se houver indicação)
                    Caso faça sentido na análise:
                    - Nome do suplemento
                    - Horário
                    - Quantidade sugerida (de forma orientativa)
                    - Objetivo funcional

                    Nunca prescrever como tratamento médico.

                    ## 5) Suas Recomendações Integrativas
                    Inclua recomendações complementares como:
                    - Hábitos diários
                    - Respiração
                    - Exposição solar
                    - Movimento corporal
                    - Alimentação funcional
                    - Práticas energéticas
                    - Sono

                    ## 6) Minhas Considerações Finais
                    Texto acolhedor e explicativo reforçando:
                    - A interpretação energética
                    - O papel ativo do paciente no processo
                    - O convite ao autocuidado consciente

                    ## 7) Tempo de Uso e Reavaliação
                        ### Ciclo de 90 dias
                        Explique que este protocolo de óleos, suplementos e práticas deve ser seguido por no máximo 90 dias.
                        
                    ## 8) Gotas de Sabedoria
                    Uma dica especial e inédita de aromaterapia para o dia.

                    ## 9) Nota sobre Biorressonância e Autocura
                    Explique de forma simples:
                    - O que é biorressonância quântica (análise de tendências energéticas)
                    - Que não substitui diagnóstico médico
                    - Como os óleos essenciais atuam harmonizando emoções, energia e frequência corporal
                    - Conceito de autocura como processo de equilíbrio interno

                    -------------------------------------------------------

                    FORMATAÇÃO:

                    - Use '##' para seções principais, '###' para subtópicos, e use negritos nos pontos chaves importantes
                    - Texto organizado, agradável e fácil de ler.
                    - Parágrafos bem distribuídos.
                    - Tom profissional e empático.
                    - Referencie o texto na voz do(a) consultora.

                    Finalize com:
                    Uma mensagem curta de motivação, otimismo e incentivo personalizada para o paciente.
          

                """
                
                response = model.generate_content([prompt_final, arquivo_gemini])
                st.session_state["analise_atual"] = response.text
                
                salvar_no_historico(nome_paciente)
                
                info_rodape = {"endereco": endereco, "insta": insta, "tel": tel}
                st.session_state["pdf_bytes"] = gerar_pdf(
                    response.text, 
                    {"nome": nome_paciente, "nascimento": nascimento, "sexo": sexo, "idade": idade}, 
                    nome_terapeuta, 
                    info_rodape
                )
                
                os.remove(path_pdf_tmp)
                st.success("Relatório gerado com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Ocorreu um erro durante o processamento: {e}")

# EXIBIÇÃO DO RESULTADO
if "analise_atual" in st.session_state:
    st.divider()
    st.subheader("📄 Visualização do Relatório")
    st.markdown(st.session_state["analise_atual"])
    
    st.download_button(
        label="📥 Baixar Relatório em PDF",
        data=st.session_state["pdf_bytes"],
        file_name=f"Relatorio_{nome_paciente.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
